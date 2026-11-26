# The plant drawing for the process section.
# Units, which sensors sit on them, and where the disturbances were applied.

WIDTH, HEIGHT = 980, 470
FRAME_HEIGHT = 430

# the column is drawn as one vessel with three bands
COLUMN_X, COLUMN_W = 190, 120
BANDS = {"C003": (60, 140), "C002": (140, 220), "C001": (220, 300)}

UNITS = {
    "V001": dict(label="V001", name="Reboiler vessel", sensors=["T703"],
                 box=(170, 330, 160, 92), symbol="heater",
                 note="The mixture is heated here and partly evaporates."),
    "C001": dict(label="C001", name="Column section 1", sensors=["T709", "PDI701"],
                 band="C001",
                 note="Bottom section. The vapour rises from the reboiler."),
    "C002": dict(label="C002", name="Column section 2", sensors=["T711"],
                 band="C002",
                 note="Middle section. The vapour keeps getting richer in the "
                      "more volatile component."),
    "C003": dict(label="C003", name="Column section 3", sensors=["T712", "T705"],
                 band="C003",
                 note="Top section. The vapour leaves here for the condensers."),
    "HE": dict(label="HE001/HE002", name="Condensers", sensors=["FYI702"],
               box=(410, 60, 160, 92), symbol="exchanger",
               note="Cooling water turns the vapour back into liquid."),
    "V002": dict(label="V002", name="Buffer vessel", sensors=["PDI702"],
                 box=(630, 60, 150, 92), symbol="vessel",
                 note="Collects the condensed liquid before it is split into "
                      "reflux and distillate."),
    "G001": dict(label="G001", name="Pressure control", sensors=["PY23"],
                 box=(820, 60, 150, 92), symbol="gauge",
                 note="The plant runs below atmospheric pressure. Valve TV1 "
                      "sets it."),
    "P701": dict(label="P701", name="Reflux pump", sensors=["FT704"],
                 box=(410, 250, 150, 92), symbol="pump",
                 note="Sends part of the liquid back to the top of the column."),
    "P702": dict(label="P702", name="Distillate pump", sensors=["FT703"],
                 box=(630, 250, 150, 92), symbol="pump",
                 note="Takes the rest out as distillate, the top product."),
}

# which unit each piece of disturbance equipment sits on
SOURCE_UNITS = {
    "HV009": "V001",   # manual valve at the reboiler
    "HV001": "V001",   # side draw between reboiler and column
    "H701": "V001",    # reboiler heater
    "H702": "V001",    # reboiler heater
    "H704": "C002",    # column heater
    "HV004": "P701",   # sample valve on the reflux line
    "HV005": "P701",   # sample valve on the reflux line
    "P701": "P701",
    "P702": "P702",
    "TCU1": "HE",      # thermostat for the condensers
    "TV1": "G001",     # vacuum throttle valve
}

STREAMS = [
    ([(250, 330), (250, 300)], None, None),
    ([(250, 60), (250, 30), (490, 30), (490, 60)], "vapour", (330, 24)),
    ([(545, 20), (545, 60)], "cooling water", (553, 26)),
    ([(570, 106), (630, 106)], None, None),
    ([(780, 106), (820, 106)], None, None),
    ([(705, 152), (705, 205), (485, 205), (485, 250)], None, None),
    ([(705, 205), (705, 250)], None, None),
    ([(410, 296), (360, 296), (360, 100), (310, 100)], "reflux", (366, 330)),
    ([(780, 296), (860, 296)], "distillate", (790, 286)),
]

from palette import ACCENT, BASE, EDGE, GLOW, MARK, MUTED, TEXT


def sensor_unit(sensor):
    for unit_id, unit in UNITS.items():
        if sensor in unit["sensors"]:
            return unit_id
    return None


def disturbance_units(source_ids):
    """Turn a list of equipment ids into the units they sit on."""
    units = []
    for source in source_ids:
        unit = SOURCE_UNITS.get(source.strip())
        if unit and unit not in units:
            units.append(unit)
    return units




# ----------------------------------------------------------------- drawing
# The plant is drawn as a plotly figure rather than an svg, so that clicking
# a unit or a sensor is an ordinary streamlit event. Everything is placed in
# the coordinate system above, with y growing downwards, and the y axis is
# reversed to match.

import plotly.graph_objects as go

from anomaly_annotations import SENSOR_LABELS

CHIP_W, CHIP_H = 52, 16


def rounded(x, y, w, h, r):
    """An svg path for a rounded rectangle, which plotly accepts as a shape."""
    return (f"M {x + r},{y} L {x + w - r},{y} Q {x + w},{y} {x + w},{y + r} "
            f"L {x + w},{y + h - r} Q {x + w},{y + h} {x + w - r},{y + h} "
            f"L {x + r},{y + h} Q {x},{y + h} {x},{y + h - r} "
            f"L {x},{y + r} Q {x},{y} {x + r},{y} Z")


def symbol_shapes(kind, x, y, colour):
    """The little equipment symbol, as plotly shapes."""
    line = dict(color=colour, width=1.4)
    if kind == "pump":
        return [dict(type="circle", x0=x + 3, y0=y + 3, x1=x + 23, y1=y + 23, line=line),
                dict(type="path", path=f"M {x + 9},{y + 7} L {x + 20},{y + 13} "
                                       f"L {x + 9},{y + 19} Z", line=line)]
    if kind == "exchanger":
        return [dict(type="rect", x0=x + 2, y0=y + 4, x1=x + 24, y1=y + 22, line=line),
                dict(type="path", path=f"M {x + 5},{y + 13} L {x + 9},{y + 7} "
                                       f"L {x + 13},{y + 19} L {x + 17},{y + 7} "
                                       f"L {x + 21},{y + 13}", line=line)]
    if kind == "vessel":
        return [dict(type="path", path=rounded(x + 5, y + 3, 16, 20, 7), line=line),
                dict(type="path", path=f"M {x + 5},{y + 15} Q {x + 9},{y + 11} "
                                       f"{x + 13},{y + 15} Q {x + 17},{y + 19} "
                                       f"{x + 21},{y + 15}", line=line)]
    if kind == "heater":
        return [dict(type="path", path=rounded(x + 4, y + 4, 18, 18, 4), line=line),
                dict(type="path", path=f"M {x + 8},{y + 19} L {x + 8},{y + 11} "
                                       f"L {x + 13},{y + 11} L {x + 13},{y + 19} "
                                       f"L {x + 18},{y + 19} L {x + 18},{y + 11}",
                     line=line)]
    if kind == "gauge":
        return [dict(type="circle", x0=x + 3, y0=y + 3, x1=x + 23, y1=y + 23, line=line),
                dict(type="line", x0=x + 13, y0=y + 13, x1=x + 19, y1=y + 7, line=line),
                dict(type="circle", x0=x + 11.4, y0=y + 11.4, x1=x + 14.6, y1=y + 14.6,
                     line=dict(color=colour, width=1), fillcolor=colour)]
    return []


def chip_positions(unit_id):
    """Where this unit's sensor chips sit, in order."""
    unit = UNITS[unit_id]
    places = []
    if "band" in unit:
        top, bottom = BANDS[unit["band"]]
        y = (top + bottom) / 2 - 9
        for _ in unit["sensors"]:
            places.append((COLUMN_X - 14 - CHIP_W, y - 4))
            y += 21
    else:
        x, y, w, h = unit["box"]
        start = x + w / 2 - (len(unit["sensors"]) * 58 - 6) / 2 + 26
        for _ in unit["sensors"]:
            places.append((start, y + h - 24))
            start += 58
    return places


def figure(selected_unit=None, selected_sensor=None, marked=()):
    """The plant, ready for st.plotly_chart with on_select."""
    shapes, notes = [], []
    click_x, click_y, click_kind, click_text = [], [], [], []

    def label(x, y, text, colour, size=12, weight=None, anchor="center"):
        notes.append(dict(x=x, y=y, text=(f"<b>{text}</b>" if weight else text),
                          showarrow=False, font=dict(color=colour, size=size),
                          xanchor=anchor, yanchor="middle"))

    # pipes
    for stream in STREAMS:
        points, name, at = stream[0], stream[1], stream[2]
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                               line=dict(color=EDGE, width=2), layer="below"))
        # an arrowhead on the last segment, so flow direction still reads
        (tail_x, tail_y), (head_x, head_y) = points[-2], points[-1]
        notes.append(dict(x=head_x, y=head_y, ax=tail_x, ay=tail_y,
                          xref="x", yref="y", axref="x", ayref="y",
                          text="", showarrow=True, arrowhead=2, arrowsize=1.2,
                          arrowwidth=2, arrowcolor=EDGE))
        if name:
            label(at[0], at[1], name, MUTED, 11, anchor="left")

    def draw_chips(unit_id, on):
        for (cx, cy), sensor in zip(chip_positions(unit_id), UNITS[unit_id]["sensors"]):
            picked = sensor == selected_sensor
            colour = ACCENT if (on or picked) else MUTED
            shapes.append(dict(type="path", path=rounded(cx, cy, CHIP_W, CHIP_H, 8),
                               line=dict(color=colour, width=2 if picked else 1),
                               fillcolor=GLOW if picked else "rgba(0,0,0,0)"))
            if "band" in UNITS[unit_id]:
                shapes.append(dict(type="line", x0=cx + CHIP_W, y0=cy + CHIP_H / 2,
                                   x1=COLUMN_X, y1=cy + CHIP_H / 2,
                                   line=dict(color=colour, width=1), layer="below"))
            label(cx + CHIP_W / 2, cy + CHIP_H / 2, sensor, colour, 9.5)
            click_x.append(cx + CHIP_W / 2)
            click_y.append(cy + CHIP_H / 2)
            click_kind.append("sensor:" + sensor)
            click_text.append(sensor + " - " + SENSOR_LABELS[sensor])

    # the column, as one vessel with three bands
    shapes.append(dict(type="path", path=rounded(COLUMN_X, 60, COLUMN_W, 240, 10),
                       line=dict(color=EDGE, width=1.5), fillcolor=BASE, layer="below"))

    for band_id, (top, bottom) in BANDS.items():
        on = band_id == selected_unit
        unit = UNITS[band_id]
        if on:
            shapes.append(dict(type="path",
                               path=rounded(COLUMN_X + 2, top + 1, COLUMN_W - 4,
                                            bottom - top - 2, 8),
                               line=dict(color=ACCENT, width=2), fillcolor=GLOW))
        if top != 60:
            shapes.append(dict(type="line", x0=COLUMN_X, y0=top, x1=COLUMN_X + COLUMN_W,
                               y1=top, line=dict(color=EDGE, width=1)))
        for k in range(1, 4):
            tray = top + k * (bottom - top) / 4
            shapes.append(dict(type="line", x0=COLUMN_X + 18, y0=tray,
                               x1=COLUMN_X + COLUMN_W - 18, y1=tray,
                               line=dict(color=ACCENT if on else EDGE, width=1),
                               opacity=0.45, layer="below"))

        middle = (top + bottom) / 2
        label(COLUMN_X + COLUMN_W / 2, middle - 6, band_id, ACCENT if on else TEXT, 14, True)
        label(COLUMN_X + COLUMN_W / 2, middle + 9,
              unit["name"].replace("Column section ", "section "), MUTED, 9.5)
        draw_chips(band_id, on)

        click_x.append(COLUMN_X + COLUMN_W / 2)
        click_y.append(middle - 6)
        click_kind.append("unit:" + band_id)
        click_text.append(band_id + " - " + unit["name"])

        if band_id in marked:
            shapes.append(dict(type="circle", x0=COLUMN_X + COLUMN_W - 18, y0=top + 8,
                               x1=COLUMN_X + COLUMN_W - 6, y1=top + 20,
                               fillcolor=MARK, line=dict(width=0)))

    # the boxed units
    for unit_id, unit in UNITS.items():
        if "box" not in unit:
            continue
        x, y, w, h = unit["box"]
        on = unit_id == selected_unit
        shapes.append(dict(type="path", path=rounded(x, y, w, h, 10),
                           line=dict(color=ACCENT if on else EDGE,
                                     width=2.5 if on else 1.5),
                           fillcolor=GLOW if on else BASE, layer="below"))
        if unit.get("symbol"):
            shapes += symbol_shapes(unit["symbol"], x + 10, y + 8,
                                    ACCENT if on else MUTED)

        text_x = x + 44 if unit.get("symbol") else x + w / 2
        anchor = "left" if unit.get("symbol") else "center"
        label(text_x, y + 22, unit["label"], ACCENT if on else TEXT, 14, True, anchor)
        label(text_x, y + 39, unit["name"], MUTED, 10, anchor=anchor)
        draw_chips(unit_id, on)

        click_x.append(x + w / 2)
        click_y.append(y + 22)
        click_kind.append("unit:" + unit_id)
        click_text.append(unit["label"] + " - " + unit["name"])

        if unit_id in marked:
            shapes.append(dict(type="circle", x0=x + w - 21, y0=y + h - 22,
                               x1=x + w - 9, y1=y + h - 10,
                               fillcolor=MARK, line=dict(width=0)))

    fig = go.Figure()
    # the click targets: invisible, but big enough to hit comfortably
    fig.add_trace(go.Scatter(
        x=click_x, y=click_y, mode="markers",
        marker=dict(size=30, color="rgba(0,0,0,0)"),
        customdata=click_kind, text=click_text,
        hovertemplate="%{text}<extra></extra>", showlegend=False))

    fig.update_layout(
        shapes=shapes, annotations=notes,
        height=430, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False, clickmode="event+select",
        xaxis=dict(range=[0, WIDTH], visible=False, fixedrange=True,
                   constrain="domain"),
        yaxis=dict(range=[HEIGHT, 0], visible=False, fixedrange=True,
                   scaleanchor="x", scaleratio=1, constrain="domain"),
    )
    return fig
