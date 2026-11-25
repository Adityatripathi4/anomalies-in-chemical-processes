# All 11 sensors around one anomaly, then one sensor in detail.

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from annotations import OPS, SENSORS, SENSOR_LABELS
from data import (ANOMALOUS_RUN, DAY, NORMAL_RUN, data_missing, load_events,
                  load_run, run_path)

HIGHLIGHT = "#f08030"
PLAIN = "#5b8ff9"
SHADE = "#f08030"

if data_missing():
    st.error("Could not find the folder batch_distillation_dataset next to app.py.")
    st.stop()

# if we arrived from the anomalies page, start on the anomaly that was clicked
if "jump_op" in st.session_state:
    st.session_state["op"] = st.session_state.pop("jump_op")
if "jump_event" in st.session_state:
    st.session_state["event_id"] = st.session_state.pop("jump_event")

if st.button("Back to overview"):
    st.switch_page("views/overview.py")

st.title("Sensor responses")
st.write("All 11 sensors around one anomaly. The sensors named in the annotation "
         "are drawn in orange, the rest in blue. Pick one for a closer look.")

pick_op, pick_event = st.columns(2)
op = pick_op.selectbox("Operating point", OPS, key="op")

events = load_events(op)
events = events[events["confirmed"]]

if len(events) == 0:
    st.info("This operating point has no confirmed anomalies.")
    st.stop()

# one entry per anomaly, not per interval
spans = events.groupby("event_id").agg(
    start=("start", "min"), end=("end", "max"), category=("category", "first"),
    sensors=("sensors", "first"), perturbation=("perturbation", "first"),
    source_labels=("source_labels", "first"), effects=("effects", "first"),
    intervals=("interval", "size")).reset_index()

if st.session_state.get("event_id") not in list(spans["event_id"]):
    st.session_state.pop("event_id", None)

event_id = pick_event.selectbox(
    "Anomaly", spans["event_id"], key="event_id",
    format_func=lambda e: e + "  (" + spans.loc[spans["event_id"] == e, "category"].iloc[0] + ")")

event = spans[spans["event_id"] == event_id].iloc[0]
named = [s.strip() for s in event["sensors"].split(",") if s.strip()]
# some annotations name sensors outside the 11 used in this project
named_here = [s for s in named if s in SENSORS]
named_elsewhere = [s for s in named if s not in SENSORS]

context = st.slider("Context (seconds)", min_value=60, max_value=1800, value=300, step=60,
                    help="How much time to show on each side of the anomaly.")

anomalous = load_run(run_path(op, ANOMALOUS_RUN))
normal = load_run(run_path(op, NORMAL_RUN))

pad = pd.Timedelta(seconds=context)
window_start = event["start"] - pad
window_end = event["end"] + pad
window = anomalous[anomalous["offset"].between(window_start, window_end)]

facts = st.columns(4)
facts[0].metric("Category", event["category"])
facts[1].metric("Intervals", int(event["intervals"]))
facts[2].metric("Length", str(round((event["end"] - event["start"]).total_seconds() / 60, 1)) + " min")
facts[3].metric("Named sensors", len(named_here))

if event["perturbation"]:
    st.caption(event["perturbation"])
if named_elsewhere:
    st.caption("The annotation also names " + ", ".join(named_elsewhere)
               + ", which are not among the 11 sensors used in this project.")


# all sensors at once

st.subheader("All sensors")

rows = make_subplots(rows=len(SENSORS), cols=1, shared_xaxes=True, vertical_spacing=0.006)

before = anomalous[anomalous["offset"].between(window_start, event["start"])]

for i, sensor in enumerate(SENSORS, start=1):
    # show each sensor as its distance from the level just before the anomaly,
    # so all 11 fit on the same scale
    base = before[sensor].mean()
    spread = before[sensor].std()
    if not spread or pd.isna(spread):
        spread = 1.0
    scaled = (window[sensor] - base) / spread

    rows.add_trace(go.Scatter(
        x=window["clock"], y=scaled, mode="lines",
        line=dict(color=HIGHLIGHT if sensor in named_here else PLAIN, width=1),
        name=sensor, showlegend=False,
        hovertemplate=sensor + ": %{y:.1f} sd<extra></extra>"), row=i, col=1)

    rows.update_yaxes(title_text=sensor, row=i, col=1, title_font=dict(size=10),
                      tickfont=dict(size=9))

# one shape per interval across the whole figure, not one per sensor row:
# the recurrent anomaly at OP18 has 64 intervals and 11 rows would be 704 shapes
shading = []
for _, part in events[events["event_id"] == event_id].iterrows():
    shading.append(dict(type="rect", xref="x", yref="paper",
                        x0=DAY + part["start"], x1=DAY + part["end"],
                        y0=0, y1=1, fillcolor=SHADE, opacity=0.18,
                        line_width=0, layer="below"))
rows.update_layout(shapes=shading)

rows.update_layout(height=110 * len(SENSORS), margin=dict(l=10, r=10, t=20, b=40),
                   hovermode="x unified")
rows.update_xaxes(tickformat="%H:%M:%S", row=len(SENSORS), col=1,
                  title_text="Recording time")
st.plotly_chart(rows, width="stretch")

st.caption("Each sensor is drawn as its distance from its own average in the "
           + str(context) + " seconds before the anomaly, measured in standard "
           "deviations of that same stretch. That is only so the 11 sensors fit on "
           "one scale. The detail view below shows the real values.")


# one sensor in detail

st.subheader("One sensor in detail")

default = named_here[0] if named_here else SENSORS[0]
sensor = st.selectbox("Inspect sensor", SENSORS, index=SENSORS.index(default),
                      format_func=lambda s: s + " - " + SENSOR_LABELS[s])
compare = st.checkbox("Compare with the normal run")

detail = go.Figure()
detail.add_trace(go.Scatter(x=window["clock"], y=window[sensor], mode="lines",
                            name="anomalous run",
                            line=dict(color=HIGHLIGHT if sensor in named_here else PLAIN, width=1.4)))

if compare:
    # line the two runs up on time since the start of their own run
    offset_start = window_start - anomalous["offset"].iloc[0]
    offset_end = window_end - anomalous["offset"].iloc[0]
    same = normal[(normal["offset"] - normal["offset"].iloc[0]).between(offset_start, offset_end)]
    if len(same):
        shifted = same["offset"] - same["offset"].iloc[0] + window_start
        detail.add_trace(go.Scatter(x=DAY + shifted, y=same[sensor], mode="lines",
                                    name="normal run",
                                    line=dict(color="#8899aa", width=1.2, dash="dot")))
    else:
        st.caption("The normal run at this operating point is too short to cover "
                   "the same stretch.")

for _, part in events[events["event_id"] == event_id].iterrows():
    detail.add_vrect(x0=DAY + part["start"], x1=DAY + part["end"],
                     fillcolor=SHADE, opacity=0.18, line_width=0, layer="below")

detail.add_vline(x=DAY + event["start"], line_width=1, line_dash="dot", line_color=SHADE)
detail.add_vline(x=DAY + event["end"], line_width=1, line_dash="dot", line_color=SHADE)

detail.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10),
                     xaxis_title="Recording time", yaxis_title=sensor,
                     hovermode="x unified",
                     legend=dict(orientation="h", y=1.12, x=0))
detail.update_xaxes(tickformat="%H:%M:%S")
st.plotly_chart(detail, width="stretch")

st.caption("Anomaly from " + str(event["start"]).split()[-1] + " to "
           + str(event["end"]).split()[-1]
           + (". This sensor is named in the annotation." if sensor in named_here
              else ". This sensor is not named in the annotation."))

with st.expander("Annotation details"):
    st.write("**Anomaly** " + event_id + " - " + event["category"])
    st.write(event["perturbation"] or "No description given.")
    if event["source_labels"]:
        st.write("**Applied at** " + event["source_labels"])
    if event["effects"]:
        st.write("**Observed** " + event["effects"])
    st.write("**Sensors named** " + (event["sensors"] or "none"))
