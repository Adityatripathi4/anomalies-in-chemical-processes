# Dashboard for the batch distillation data.
# Run with: streamlit run app.py

import streamlit as st

st.set_page_config(page_title="Catching Anomalies in a Distillation Column",
                   page_icon=":material/science:", layout="wide")

st.html("""
<style>
[data-testid="stMainBlockContainer"] {
    padding-top: 2rem !important;
}
</style>
""")

pages = [
    st.Page("views/overview.py", title="Overview", url_path="overview", default=True),
    st.Page("views/timeseries.py", title="Time series", url_path="time-series"),
    st.Page("views/anomalies.py", title="Anomalies", url_path="anomalies"),
    st.Page("views/responses.py", title="Sensor responses", url_path="sensor-responses"),
]

st.navigation(pages, position="hidden").run()
