# Loads the anomaly annotations from the YAML files.
# The files need some cleaning first:
#  - the same anomaly id can appear more than once, once per sensor
#  - hasBeginning / hasEnd are sometimes lists with many time intervals
#  - OP29 has some anomalies with no category

import pandas as pd
import yaml

SENSORS = ["FT703", "FT704", "FYI702", "PDI701", "PDI702", "PY23",
           "T703", "T705", "T709", "T711", "T712"]

SENSOR_LABELS = {
    "FT703": "Flow, top product stream",
    "FT704": "Flow, reflux stream",
    "FYI702": "Cooling water flow",
    "PDI701": "Pressure difference along column",
    "PDI702": "Pressure difference, buffer vessel",
    "PY23": "Pressure, top vessel",
    "T703": "Temperature, reboiler",
    "T705": "Temperature, top of column",
    "T709": "Temperature, below section C001",
    "T711": "Temperature, between C001 and C002",
    "T712": "Temperature, between C002 and C003",
}


def as_list(value):
    # some fields are a single value, some are a list
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_sensors(entry):
    # dig out the sensor ids mentioned in this entry
    names = []
    for mode in as_list(entry.get("PerturbationMode")):
        for effect in as_list(mode.get("hasLocalEffect")):
            for value in effect.values():
                for item in as_list(value):
                    sensor = item.get("madeBySensor", {}).get("Sensor", {})
                    if sensor.get("id"):
                        names.append(sensor["id"])
    return names


def get_intervals(entry):
    # pair up the start and end times
    starts = sorted(pd.Timedelta(t) for t in as_list(entry.get("hasBeginning")))
    ends = sorted(pd.Timedelta(t) for t in as_list(entry.get("hasEnd")))

    intervals = []
    skipped = 0
    for start, end in zip(starts, ends):
        # skip anything that ends before it starts, or overlaps the one before
        if end <= start or (intervals and start < intervals[-1][1]):
            skipped += 1
        else:
            intervals.append((start, end))
    return intervals, skipped


def load_annotations(path, op, run_start=None, run_end=None):
    """Return one row per anomaly interval."""
    data = yaml.safe_load(open(path))

    # group the entries that belong to the same anomaly
    groups = {}
    for entry in data.get("anomalies", []):
        groups.setdefault(entry["id"], []).append(entry)

    rows = []
    for anomaly_id, entries in groups.items():
        sensors = []
        for entry in entries:
            sensors += get_sensors(entry)
        sensors = list(dict.fromkeys(sensors))

        # if the same anomaly is listed twice, use the entry with
        # the time list that actually makes sense
        best = None
        for entry in entries:
            intervals, skipped = get_intervals(entry)
            score = (skipped == 0, len(intervals))
            if best is None or score > best[0]:
                best = (score, intervals, entry)
        intervals, entry = best[1], best[2]

        for i, (start, end) in enumerate(intervals):
            if run_start is not None:
                if end < run_start or start > run_end:
                    continue            # outside the recording
                start = max(start, run_start)
                end = min(end, run_end)

            rows.append({
                "op": op,
                "event_id": anomaly_id,
                "interval": i,
                "start": start,
                "end": end,
                "duration_s": int((end - start).total_seconds()),
                "category": entry.get("hasCategory") or "unspecified",
                "sensors": ", ".join(sensors),
                "no_category": entry.get("hasCategory") is None,
            })

    if not rows:
        return pd.DataFrame(columns=["op", "event_id", "interval", "start", "end",
                                     "duration_s", "category", "sensors", "no_category"])
    return pd.DataFrame(rows).sort_values("start").reset_index(drop=True)
