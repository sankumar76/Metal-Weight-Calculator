"""Shape diagrams, rendered with Pillow.

Every shape is described once as a 2-D cross-section (polygons in mm, y up).
From that single description we render:

  * a detailed, dimensioned 3-D view for the calculator pages,
  * a 3-D thumbnail for the home-screen tiles,
  * a flat silhouette icon for the sidebar.

Drawings are supersampled and downscaled so edges are anti-aliased (the Tk
canvas cannot anti-alias polygons on Windows).
"""

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS = 3  # supersampling factor

# Extrusion direction for the oblique 3-D view (30 degrees, up and to the right).
_DIR = (math.cos(math.radians(30)), -math.sin(math.radians(30)))

STEEL = {
    "face_top": (244, 247, 251),
    "face_bottom": (197, 210, 227),
    "side_back": (52, 78, 114),
    "side_front": (118, 142, 175),
    "outline": (26, 48, 82),
    "dim": (217, 119, 6),
    "text": (15, 23, 42),
    "pill": (255, 255, 255),
    "shadow": (15, 23, 42),
}


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
@lru_cache(maxsize=32)
def _font(size: int, bold: bool = True):
    names = ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fmt(v: float) -> str:
    return ("%.2f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Shape definitions
# ---------------------------------------------------------------------------
def _circle(cx, cy, r, n=144):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _aspect(w, h, limit=3.2):
    """Visually limit extreme aspect ratios so the drawing stays legible."""
    if w / h > limit:
        h = w / limit
    elif h / w > limit:
        w = h / limit
    return w, h


def _round_bar(v, lab):
    d = v["D"]
    return dict(
        size=(d, d),
        outer=[_circle(d / 2, d / 2, d / 2)],
        dims=[("hdim", 0, d, lab["D"], 0, d / 2)],
    )


def _pipe(v, lab):
    od = v["OD"]
    idm = _clamp(v["ID"], 0, od * 0.88)
    if 0 < idm < od * 0.3:
        idm = od * 0.3
    holes = [_circle(od / 2, od / 2, idm / 2)] if idm > 0 else []
    dims = [("hdim", 0, od, lab["OD"], 0, od / 2)]
    if idm > 0:
        dims.append(("inner", od / 2 - idm / 2, od / 2 + idm / 2, od / 2, lab["ID"]))
    return dict(size=(od, od), outer=[_circle(od / 2, od / 2, od / 2)], holes=holes, dims=dims)


def _box(v, lab):
    a, b = _aspect(v["A"], v["B"])
    m = min(a, b)
    t = _clamp(v["t"] * a / v["A"], 0.07 * m, 0.32 * m)
    return dict(
        size=(a, b),
        outer=[_rect(0, 0, a, b)],
        holes=[_rect(t, t, a - t, b - t)],
        dims=[
            ("hdim", 0, a, lab["A"], 0, 0),
            ("vdim", 0, b, lab["B"], 0, 0),
            ("xcall", 0, t, b / 2, lab["t"], (t, b / 2, 18, 0)),
        ],
    )


def _plate(v, lab):
    w = v["W"]
    t = _clamp(v["T"], 0.06 * w, 0.16 * w)
    return dict(
        size=(w, t),
        outer=[_rect(0, 0, w, t)],
        dims=[("hdim", 0, w, lab["W"], 0, 0), ("vdim", 0, t, lab["T"], 0, 0)],
        depth=0.62,
    )


def _i_like_dims(v):
    h, b = v["H"], v["B"]
    h2, b2 = _aspect(h, b, 3.0)
    k = max(h2, b2)
    tw = _clamp(v["tw"] * b2 / b, 0.04 * k, 0.3 * b2)
    tf = _clamp(v["tf"] * h2 / h, 0.04 * k, 0.28 * h2)
    return h2, b2, tw, tf


def _beam(v, lab):
    h, b, tw, tf = _i_like_dims(v)
    c = b / 2
    poly = [(0, 0), (b, 0), (b, tf), (c + tw / 2, tf), (c + tw / 2, h - tf), (b, h - tf),
            (b, h), (0, h), (0, h - tf), (c - tw / 2, h - tf), (c - tw / 2, tf), (0, tf)]
    return dict(
        size=(b, h),
        outer=[poly],
        dims=[
            ("vdim", 0, h, lab["H"], 0, 0),
            ("hdim", 0, b, lab["B"], 0, 0),
            ("xcall", c - tw / 2, c + tw / 2, h / 2, lab["tw"], (b, h / 2, 12, 0)),
            ("ycall", h - tf, h, b * 0.9, lab["tf"], (b, h - tf, 12, 18)),
        ],
    )


def _channel(v, lab):
    h, b, tw, tf = _i_like_dims(v)
    poly = [(0, 0), (b, 0), (b, tf), (tw, tf), (tw, h - tf), (b, h - tf), (b, h), (0, h)]
    return dict(
        size=(b, h),
        outer=[poly],
        dims=[
            ("vdim", 0, h, lab["H"], 0, 0),
            ("hdim", 0, b, lab["B"], 0, 0),
            ("xcall", 0, tw, h / 2, lab["tw"], (b, h / 2, 12, 0)),
            ("ycall", h - tf, h, b * 0.86, lab["tf"], (b, h - tf, 12, 18)),
        ],
    )


def _angle(v, lab):
    a, b = _aspect(v["A"], v["B"])
    t = _clamp(v["t"] * a / v["A"], 0.07 * max(a, b), 0.3 * min(a, b))
    poly = [(0, 0), (b, 0), (b, t), (t, t), (t, a), (0, a)]
    return dict(
        size=(b, a),
        outer=[poly],
        dims=[
            ("vdim", 0, a, lab["A"], 0, 0),
            ("hdim", 0, b, lab["B"], 0, 0),
            ("xcall", 0, t, a * 0.7, lab["t"], (t, a * 0.7, 18, 0)),
        ],
    )


def _tee(v, lab):
    h, b, tw, tf = _i_like_dims(v)
    c = b / 2
    poly = [(c - tw / 2, 0), (c + tw / 2, 0), (c + tw / 2, h - tf), (b, h - tf), (b, h),
            (0, h), (0, h - tf), (c - tw / 2, h - tf)]
    return dict(
        size=(b, h),
        outer=[poly],
        dims=[
            ("vdim", 0, h, lab["H"], 0, 0),
            ("hdim", 0, b, lab["B"], 0, 0),
            ("xcall", c - tw / 2, c + tw / 2, (h - tf) * 0.45, lab["tw"], (b, (h - tf) * 0.45, 12, 0)),
            ("ycall", h - tf, h, b * 0.88, lab["tf"], (b, h - tf, 12, 18)),
        ],
    )


def _valid_pipe(v):
    return v["OD"] > 0 and 0 <= v["ID"] < v["OD"]


def _valid_box(v):
    return min(v.values()) > 0 and 2 * v["t"] < min(v["A"], v["B"])


def _valid_i(v):
    return min(v.values()) > 0 and 2 * v["tf"] < v["H"] and v["tw"] < v["B"]


def _valid_tee(v):
    return min(v.values()) > 0 and v["tf"] < v["H"] and v["tw"] < v["B"]


def _valid_angle(v):
    return min(v.values()) > 0 and v["t"] < min(v["A"], v["B"])


def _positive(v):
    return min(v.values()) > 0


# kind -> (builder, defaults, validator, label prefixes)
SHAPES = {
    "round_bar": (_round_bar, {"D": 50}, _positive, {"D": "Ø D"}),
    "pipe": (_pipe, {"OD": 60, "ID": 44}, _valid_pipe, {"OD": "Ø OD", "ID": "Ø ID"}),
    "box": (_box, {"A": 80, "B": 50, "t": 5}, _valid_box, {}),
    "plate": (_plate, {"W": 400, "T": 30}, _positive, {}),
    "beam": (_beam, {"H": 250, "B": 125, "tw": 6.9, "tf": 12.5}, _valid_i, {}),
    "channel": (_channel, {"H": 200, "B": 75, "tw": 6.2, "tf": 11.4}, _valid_i, {}),
    "angle": (_angle, {"A": 75, "B": 75, "t": 8}, _valid_angle, {}),
    "tee": (_tee, {"H": 100, "B": 100, "tw": 8, "tf": 10}, _valid_tee, {}),
}


def _section(kind, values=None):
    """Resolve the geometry for *kind*. Missing/invalid values fall back to
    default proportions and symbol-only labels."""
    builder, defaults, valid, prefixes = SHAPES[kind]
    vals, labels = dict(defaults), {k: prefixes.get(k, k) for k in defaults}
    if values:
        try:
            given = {k: float(values[k]) for k in defaults}
        except (KeyError, TypeError, ValueError):
            given = None
        if given and valid(given):
            vals = given
            labels = {k: f"{labels[k]} = {_fmt(given[k])}" for k in defaults}
    geom = builder(vals, labels)
    geom.setdefault("holes", [])
    geom.setdefault("depth", 0.30)
    return geom


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def _lerp(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def _vertical_gradient(size, top, bottom):
    w, h = size
    col = Image.new("RGB", (1, max(h, 1)))
    for y in range(max(h, 1)):
        col.putpixel((0, y), _lerp(top, bottom, y / max(h - 1, 1)))
    return col.resize((max(w, 1), max(h, 1)))


def _arrow(draw, tip, frm, k, color):
    """Filled arrowhead at *tip*, pointing away from *frm*."""
    dx, dy = tip[0] - frm[0], tip[1] - frm[1]
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    ln, hw = 7 * k, 3.2 * k
    bx, by = tip[0] - ux * ln, tip[1] - uy * ln
    draw.polygon([tip, (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw)], fill=color)


def _pill(draw, center, text, k, align="center"):
    font = _font(int(11 * k))
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    tw, th = r - l, b - t
    pw, ph = tw + 14 * k, 20 * k
    cx, cy = center
    if align == "left":
        cx += pw / 2
    elif align == "right":
        cx -= pw / 2
    box = (cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2)
    draw.rounded_rectangle(box, radius=ph / 2, fill=STEEL["pill"], outline=STEEL["dim"], width=max(1, int(1.2 * k)))
    draw.text((cx - tw / 2 - l, cy - th / 2 - t), text, font=font, fill=STEEL["text"])


def _line(draw, p0, p1, k, width=1.1):
    draw.line([p0, p1], fill=STEEL["dim"], width=max(1, int(width * k)))


def _dim_line(draw, p0, p1, label, k):
    """Dimension line between p0 and p1 with arrowheads at both ends."""
    _line(draw, p0, p1, k)
    _arrow(draw, p0, p1, k, STEEL["dim"])
    _arrow(draw, p1, p0, k, STEEL["dim"])
    _pill(draw, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), label, k)


def _layout(geom, width, height, k, detailed):
    bw, bh = geom["size"]
    if detailed:
        dims = geom["dims"]
        nv = 1 + max([d[4] for d in dims if d[0] == "vdim"], default=-1)
        nh = 1 + max([d[4] for d in dims if d[0] == "hdim"], default=-1)
        right_pills = any(d[0] in ("xcall", "ycall") and d[5][0] >= bw for d in dims)
        left = (24 + 28 * nv + 30) * k if nv else 16 * k
        bottom = (18 + 26 * nh + 12) * k if nh else 16 * k
        right = 96 * k if right_pills else 22 * k
        top = 38 * k
    else:
        left = right = width * 0.12
        top = height * 0.12
        bottom = height * 0.16
    aw, ah = width - left - right, height - top - bottom
    depth = geom["depth"] * min(aw, ah) * (1.0 if detailed else 1.1)
    dx, dy = depth * _DIR[0], -depth * _DIR[1]
    s = min((aw - dx) / bw, (ah - dy) / bh)
    comp_w, comp_h = bw * s + dx, bh * s + dy
    fx = left + (aw - comp_w) / 2
    fy = top + (ah - comp_h) / 2 + dy  # top edge of the front face
    return s, fx, fy, dx, dy


def _render_solid(img, geom, s, fx, fy, dx, dy, k, pal=STEEL):
    bw, bh = geom["size"]
    to_px = lambda p: ((p[0]) * s, (bh - p[1]) * s)  # relative to front-face origin
    mw, mh = int(math.ceil(bw * s)) + 2, int(math.ceil(bh * s)) + 2
    mask = Image.new("L", (mw, mh), 0)
    md = ImageDraw.Draw(mask)
    for poly in geom["outer"]:
        md.polygon([to_px(p) for p in poly], fill=255)
    for poly in geom["holes"]:
        md.polygon([to_px(p) for p in poly], fill=0)

    # Extrusion: stack the section from the back to the front. The sides are
    # a smooth gradient, so this is done at a lower resolution for speed.
    r = min(1.0, 1.6 / SS)
    W, H = img.size
    low = Image.new("RGBA", (max(1, int(W * r)), max(1, int(H * r))), (0, 0, 0, 0))
    lmask = mask.resize((max(1, int(mw * r)), max(1, int(mh * r))), Image.BILINEAR)
    steps = max(int(math.hypot(dx, dy) * r / 2.0), 1)
    for i in range(steps, 0, -1):
        t = i / steps
        color = _lerp(pal["side_front"], pal["side_back"], t) + (255,)
        low.paste(color, (int(round((fx + dx * t) * r)), int(round((fy - dy * t) * r))), lmask)
    low = low.resize((W, H), Image.BILINEAR)
    img.paste(low, (0, 0), low)

    face = _vertical_gradient((mw, mh), pal["face_top"], pal["face_bottom"])
    img.paste(face, (int(round(fx)), int(round(fy))), mask)

    draw = ImageDraw.Draw(img)
    ow = max(1, int(1.4 * k))
    for poly in geom["outer"] + geom["holes"]:
        pts = [(fx + x, fy + y) for x, y in (to_px(p) for p in poly)]
        draw.line(pts + [pts[0]], fill=pal["outline"], width=ow, joint="curve")
    return draw


def _render_dims(draw, geom, s, fx, fy, dx, dy, k):
    bw, bh = geom["size"]
    X = lambda x: fx + x * s
    Y = lambda y: fy + (bh - y) * s
    al = 12 * k  # arrow tail length for thickness call-outs

    for d in geom["dims"]:
        kind = d[0]
        if kind == "hdim":
            _, x1, x2, label, level, ext_y = d
            yl = Y(0) + (18 + 26 * level) * k
            for x in (x1, x2):
                _line(draw, (X(x), Y(ext_y) + 3 * k), (X(x), yl + 5 * k), k, 0.8)
            _dim_line(draw, (X(x1), yl), (X(x2), yl), label, k)
        elif kind == "vdim":
            _, y1, y2, label, level, ext_x = d
            xl = X(0) - (24 + 28 * level) * k
            for y in (y1, y2):
                _line(draw, (X(ext_x) - 3 * k, Y(y)), (xl - 5 * k, Y(y)), k, 0.8)
            _dim_line(draw, (xl, Y(y2)), (xl, Y(y1)), label, k)
        elif kind == "inner":
            _, x1, x2, y, label = d
            _dim_line(draw, (X(x1), Y(y)), (X(x2), Y(y)), label, k)
        elif kind == "xcall":
            _, x1, x2, y, label, (lx, ly, ox, oy) = d
            yy = Y(y)
            _line(draw, (X(x1) - al, yy), (X(x1), yy), k)
            _arrow(draw, (X(x1), yy), (X(x1) - al, yy), k, STEEL["dim"])
            _line(draw, (X(x2) + al, yy), (X(x2), yy), k)
            _arrow(draw, (X(x2), yy), (X(x2) + al, yy), k, STEEL["dim"])
            px, py = X(lx) + ox * k, Y(ly) + oy * k
            _line(draw, (X(x2) + al, yy), (px, py), k)
            _pill(draw, (px, py), label, k, align="left")
        elif kind == "ycall":
            _, y1, y2, x, label, (lx, ly, ox, oy) = d
            xx = X(x)
            _line(draw, (xx, Y(y2) - al), (xx, Y(y2)), k)
            _arrow(draw, (xx, Y(y2)), (xx, Y(y2) - al), k, STEEL["dim"])
            _line(draw, (xx, Y(y1) + al), (xx, Y(y1)), k)
            _arrow(draw, (xx, Y(y1)), (xx, Y(y1) + al), k, STEEL["dim"])
            px, py = X(lx) + ox * k, Y(ly) + oy * k
            _line(draw, (xx, Y(y1) + al), (xx, py), k)
            _line(draw, (xx, py), (px, py), k)
            _pill(draw, (px, py), label, k, align="left")

    # Length along the extrusion, offset from the upper-left silhouette edge.
    pts = [(X(x), Y(y)) for poly in geom["outer"] for x, y in poly]
    ax, ay = min(pts, key=lambda p: p[0] + p[1])
    nx, ny = -_DIR[1], -_DIR[0]  # perpendicular, pointing up-left
    off = 14 * k
    p0 = (ax + nx * off, ay + ny * off)
    p1 = (p0[0] + dx, p0[1] - dy)
    for (bx, by) in ((ax, ay), (ax + dx, ay - dy)):
        _line(draw, (bx + nx * 3 * k, by + ny * 3 * k), (bx + nx * (off + 5 * k), by + ny * (off + 5 * k)), k, 0.8)
    _dim_line(draw, p0, p1, geom.get("length_label", "L"), k)


def render_section(kind, values=None, length=None, width=400, height=300,
                   scale=1.0, bg=(255, 255, 255), detailed=True):
    """Render a shape as an RGB image of (width x height) * scale pixels.

    *values* maps dimension symbols (e.g. "H", "tw") to numbers; anything
    missing or invalid falls back to default proportions.
    """
    geom = _section(kind, values)
    if length:
        try:
            lv = float(length)
            geom["length_label"] = f"L = {_fmt(lv)}" if lv > 0 else "L"
        except (TypeError, ValueError):
            pass
    k = SS * scale
    W, H = int(width * k), int(height * k)
    img = Image.new("RGB", (W, H), bg)
    s, fx, fy, dx, dy = _layout(geom, W, H, k, detailed)

    if not detailed:
        # Soft contact shadow beneath the part.
        bw, bh = geom["size"]
        shadow = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(shadow)
        cx = fx + (bw * s + dx) / 2
        by = fy + bh * s
        sd.ellipse((cx - (bw * s + dx) * 0.55, by - 6 * k, cx + (bw * s + dx) * 0.55, by + 8 * k), fill=70)
        shadow = shadow.filter(ImageFilter.GaussianBlur(8 * k))
        img.paste(STEEL["shadow"], (0, 0), shadow)

    draw = _render_solid(img, geom, s, fx, fy, dx, dy, k)
    if detailed:
        _render_dims(draw, geom, s, fx, fy, dx, dy, k)
    return img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)


def render_icon(kind, size=20, color=(200, 210, 224), scale=1.0, bg=None):
    """Flat silhouette of the cross-section (for the sidebar)."""
    k = 4 * scale
    S = int(size * k)
    img = Image.new("RGBA", (S, S), bg or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = color + (255,) if len(color) == 3 else color

    if kind in SHAPES:
        geom = _section(kind)
        bw, bh = geom["size"]
        pad = S * 0.1
        s = (S - 2 * pad) / max(bw, bh)
        ox, oy = (S - bw * s) / 2, (S - bh * s) / 2
        pt = lambda p: (ox + p[0] * s, oy + (bh - p[1]) * s)
        for poly in geom["outer"]:
            draw.polygon([pt(p) for p in poly], fill=rgba)
        for poly in geom["holes"]:
            draw.polygon([pt(p) for p in poly], fill=bg or (0, 0, 0, 0))
    else:
        _draw_glyph(draw, kind, S, rgba, bg or (0, 0, 0, 0))
    return img.resize((int(size * scale), int(size * scale)), Image.LANCZOS)


def _draw_glyph(draw, kind, S, color, bg):
    """Simple glyphs for non-shape navigation items, drawn on a 100-unit grid."""
    u = S / 100.0
    P = lambda x, y: (x * u, y * u)
    w = max(1, int(8 * u))
    if kind == "home":
        draw.polygon([P(50, 10), P(92, 46), P(80, 46), P(80, 88), P(20, 88), P(20, 46), P(8, 46)], fill=color)
        draw.rectangle([P(42, 60), P(58, 88)], fill=bg)
    elif kind == "sg_ref":
        draw.polygon([P(36, 8), P(64, 8), P(64, 38), P(90, 86), P(84, 94), P(16, 94), P(10, 86), P(36, 38)], fill=color)
        draw.polygon([P(46, 18), P(54, 18), P(54, 42), P(72, 74), P(28, 74), P(46, 42)], fill=bg)
    elif kind == "units":
        draw.line([P(10, 34), P(84, 34)], fill=color, width=w)
        draw.polygon([P(90, 34), P(70, 18), P(70, 50)], fill=color)
        draw.line([P(16, 68), P(90, 68)], fill=color, width=w)
        draw.polygon([P(10, 68), P(30, 52), P(30, 84)], fill=color)
    elif kind == "about":
        draw.ellipse([P(6, 6), P(94, 94)], fill=color)
        draw.ellipse([P(43, 22), P(57, 36)], fill=bg)
        draw.rounded_rectangle([P(43, 44), P(57, 78)], radius=3 * u, fill=bg)


def render_reference_art(kind, size=64, scale=1.0, bg=(255, 255, 255)):
    """Small colour illustrations for the reference tiles (SG table, units)."""
    k = SS * scale
    S = int(size * k)
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)
    u = S / 100.0
    P = lambda x, y: (x * u, y * u)
    outline = STEEL["outline"]
    accent = (37, 99, 235)
    if kind == "sg_ref":
        d.rounded_rectangle([P(10, 10), P(90, 90)], radius=18 * u, fill=(232, 240, 254))
        flask = [P(40, 20), P(60, 20), P(60, 42), P(78, 76), P(74, 82), P(26, 82), P(22, 76), P(40, 42)]
        liquid = [P(31, 62), P(69, 62), P(78, 76), P(74, 82), P(26, 82), P(22, 76)]
        d.polygon(flask, fill=(255, 255, 255))
        d.polygon(liquid, fill=accent)
        d.line(flask + [flask[0]], fill=outline, width=max(1, int(3 * u)), joint="curve")
        d.line([P(36, 20), P(64, 20)], fill=outline, width=max(1, int(4 * u)))
        for (x, y, r) in ((44, 72, 3), (55, 68, 2.4), (60, 75, 2)):
            d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=(255, 255, 255))
    elif kind == "units":
        d.rounded_rectangle([P(10, 10), P(90, 90)], radius=18 * u, fill=(254, 243, 226))
        d.rounded_rectangle([P(18, 30), P(82, 54)], radius=4 * u, fill=(255, 255, 255), outline=outline, width=max(1, int(3 * u)))
        for i in range(9):
            x = 24 + i * 6.5
            d.line([P(x, 30), P(x, 30 + (12 if i % 2 == 0 else 7))], fill=outline, width=max(1, int(2.4 * u)))
        amber = STEEL["dim"]
        d.line([P(26, 70), P(74, 70)], fill=amber, width=max(1, int(4 * u)))
        d.polygon([P(20, 70), P(32, 62), P(32, 78)], fill=amber)
        d.polygon([P(80, 70), P(68, 62), P(68, 78)], fill=amber)
    return img.resize((int(size * scale), int(size * scale)), Image.LANCZOS)
