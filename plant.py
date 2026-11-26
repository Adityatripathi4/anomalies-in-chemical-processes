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


def chip(x, y, text, colour, anchor="middle"):
    """A small rounded label for a sensor."""
    w = 52
    left = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    return (f'<rect x="{left}" y="{y - 10}" width="{w}" height="15" rx="7.5" '
            f'fill="none" stroke="{colour}" stroke-width="1"/>'
            f'<text x="{left + w / 2}" y="{y + 0.5}" fill="{colour}" font-size="9.5" '
            f'text-anchor="middle" letter-spacing="0.3">{text}</text>')



def symbol(kind, x, y, colour):
    """A small equipment symbol, drawn in a 26 by 26 box with its top-left at x, y."""
    o = []
    if kind == "pump":
        o.append(f'<circle cx="{x + 13}" cy="{y + 13}" r="10" fill="none" '
                 f'stroke="{colour}" stroke-width="1.4"/>')
        o.append(f'<path d="M{x + 9},{y + 7} L{x + 20},{y + 13} L{x + 9},{y + 19} z" '
                 f'fill="none" stroke="{colour}" stroke-width="1.4" '
                 f'stroke-linejoin="round"/>')
    elif kind == "exchanger":
        o.append(f'<rect x="{x + 2}" y="{y + 4}" width="22" height="18" rx="3" '
                 f'fill="none" stroke="{colour}" stroke-width="1.4"/>')
        o.append(f'<path d="M{x + 5},{y + 13} L{x + 9},{y + 7} L{x + 13},{y + 19} '
                 f'L{x + 17},{y + 7} L{x + 21},{y + 13}" fill="none" '
                 f'stroke="{colour}" stroke-width="1.4" stroke-linejoin="round"/>')
    elif kind == "vessel":
        o.append(f'<rect x="{x + 5}" y="{y + 3}" width="16" height="20" rx="7" '
                 f'fill="none" stroke="{colour}" stroke-width="1.4"/>')
        o.append(f'<path d="M{x + 5},{y + 15} q4,-4 8,0 q4,4 8,0" fill="none" '
                 f'stroke="{colour}" stroke-width="1.3"/>')
    elif kind == "heater":
        o.append(f'<rect x="{x + 4}" y="{y + 4}" width="18" height="18" rx="4" '
                 f'fill="none" stroke="{colour}" stroke-width="1.4"/>')
        o.append(f'<path d="M{x + 8},{y + 19} L{x + 8},{y + 11} L{x + 13},{y + 11} '
                 f'L{x + 13},{y + 19} L{x + 18},{y + 19} L{x + 18},{y + 11}" '
                 f'fill="none" stroke="{colour}" stroke-width="1.4" '
                 f'stroke-linejoin="round"/>')
    elif kind == "gauge":
        o.append(f'<circle cx="{x + 13}" cy="{y + 13}" r="10" fill="none" '
                 f'stroke="{colour}" stroke-width="1.4"/>')
        o.append(f'<line x1="{x + 13}" y1="{y + 13}" x2="{x + 19}" y2="{y + 7}" '
                 f'stroke="{colour}" stroke-width="1.4" stroke-linecap="round"/>')
        o.append(f'<circle cx="{x + 13}" cy="{y + 13}" r="1.6" fill="{colour}"/>')
    return "".join(o)


def draw(selected=None, marked=()):
    """The plant as SVG. selected is highlighted, units in marked get a dot."""
    out = [f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" '
           'preserveAspectRatio="xMidYMid meet" '
           'style="width:100%;height:100%;display:block;'
           'font-family:system-ui,-apple-system,sans-serif">',
           f'<defs><marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" '
           f'orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="{EDGE}"/></marker></defs>']

    # pipes first, so the vessels sit on top of them
    for stream in STREAMS:
        points, label, at = stream[0], stream[1], stream[2]
        anchor = stream[3] if len(stream) > 3 else "start"
        path = " ".join(f"{x},{y}" for x, y in points)
        out.append(f'<polyline points="{path}" fill="none" stroke="{EDGE}" '
                   f'stroke-width="2" stroke-linejoin="round" marker-end="url(#arw)"/>')
        if label:
            out.append(f'<text x="{at[0]}" y="{at[1]}" fill="{MUTED}" font-size="12" '
                       f'text-anchor="{anchor}">{label}</text>')

    # the column: one vessel, three bands
    out.append(f'<rect x="{COLUMN_X}" y="60" width="{COLUMN_W}" height="240" rx="10" '
               f'fill="{BASE}" stroke="{EDGE}" stroke-width="1.5"/>')

    for band_id, (top, bottom) in BANDS.items():
        on = band_id == selected
        unit = UNITS[band_id]
        if on:
            out.append(f'<rect x="{COLUMN_X + 1.5}" y="{top + (1.5 if top == 60 else 0)}" '
                       f'width="{COLUMN_W - 3}" height="{bottom - top - (1.5 if top == 60 else 0)}" '
                       f'rx="{8 if top == 60 else 0}" fill="{GLOW}" stroke="{ACCENT}" '
                       f'stroke-width="2"/>')
        if top != 60:
            out.append(f'<line x1="{COLUMN_X}" y1="{top}" x2="{COLUMN_X + COLUMN_W}" '
                       f'y2="{top}" stroke="{EDGE}" stroke-width="1"/>')

        tray_colour = ACCENT if on else EDGE
        for k in range(1, 4):
            tray_y = top + k * (bottom - top) / 4
            out.append(f'<line x1="{COLUMN_X + 18}" y1="{tray_y}" '
                       f'x2="{COLUMN_X + COLUMN_W - 18}" y2="{tray_y}" '
                       f'stroke="{tray_colour}" stroke-width="1" opacity="0.45"/>')

        middle = (top + bottom) / 2
        out.append(f'<text x="{COLUMN_X + COLUMN_W / 2}" y="{middle + 1}" '
                   f'fill="{ACCENT if on else TEXT}" font-size="15" font-weight="600" '
                   f'text-anchor="middle">{band_id}</text>')
        out.append(f'<text x="{COLUMN_X + COLUMN_W / 2}" y="{middle + 17}" '
                   f'fill="{MUTED}" font-size="9.5" text-anchor="middle">'
                   f'{unit["name"].replace("Column section ", "section ")}</text>')

        # sensors to the left of the column, with a tick into it
        chip_y = middle - 9
        for sensor in unit["sensors"]:
            colour = ACCENT if on else MUTED
            out.append(f'<line x1="{COLUMN_X - 10}" y1="{chip_y - 4}" x2="{COLUMN_X}" '
                       f'y2="{chip_y - 4}" stroke="{colour}" stroke-width="1"/>')
            out.append(chip(COLUMN_X - 12, chip_y, sensor, colour, anchor="end"))
            chip_y += 21

        if band_id in marked:
            out.append(f'<circle cx="{COLUMN_X + COLUMN_W - 12}" cy="{top + 14}" '
                       f'r="5.5" fill="{MARK}"/>')

    # the boxed units
    for unit_id, unit in UNITS.items():
        if "box" not in unit:
            continue
        x, y, w, h = unit["box"]
        on = unit_id == selected
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                   f'fill="{GLOW if on else BASE}" stroke="{ACCENT if on else EDGE}" '
                   f'stroke-width="{2.5 if on else 1.5}"/>')

        if unit.get("symbol"):
            out.append(symbol(unit["symbol"], x + 10, y + 8, ACCENT if on else MUTED))

        cx = x + w / 2
        # the title sits beside the symbol rather than under it, so a long
        # label like HE001/HE002 has room
        text_x = x + 44 if unit.get("symbol") else cx
        anchor = "start" if unit.get("symbol") else "middle"
        out.append(f'<text x="{text_x}" y="{y + 27}" fill="{ACCENT if on else TEXT}" '
                   f'font-size="15" font-weight="600" text-anchor="{anchor}">'
                   f'{unit["label"]}</text>')
        out.append(f'<text x="{text_x}" y="{y + 44}" fill="{MUTED}" font-size="10" '
                   f'text-anchor="{anchor}">{unit["name"]}</text>')

        colour = ACCENT if on else MUTED
        chip_x = cx - (len(unit["sensors"]) * 58 - 6) / 2 + 26
        for sensor in unit["sensors"]:
            out.append(chip(chip_x, y + h - 18, sensor, colour))
            chip_x += 58

        if unit_id in marked:
            out.append(f'<circle cx="{x + w - 15}" cy="{y + h - 16}" r="5.5" '
                       f'fill="{MARK}"/>')

    out.append("</svg>")
    return "\n".join(out)


def page(selected=None, marked=()):
    """The drawing in a box of a fixed height, so it cannot collapse or overflow."""
    return ('<div style="width:100%;height:' + str(FRAME_HEIGHT) + 'px;'
            'background:transparent">' + draw(selected, marked) + "</div>")

