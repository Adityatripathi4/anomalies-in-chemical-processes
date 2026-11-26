# Every annotated anomaly: what was done, where, and which sensors reacted.

import pandas as pd
import streamlit as st

import plant
from anomaly_annotations import OPS, SENSOR_LABELS
from data import ANOMALOUS_RUN, data_missing, load_events, load_run, run_path

if data_missing():
    st.error("Could not find the folder batch_distillation_dataset next to app.py.")
    st.stop()

if st.button("Back to overview"):
    st.switch_page("views/overview.py")

st.title("Annotated anomalies")

op = st.selectbox("Operating point", OPS, key="op")

run = load_run(run_path(op, ANOMALOUS_RUN))
events = load_events(op)
confirmed = events[events["confirmed"]]
unconfirmed = events[~events["confirmed"]]

n_events = confirmed["event_id"].nunique()
minutes = round((run["offset"].iloc[-1] - run["offset"].iloc[0]).total_seconds() / 60)
st.write("The run lasts " + str(minutes) + " minutes and has " + str(n_events)
         + (" confirmed anomaly" if n_events == 1 else " confirmed anomalies")
         + " in " + str(len(confirmed))
         + (" interval." if len(confirmed) == 1 else " intervals."))


# one block per anomaly

for event_id, group in confirmed.groupby("event_id"):
    first = group.iloc[0]
    minutes = round(sum(group["duration_s"]) / 60, 1)

    with st.container(border=True):
        head, facts = st.columns([2, 1])

        with head:
            st.markdown("**" + event_id + "** - " + first["category"])
            st.write(first["perturbation"] or "No description given.")
            if first["source_labels"]:
                st.caption("Applied at: " + first["source_labels"]
                           + " (" + first["source_ids"] + ")")
            if first["effects"]:
                st.caption("Observed: " + first["effects"])

        with facts:
            st.write("Intervals: " + str(len(group)))
            st.write("Total: " + str(minutes) + " min")
            st.write("First at " + str(first["start"]).split()[-1])
            if first["sensors"]:
                st.write("Sensors: " + first["sensors"])
            units = plant.disturbance_units(
                [s.strip() for s in first["source_ids"].split(",") if s.strip()])
            if units:
                st.write("Plant part: " + ", ".join(units))
            if st.button("Sensor responses", key="go_" + event_id, width="stretch"):
                # the responses page picks these up before it builds its widgets
                st.session_state["jump_op"] = op
                st.session_state["jump_event"] = event_id
                st.switch_page("views/responses.py")

if len(unconfirmed):
    with st.container(border=True):
        st.markdown("**Unconfirmed observations**")
        st.write("This operating point also has "
                 + str(unconfirmed["event_id"].nunique())
                 + " entries marked `Anomaly` instead of `ConfirmedAnomaly`. They "
                 "carry timings but no description, no category and no sensor "
                 "information, so they are left out of the charts.")
        st.write(", ".join(sorted(unconfirmed["event_id"].unique())))
