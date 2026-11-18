# Dashboard for the batch distillation data.
# Question 1: how do sensor readings change when an anomaly occurs?
# Run with: streamlit run app.py

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from annotations import SENSORS, SENSOR_LABELS, load_annotations

DATA_DIR = "batch_distillation_dataset"
CONTEXT_MINUTES = 5

st.set_page_config(page_title="Anomalies in Batch Distillation", layout="wide")


@st.cache_data
def load_run(path):
    df = pd.read_csv(path)
    df["offset"] = pd.to_timedelta(df["Time"])
    # plotly draws a nicer time axis with real timestamps, so add a dummy date
    df["clock"] = pd.Timestamp("2000-01-01") + df["offset"]
    return df


if not os.path.isdir(DATA_DIR):
    st.error("Could not find the folder " + DATA_DIR + " next to app.py.")
    st.stop()

st.title("Anomalies in Batch Distillation")
st.write("Question 1 - how do sensor readings change when an anomaly occurs?")

ops = sorted(os.listdir(DATA_DIR))
ops = [op for op in ops if op.startswith("OP")]

op = st.sidebar.selectbox("Operating point", ops)
sensor = st.sidebar.selectbox("Sensor", SENSORS,
                              format_func=lambda s: s + " - " + SENSOR_LABELS[s])

normal = load_run(DATA_DIR + "/" + op + "/measurements/train_normal_experiment_001.csv")
anomalous = load_run(DATA_DIR + "/" + op + "/measurements/test_anormal_experiment_001.csv")

events = load_annotations(DATA_DIR + "/" + op + "/annotations/test_anormal_experiment_001.yaml",
                          op, anomalous["offset"].iloc[0], anomalous["offset"].iloc[-1])
events = events[events["no_category"] == False]

sd = normal[sensor].std()

# how much of the run is inside an annotated anomaly
inside = pd.Series(False, index=anomalous.index)
for _, event in events.iterrows():
    inside = inside | anomalous["offset"].between(event["start"], event["end"])

col1, col2, col3 = st.columns(3)
col1.metric("Anomalies", events["event_id"].nunique())
col2.metric("Time intervals", len(events))
col3.metric("Share of run", str(round(100 * inside.mean())) + " %")


# first chart - the anomalous run with the anomalies shaded

st.subheader("Before, during and after the anomalies")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=anomalous["clock"], y=anomalous[sensor],
                          mode="lines", line=dict(color="orange", width=1)))
for _, event in events.iterrows():
    fig1.add_vrect(x0=pd.Timestamp("2000-01-01") + event["start"],
                   x1=pd.Timestamp("2000-01-01") + event["end"],
                   fillcolor="orange", opacity=0.2, line_width=0, layer="below")

fig1.update_layout(height=400, xaxis_title="Time", yaxis_title=sensor,
                   showlegend=False, hovermode="x unified")
fig1.update_xaxes(tickformat="%H:%M")
st.plotly_chart(fig1, width="stretch")
st.write("The shaded parts are the annotated anomalies.")


# second chart - the same sensor in the normal run and the anomalous run

st.subheader("Compared with the normal run")

fig2 = go.Figure()
for name, run, color in [("normal", normal, "blue"), ("anomalous", anomalous, "orange")]:
    minutes = (run["offset"] - run["offset"].iloc[0]).dt.total_seconds() / 60
    fig2.add_trace(go.Scatter(x=minutes, y=run[sensor], mode="lines",
                              name=name, line=dict(color=color, width=1)))

fig2.update_layout(height=400, xaxis_title="Minutes since start of run",
                   yaxis_title=sensor, hovermode="x unified")
st.plotly_chart(fig2, width="stretch")
st.write("Both runs start at zero. If the two lines stay apart the whole time, "
         "the difference is not only caused by the anomalies.")


# table - what the sensor does around each anomaly

st.subheader("What " + sensor + " does during each anomaly")

if len(events) == 0:
    st.write("There are no annotated anomalies at this operating point.")
else:
    context = pd.Timedelta(str(CONTEXT_MINUTES) + "min")
    rows = []

    for event_id, group in events.groupby("event_id"):
        start = group["start"].min()
        end = group["end"].max()

        before = anomalous.loc[anomalous["offset"].between(start - context, start), sensor].mean()
        during = anomalous.loc[anomalous["offset"].between(start, end), sensor].mean()
        after = anomalous.loc[anomalous["offset"].between(end, end + context), sensor].mean()

        change = during - before
        if pd.isna(after):
            back = "-"
        elif abs(after - before) <= sd:
            back = "yes"
        else:
            back = "no"

        rows.append({
            "Anomaly": event_id,
            "Type": group["category"].iloc[0],
            "Start": str(start).split()[-1],
            "Minutes": round((end - start).total_seconds() / 60, 1),
            "Before": round(before, 3),
            "During": round(during, 3),
            "After": round(after, 3),
            "Change": ("up " if change > 0 else "down ") + str(round(abs(change), 3)),
            "Change in sd": round(change / sd, 1),
            "Back to before": back,
            "Sensors in annotation": group["sensors"].iloc[0],
        })

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.write("Before and after use the " + str(CONTEXT_MINUTES) +
             " minutes on each side of the anomaly. sd is the standard deviation of " +
             sensor + " in the normal run (" + str(round(sd, 3)) + ").")
