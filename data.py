# Loading the measurement files and the annotations.

import os

import pandas as pd
import streamlit as st

from annotations import OPS, load_annotations

DATA_DIR = "batch_distillation_dataset"
DAY = pd.Timestamp("2000-01-01")

NORMAL_RUN = "train_normal_experiment_001.csv"
ANOMALOUS_RUN = "test_anormal_experiment_001.csv"


def run_path(op, filename):
    return DATA_DIR + "/" + op + "/measurements/" + filename


@st.cache_data
def load_run(path):
    df = pd.read_csv(path)
    df["offset"] = pd.to_timedelta(df["Time"])
    # dummy date so plotly draws a time axis
    df["clock"] = DAY + df["offset"]
    return df


@st.cache_data
def load_events(op):
    run = load_run(run_path(op, ANOMALOUS_RUN))
    return load_annotations(
        DATA_DIR + "/" + op + "/annotations/" + ANOMALOUS_RUN.replace(".csv", ".yaml"),
        op, run["offset"].iloc[0], run["offset"].iloc[-1])


@st.cache_data
def all_events():
    return pd.concat([load_events(op) for op in OPS], ignore_index=True)


@st.cache_data
def dataset_summary():
    """Counts for the cards at the top of the overview."""
    runs, steps, seconds = 0, 0, 0
    for op in OPS:
        folder = DATA_DIR + "/" + op + "/measurements"
        for name in os.listdir(folder):
            if not name.endswith(".csv"):
                continue
            run = load_run(folder + "/" + name)
            runs += 1
            steps += len(run)
            seconds += (run["offset"].iloc[-1] - run["offset"].iloc[0]).total_seconds()

    events = all_events()
    confirmed = events[events["confirmed"]]
    unconfirmed = events[~events["confirmed"]]

    return {
        "ops": len(OPS),
        "runs": runs,
        "normal_runs": runs - len(OPS),
        "anomalous_runs": len(OPS),
        "steps": steps,
        "hours": seconds / 3600,
        "confirmed": confirmed["event_id"].nunique(),
        "unconfirmed": unconfirmed["event_id"].nunique(),
        "intervals": len(confirmed),
    }


def data_missing():
    return not os.path.isdir(DATA_DIR)
