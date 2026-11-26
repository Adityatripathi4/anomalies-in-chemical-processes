# One sensor over a run, with the anomalies shaded, and the normal run next to it.

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from anomaly_annotations import OPS, SENSORS, SENSOR_LABELS
from data import ANOMALOUS_RUN, DAY, NORMAL_RUN, data_missing, load_events, load_run, run_path
from palette import ANOMALY, CHART_HEIGHT, NORMAL, SIGNAL

CONTEXT_MINUTES = 5

if data_missing():
    st.error("Could not find the folder batch_distillation_dataset next to app.py.")
    st.stop()

if "jump_sensor" in st.session_state:
    st.session_state["sensor"] = st.session_state.pop("jump_sensor")

if st.button("Back to overview"):
    st.switch_page("views/overview.py")

st.title("Time series")

pick_op, pick_sensor = st.columns(2)
op = pick_op.selectbox("Operating point", OPS, key="op")
sensor = pick_sensor.selectbox("Sensor", SENSORS, key="sensor",
                               format_func=lambda s: s + " - " + SENSOR_LABELS[s])

normal = load_run(run_path(op, NORMAL_RUN))
anomalous = load_run(run_path(op, ANOMALOUS_RUN))
events = load_events(op)
events = events[events["confirmed"]]

sd = normal[sensor].std()

inside = pd.Series(False, index=anomalous.index)
for _, event in events.iterrows():
    inside = inside | anomalous["offset"].between(event["start"], event["end"])

top = st.columns(3)
top[0].metric("Anomalies", events["event_id"].nunique())
top[1].metric("Time intervals", len(events))
top[2].metric("Share of run", str(round(100 * inside.mean())) + " %")


# chart 1

st.subheader("Before, during and after the anomalies")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=anomalous["clock"], y=anomalous[sensor],
                          mode="lines", line=dict(color=SIGNAL, width=1)))
for _, event in events.iterrows():
    fig1.add_vrect(x0=DAY + event["start"], x1=DAY + event["end"],
                   fillcolor=ANOMALY, opacity=0.22, line_width=0, layer="below")

fig1.update_layout(height=CHART_HEIGHT, xaxis_title="Time", yaxis_title=sensor,
                   showlegend=False, hovermode="x unified",
                   margin=dict(l=10, r=10, t=20, b=10))
fig1.update_xaxes(tickformat="%H:%M")
st.plotly_chart(fig1, width="stretch")
st.caption("The shaded parts are the annotated anomalies.")


# chart 2

st.subheader("Compared with the normal run")

fig2 = go.Figure()
for name, run, color in [("normal", normal, NORMAL), ("anomalous", anomalous, SIGNAL)]:
    minutes = (run["offset"] - run["offset"].iloc[0]).dt.total_seconds() / 60
    fig2.add_trace(go.Scatter(x=minutes, y=run[sensor], mode="lines",
                              name=name, line=dict(color=color, width=1)))

fig2.update_layout(height=CHART_HEIGHT, xaxis_title="Minutes since start of run",
                   yaxis_title=sensor, hovermode="x unified",
                   margin=dict(l=10, r=10, t=20, b=10))
st.plotly_chart(fig2, width="stretch")
st.caption("Both runs start at zero. If the two lines stay apart the whole time, "
           "the difference is not only caused by the anomalies.")


# table

with st.expander("What " + sensor + " does during each anomaly"):
    if len(events) == 0:
        st.write("There are no confirmed anomalies at this operating point.")
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
                "Change": ("up " if change > 0 else "down ") + str(round(abs(change), 3))
                          + "  (" + str(round(change / sd, 1)) + " sd)",
                "Back to before": back,
            })

        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption("Before and after use the " + str(CONTEXT_MINUTES) + " minutes on "
                   "each side of the anomaly. sd is the standard deviation of "
                   + sensor + " in the normal run (" + str(round(sd, 3)) + ").")
