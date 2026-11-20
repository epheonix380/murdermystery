"""Draw a case's floor plan (extras.json "map") as a standalone SVG image.

The result is what the case browser shows. Colours are written into the file
so it looks the same anywhere: in the app, opened directly, or printed.
"""

from xml.sax.saxutils import escape

BG, ROOM, OUTDOOR, EDGE, WALL = "#121016", "#1d1924", "#2c2636", "#5b5168", "#a89cb8"
TEXT, MUTED, DOOR, SEAL = "#ece6f2", "#a89cb8", "#f07a2e", "#9a7bff"


def render(map_data, title="Floor plan"):
    rooms = map_data["rooms"]
    x0 = min(r["x"] for r in rooms) - 8
    y0 = min(r["y"] for r in rooms) - 8
    width = max(r["x"] + r["w"] for r in rooms) - x0 + 8
    height = max(r["y"] + r["h"] for r in rooms) - y0 + 8

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{escape(title, {chr(34): "&quot;"})}" font-family="Inter, system-ui, sans-serif">',
        f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="{BG}"/>',
    ]
    for r in rooms:
        kind = r.get("kind")
        fill = OUTDOOR if kind == "outdoor" else ROOM
        rx = 8 if kind == "outdoor" else 0
        dash = ' stroke-dasharray="6 4"' if kind == "upstairs" else ""
        out.append(f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["w"]}" height="{r["h"]}" rx="{rx}" fill="{fill}" stroke="{EDGE}"{dash}/>')
    for x, y, w, h in map_data.get("walls", []):
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{WALL}" stroke-width="3"/>')
    for x1, y1, x2, y2 in map_data.get("doors", []):
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{DOOR}" stroke-width="5" stroke-linecap="round"/>')
    for r in rooms:
        name = escape(r["name"])
        if r.get("center"):
            out.append(f'<text x="{r["x"] + r["w"] / 2:g}" y="{r["y"] + r["h"] / 2 + 5:g}" text-anchor="middle" fill="{TEXT}" font-size="14" font-weight="600">{name}</text>')
            continue
        y = r["y"] + 22
        out.append(f'<text x="{r["x"] + 12}" y="{y}" fill="{TEXT}" font-size="14" font-weight="600">{name}</text>')
        for line in r.get("lines", []):
            y += 18
            out.append(f'<text x="{r["x"] + 12}" y="{y}" fill="{MUTED}" font-size="12">{escape(line)}</text>')
        if r.get("sealed"):
            y += 18
            out.append(f'<circle cx="{r["x"] + 16}" cy="{y - 4}" r="5" fill="{SEAL}"/>'
                       f'<text x="{r["x"] + 26}" y="{y}" fill="{MUTED}" font-size="12">{escape(r["sealed"])}</text>')
    for label in map_data.get("labels", []):
        out.append(f'<text x="{label["x"]}" y="{label["y"]}" text-anchor="middle" fill="{MUTED}" font-size="12">{escape(label["text"])}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
