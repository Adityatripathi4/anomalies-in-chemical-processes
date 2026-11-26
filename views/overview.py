# Overview page. Everything starts here, the cards link to the other pages.

import streamlit as st
import streamlit.components.v1 as components

import plant
from anomaly_annotations import OPS, SENSOR_LABELS
from data import all_events, data_missing, dataset_summary

if data_missing():
    st.error("Could not find the folder batch_distillation_dataset next to app.py.")
    st.stop()

st.title("Catching Anomalies in a Distillation Column")
st.caption("How the sensors react to disturbances, and which ones an LSTM and a "
           "Transformer notice.")

summary = dataset_summary()
events = all_events()


# the numbers at the top

cards = st.columns(3)
cards[0].metric("Operating points", summary["ops"])
cards[0].caption(", ".join(OPS))
cards[1].metric("Runs", summary["runs"])
cards[1].caption(str(summary["normal_runs"]) + " normal, "
                 + str(summary["anomalous_runs"]) + " anomalous, all at 1 Hz")
cards[2].metric("Anomalies", str(summary["confirmed"]) + " + " + str(summary["unconfirmed"]))
cards[2].caption("confirmed + unconfirmed, in "
                 + str(summary["intervals"]) + " time intervals")


# the process

st.subheader("The process", icon=":material/account_tree:")
st.write("Pick a part of the plant to highlight it and see which sensors sit there. "
         "Turn on the disturbances to see where they were applied.")

left, right = st.columns([3, 1])
with left:
    choice = st.segmented_control(
        "Part of the plant",
        ["Whole plant"] + list(plant.UNITS.keys()),
        default="Whole plant",
        format_func=lambda u: u if u == "Whole plant" else plant.UNITS[u]["label"],
        label_visibility="collapsed",
    )
with right:
    show_sources = st.toggle("Show disturbances")

selected = None if choice in (None, "Whole plant") else choice

marked = []
if show_sources:
    sources = []
    for value in events[events["confirmed"]]["source_ids"]:
        sources += [s.strip() for s in value.split(",") if s.strip()]
    marked = plant.disturbance_units(sources)

diagram, detail = st.columns([2, 1])

with diagram:
    components.html(plant.page(selected, marked), height=plant.FRAME_HEIGHT + 10)

with detail:
    if selected:
        unit = plant.UNITS[selected]
        st.markdown("**" + unit["label"] + " - " + unit["name"] + "**")
        st.write(unit["note"])
        st.markdown("**Sensors here**")
        for sensor in unit["sensors"]:
            st.write(sensor + " - " + SENSOR_LABELS[sensor])

        touched = events[events["confirmed"]].copy()
        touched = touched[touched["source_ids"].apply(
            lambda value: selected in plant.disturbance_units(
                [s.strip() for s in value.split(",") if s.strip()]))]
        if len(touched):
            st.markdown("**Disturbances applied here**")
            for _, row in touched.drop_duplicates("event_id").iterrows():
                st.write(row["op"] + ": " + row["perturbation"][:90])
    else:
        st.markdown("**Batch distillation**")
        st.write("A mixture of butan-1-ol, propan-2-ol and water is separated by "
                 "heating it and cooling the vapour again.")
        st.write("1. The mixture is heated in the reboiler V001 and partly evaporates.")
        st.write("2. The vapour rises through the column sections C001 to C003 and "
                 "gets richer in the more volatile component.")
        st.write("3. The condensers HE001 and HE002 turn it back into liquid, which "
                 "collects in the buffer vessel V002.")
        st.write("4. Pump P701 sends part of it back to the column as reflux, pump "
                 "P702 takes the rest out as distillate.")
        st.write("5. The plant runs below atmospheric pressure, controlled at G001.")
        st.caption("The mixture is not refilled during a run, so its composition "
                   "changes over time and temperatures rise even when nothing is wrong.")

if show_sources and marked:
    st.caption("Red dots mark the parts of the plant where a disturbance was applied.")


# where to go next

st.subheader("Where to look next", icon=":material/explore:")

go_series, go_anomalies, go_responses = st.columns(3)

with go_series:
    with st.container(border=True):
        st.markdown("**Time series**")
        st.write("One sensor over a whole run, with the annotated anomalies shaded, "
                 "and the same sensor in the normal run for comparison.")
        if st.button("Open time series", icon=":material/show_chart:", width="stretch"):
            st.switch_page("views/timeseries.py")

with go_anomalies:
    with st.container(border=True):
        st.markdown("**Anomalies**")
        st.write("Every annotated anomaly: what was done, where in the plant, which "
                 "sensors reacted and how long it lasted.")
        if st.button("Open anomalies", icon=":material/warning:", width="stretch"):
            st.switch_page("views/anomalies.py")

with go_responses:
    with st.container(border=True):
        st.markdown("**Sensor responses**")
        st.write("All 11 sensors around one anomaly, with the sensors named in the "
                 "annotation highlighted, then one sensor in detail.")
        if st.button("Open sensor responses", icon=":material/sensors:", width="stretch"):
            st.switch_page("views/responses.py")

