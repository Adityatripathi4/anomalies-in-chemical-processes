# Reads the anomaly annotations from the YAML files.
# The files need cleaning first:
#  - the same anomaly id can appear more than once, once per sensor
#  - hasBeginning / hasEnd are sometimes lists with many time intervals
#  - OP29 has anomalies with class "Anomaly" instead of "ConfirmedAnomaly",
#    they have no description and no timing details

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

OPS = ["OP10", "OP17", "OP18", "OP22", "OP29", "OP31"]


def as_list(value):
    # some fields are a single value, some are a list
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_sensors(entry):
    names = []
    for mode in as_list(entry.get("PerturbationMode")):
        for effect in as_list(mode.get("hasLocalEffect")):
            for value in effect.values():
                for item in as_list(value):
                    sensor = item.get("madeBySensor", {}).get("Sensor", {})
                    if sensor.get("id"):
                        names.append(sensor["id"])
    return names


def get_sources(entry):
    # the equipment where the disturbance was applied
    found = []
    for mode in as_list(entry.get("PerturbationMode")):
        system = (mode.get("happenedAt") or {}).get("System") or {}
        if system.get("id"):
            found.append((system["id"], system.get("label", "")))
    return found


def get_effects(entry):
    # what was observed, and on which part of the plant
    found = []
    for mode in as_list(entry.get("PerturbationMode")):
        for effect in as_list(mode.get("hasLocalEffect")):
            for value in effect.values():
                for item in as_list(value):
                    label = item.get("label")
                    where = item.get("hasFeatureOfInterest", {}).get("FeatureOfInterest")
                    if label:
                        found.append((label, where or ""))
    return found


def get_intervals(entry):
    starts = sorted(pd.Timedelta(t) for t in as_list(entry.get("hasBeginning")))
    ends = sorted(pd.Timedelta(t) for t in as_list(entry.get("hasEnd")))

    intervals = []
    skipped = 0
    for start, end in zip(starts, ends):
        if end <= start or (intervals and start < intervals[-1][1]):
            skipped += 1
        else:
            intervals.append((start, end))
    return intervals, skipped


def load_annotations(path, op, run_start=None, run_end=None):
    """One row per anomaly interval."""
    data = yaml.safe_load(open(path))

    groups = {}
    for entry in data.get("anomalies", []):
        groups.setdefault(entry["id"], []).append(entry)

    rows = []
    for anomaly_id, entries in groups.items():
        sensors, sources, effects = [], [], []
        for entry in entries:
            sensors += get_sensors(entry)
            sources += get_sources(entry)
            effects += get_effects(entry)
        sensors = list(dict.fromkeys(sensors))
        sources = list(dict.fromkeys(sources))
        effects = list(dict.fromkeys(effects))

        # if the same anomaly is listed twice, use the entry whose
        # time list actually makes sense
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
                    continue
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
                "status": entry.get("class") or "Anomaly",
                "confirmed": entry.get("class") == "ConfirmedAnomaly",
                "perturbation": entry.get("Perturbation") or "",
                "recovery": entry.get("hasRecoveryAction") or "",
                "sensors": ", ".join(sensors),
                "source_ids": ", ".join(i for i, _ in sources),
                "source_labels": " / ".join(label for _, label in sources if label),
                "effects": " / ".join(label for label, _ in effects),
                "effect_parts": " / ".join(where for _, where in effects if where),
            })

    columns = ["op", "event_id", "interval", "start", "end", "duration_s", "category",
               "status", "confirmed", "perturbation", "recovery", "sensors",
               "source_ids", "source_labels", "effects", "effect_parts"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).sort_values("start").reset_index(drop=True)
