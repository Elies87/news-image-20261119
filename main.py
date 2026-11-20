#!/usr/bin/env python3
"""One page of world news: Thursday 19 November 2026.

Entry for the make.fun bounty "news-image-20261119" - sum up the day's
world news in a single image.  The page below is a newspaper front sheet:
a lead story, a world-court band, four panels, two mini stories and a
ticker, all painted with drawing primitives on a supersampled canvas and
then reduced to the final 1024x1024 PNG.

Standard library only.  The grading sandbox is offline and runs stock
Python 3.13, so the news is frozen into this file as data, the pictures
are drawn rather than loaded, and the PNG is encoded by hand with zlib.
No clock, no randomness, no network: repeated runs are byte-identical.
"""

import os
import struct
import zlib
from math import cos, pi, radians, sin

# ---------------------------------------------------------------------------
# The day's news, frozen as data (researched from 19 November 2026
# reporting; the source list lives in berita.md).  Multi-line fields are
# stored as one string with "|" between the printed lines.
# ---------------------------------------------------------------------------

PAPER_TITLE = "THE DAILY WORLD"
TOP_KICKER = "ONE PAGE · ONE DAY · THE WHOLE WORLD"
DATE_LINE = "THURSDAY · 19 NOVEMBER 2026"
FOOTER_LINE = "THURSDAY 19 NOVEMBER 2026 - THE DAY'S WORLD NEWS IN ONE IMAGE"

LEAD_KICKER = "SHENZHEN · APEC SUMMIT - GEOPOLITICS"
LEAD_HEAD = "TRUMP, XI & PUTIN|MEET FACE TO FACE"
LEAD_BODY = ("THE US, CHINESE AND RUSSIAN LEADERS SAT DOWN|"
             "TOGETHER FOR THE FIRST TIME IN HISTORY AT THE|"
             "APEC SUMMIT. CHINA AND RUSSIA ISSUED A JOINT|"
             "PEACE DECLARATION; UKRAINE WAS DISCUSSED.")
LEAD_CAPTION = "USA · CHINA · RUSSIA"

COURT_KICKER = "THE HAGUE · WORLD COURT - LAW & RIGHTS"
COURT_HEAD = "MYANMAR COMMITTED GENOCIDE|AGAINST THE ROHINGYA - ICJ"
COURT_BODY = ("FIRST TIME THE WORLD COURT HAS HELD A STATE RESPONSIBLE FOR|"
              "GENOCIDE. THE CASE WAS BROUGHT BY THE GAMBIA; REPARATIONS DUE.")

# (kicker, headline, body, icon) for the four panels, row by row.
PANELS = [
    ("BUSINESS · NASDAQ",
     "ANTHROPIC IPO IS|LARGEST IN HISTORY",
     "AI FIRM RAISES $81BN AT $83|A SHARE; DEBUT CLOSES AT|$97.17, UP 17% ON DAY ONE",
     "chart"),
    ("INDIA · CYCLONE AKVAN",
     "105,000 EVACUATED|AS CYCLONE NEARS",
     "ODISHA EMPTIES ITS COAST AS|AKVAN HEADS FOR A FRIDAY|LANDFALL NEAR GOPALPUR",
     "cyclone"),
    ("DEEP SPACE · NASA",
     "VOYAGER 1 NOW ONE|LIGHT-DAY AWAY",
     "NASA CONFIRMS THE SIGNAL:|VOYAGER'S CALL NOW TAKES|A FULL DAY TO ARRIVE",
     "probe"),
    ("AFRICA · SOMALIA",
     "SOMALIA EXPELS|UAE AMBASSADOR",
     "ENVOY GIVEN 72 HOURS TO|LEAVE OVER SOVEREIGNTY|ROW; OWN ENVOY RECALLED",
     "envoy"),
]

MINIS = [
    "SENEGAL - DOZENS MISSING AS|MIGRANT BOAT CAPSIZES AT SEA",
    "SEOUL - COURT OVERTURNS EX-PM|HAN'S 15-YEAR JAIL SENTENCE",
]

TICKER = [
    "ALSO TODAY: NETHERLANDS SUMMONS RUSSIAN ENVOY AFTER KYIV EMBASSY HIT",
    "MONGOLIA PRESIDENT RESIGNS · CEPU REFINERY BLAST KILLS ONE WORKER",
]

# ---------------------------------------------------------------------------
# Typeface: a 5x7 bitmap font.  Each glyph is seven row masks, one integer
# per row, bit 4 being the leftmost pixel of the row.
# ---------------------------------------------------------------------------

GLYPHS = {
    "A": (14, 17, 17, 31, 17, 17, 17), "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (15, 16, 16, 16, 16, 16, 15), "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31), "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (15, 16, 16, 23, 17, 17, 14), "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (31, 4, 4, 4, 4, 4, 31),      "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17), "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17), "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14), "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13), "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),   "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14), "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17), "X": (17, 10, 4, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),     "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 19, 21, 25, 17, 17, 14), "1": (4, 12, 4, 4, 4, 4, 31),
    "2": (14, 17, 1, 6, 8, 16, 31),    "3": (14, 17, 1, 6, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),     "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (14, 16, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 4, 4, 4),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 17, 14),
    " ": (0, 0, 0, 0, 0, 0, 0),        ".": (0, 0, 0, 0, 0, 0, 4),
    ",": (0, 0, 0, 0, 0, 4, 8),        "'": (4, 4, 0, 0, 0, 0, 0),
    "-": (0, 0, 0, 31, 0, 0, 0),       "&": (12, 18, 20, 8, 21, 18, 13),
    ":": (0, 4, 0, 0, 0, 4, 0),        ";": (0, 4, 0, 0, 0, 4, 8),
    "!": (4, 4, 4, 4, 4, 0, 4),        "?": (14, 17, 1, 2, 4, 0, 4),
    "/": (1, 1, 2, 4, 8, 16, 16),      "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),        "%": (25, 26, 1, 2, 4, 8, 19),
    "$": (4, 15, 20, 14, 5, 30, 4),    "·": (0, 0, 0, 4, 0, 0, 0),
}
BLANK_GLYPH = GLYPHS[" "]

# ---------------------------------------------------------------------------
# Canvas and painting primitives.  The page is designed at 1024x1024 and
# painted at twice that size; a box average at the end softens the art.
# ---------------------------------------------------------------------------

ZOOM = 2
EDGE = 1024
BIG = EDGE * ZOOM
canvas = bytearray(BIG * BIG * 3)

PAPER = (246, 241, 230)
INK = (22, 24, 28)
RED = (176, 36, 30)
NAVY = (28, 59, 100)
TEAL = (14, 106, 110)
GOLD = (178, 126, 18)
GREY = (98, 104, 114)
PANEL_BG = (240, 234, 217)
COURT_BG = (232, 236, 240)
WHITE = (255, 255, 255)
SKY = (213, 226, 239)


def rect(x, y, w, h, colour):
    """Solid rectangle; arguments are design units, floats allowed."""
    x0 = max(0, int(x * ZOOM))
    y0 = max(0, int(y * ZOOM))
    x1 = min(BIG, int((x + w) * ZOOM))
    y1 = min(BIG, int((y + h) * ZOOM))
    if x1 <= x0 or y1 <= y0:
        return
    stripe = bytes(colour) * (x1 - x0)
    for row in range(y0, y1):
        at = (row * BIG + x0) * 3
        canvas[at:at + len(stripe)] = stripe


def dot(x, y, colour):
    """One canvas pixel, clipped to the canvas."""
    if 0 <= x < BIG and 0 <= y < BIG:
        at = (y * BIG + x) * 3
        canvas[at:at + 3] = bytes(colour)


def circle(cx, cy, r, colour):
    """Filled circle by a bounding-box distance test."""
    ccx, ccy, rr = cx * ZOOM, cy * ZOOM, r * ZOOM
    r2 = rr * rr
    for py in range(int(ccy - rr), int(ccy + rr) + 1):
        dy = py - ccy
        for px in range(int(ccx - rr), int(ccx + rr) + 1):
            dx = px - ccx
            if dx * dx + dy * dy <= r2:
                dot(px, py, colour)


def seg(x0, y0, x1, y1, thick, colour):
    """A thick straight stroke, stamped as squares along its length."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * ZOOM) + 1
    t = 0.0
    while t <= 1.0:
        rect(x0 + (x1 - x0) * t - thick / 2.0,
             y0 + (y1 - y0) * t - thick / 2.0, thick, thick, colour)
        t += 1.0 / steps


def poly(points, colour):
    """Filled polygon, scanline by scanline, in design units."""
    pts = [(px * ZOOM, py * ZOOM) for px, py in points]
    top = max(0, int(min(p[1] for p in pts)))
    bottom = min(BIG - 1, int(max(p[1] for p in pts)))
    edges = list(zip(pts, pts[1:] + pts[:1]))
    for row in range(top, bottom + 1):
        hits = []
        for (ax, ay), (bx, by) in edges:
            if (ay <= row < by) or (by <= row < ay):
                hits.append(ax + (row - ay) * (bx - ax) / (by - ay))
        hits.sort()
        for k in range(0, len(hits) - 1, 2):
            xa = max(0, int(hits[k]))
            xb = min(BIG - 1, int(hits[k + 1]))
            stripe = bytes(colour) * (xb - xa + 1)
            at = (row * BIG + xa) * 3
            canvas[at:at + len(stripe)] = stripe


def star(cx, cy, r, colour):
    ring = []
    for i in range(10):
        ang = -pi / 2 + i * pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        ring.append((cx + rad * cos(ang), cy + rad * sin(ang)))
    poly(ring, colour)


def line_width(text, scale):
    return len(text) * 6 * scale


def put_text(x, y, text, scale, colour, bold=False, centre_in=None):
    """One printed line; glyphs are 5 wide on a 6-unit advance, y is top."""
    if centre_in is not None:
        lo, hi = centre_in
        x = lo + (hi - lo - line_width(text, scale)) // 2
    pen = x
    for ch in text:
        rows = GLYPHS.get(ch, BLANK_GLYPH)
        for gy in range(7):
            mask = rows[gy]
            for gx in range(5):
                if mask & (1 << (4 - gx)):
                    rect(pen + gx * scale, y + gy * scale, scale, scale, colour)
                    if bold:
                        rect(pen + gx * scale + scale, y + gy * scale,
                             scale, scale, colour)
        pen += 6 * scale


def put_lines(x, y, packed, scale, colour, leading, bold=False):
    """Print a "|"-packed field line by line; returns the next free y."""
    for line in packed.split("|"):
        put_text(x, y, line, scale, colour, bold=bold)
        y += 7 * scale + leading
    return y


# ---------------------------------------------------------------------------
# Pictures.  Everything is drawn from the primitives above; no photos.
# ---------------------------------------------------------------------------

def flag_usa(x, y, w, h):
    rect(x, y, w, h, WHITE)
    stripe = h / 13.0
    for i in range(0, 13, 2):
        rect(x, y + i * stripe, w, stripe + 0.6, (176, 34, 44))
    rect(x, y, w * 0.44, stripe * 7, NAVY)
    for r in range(3):
        for c in range(4):
            circle(x + 8 + c * (w * 0.44 - 14) / 3.0,
                   y + 8 + r * (stripe * 7 - 16) / 2.0, 2.2, WHITE)


def flag_china(x, y, w, h):
    rect(x, y, w, h, (222, 41, 16))
    star(x + w * 0.22, y + h * 0.28, h * 0.20, (255, 222, 0))
    for fx, fy in ((0.42, 0.14), (0.47, 0.30), (0.47, 0.47), (0.42, 0.62)):
        circle(x + w * fx, y + h * fy, 3.0, (255, 222, 0))


def flag_russia(x, y, w, h):
    rect(x, y, w, h / 3.0 + 0.6, WHITE)
    rect(x, y + h / 3.0, w, h / 3.0 + 0.6, (0, 57, 166))
    rect(x, y + 2 * h / 3.0, w, h / 3.0 + 0.6, (213, 43, 30))


def summit_art(x, y, w, h):
    """Three flags on poles above a conference table, under a small sun."""
    rect(x, y, w, h, SKY)
    circle(x + w * 0.84, y + h * 0.20, 19, (245, 205, 92))
    fw, fh = 104, 64
    gap = (w - 3 * fw) / 4.0
    fy = y + 32
    for i, painter in enumerate((flag_usa, flag_china, flag_russia)):
        fx = x + gap + i * (fw + gap)
        seg(fx + fw / 2, fy - 13, fx + fw / 2, y + h - 50, 3, INK)
        painter(fx, fy, fw, fh)
        circle(fx + fw / 2, fy - 16, 4, GOLD)
    table_y = y + h - 46
    rect(x + 24, table_y, w - 48, 10, NAVY)
    rect(x + 38, table_y + 10, w - 76, 6, INK)
    for i in range(3):
        circle(x + gap + i * (fw + gap) + fw / 2, table_y - 12, 9, INK)
    put_text(x, y + h - 27, LEAD_CAPTION, 2, INK, centre_in=(x, x + w))


def scales_art(x, y, s):
    """The scales of justice, centred in a square of side s."""
    cx = x + s / 2.0
    seg(cx, y + 10, cx, y + s - 20, 4, NAVY)
    seg(x + 12, y + 18, x + s - 12, y + 18, 4, NAVY)
    circle(cx, y + 12, 5, NAVY)
    for px in (x + 16, x + s - 16):
        seg(px, y + 18, px - 10, y + 44, 2, NAVY)
        seg(px, y + 18, px + 10, y + 44, 2, NAVY)
        for t in range(9):
            wd = 22 - abs(t - 4) * 1.2
            rect(px - wd / 2, y + 42 + t * 0.9, wd, 1.6, NAVY)
    rect(cx - 16, y + s - 18, 32, 5, NAVY)
    rect(cx - 10, y + s - 24, 20, 6, NAVY)


def art_chart(x, y):
    base = y + 62
    heights = (18, 30, 44, 60)
    for i, bh in enumerate(heights):
        rect(x + 4 + i * 18, base - bh, 13, bh, TEAL if i < 3 else GOLD)
    seg(x + 2, base - 14, x + 64, base - 60, 3, RED)
    poly([(x + 66, y + 2), (x + 56, y + 5), (x + 64, y + 13)], RED)
    rect(x, base + 3, 74, 3, INK)


def art_cyclone(x, y):
    cx, cy = x + 37, y + 32
    for i in range(150):
        f = i / 150.0
        ang = f * 4.6 * pi
        r = 4 + f * 27
        circle(cx + r * cos(ang), cy + r * sin(ang) * 0.82, 2.6, TEAL)
    circle(cx, cy, 4, NAVY)
    for rx in (8, 26, 44, 60):
        seg(x + rx, y + 66, x + rx - 5, y + 76, 2.4, NAVY)


def art_probe(x, y):
    circle(x + 24, y + 22, 15, NAVY)
    circle(x + 28, y + 22, 12, SKY)
    rect(x + 30, y + 30, 26, 5, INK)
    seg(x + 44, y + 33, x + 70, y + 58, 3, INK)
    rect(x + 66, y + 54, 9, 9, GOLD)
    seg(x + 36, y + 34, x + 20, y + 56, 2, INK)
    for sx, sy in ((58, 8), (68, 20), (52, 30), (72, 40)):
        circle(x + sx, y + sy, 1.8, GOLD)
    for r in (22, 30):
        for a in range(200, 261, 10):
            circle(x + 24 + r * cos(radians(a)) * 0.6,
                   y + 22 + r * sin(radians(a)) * 0.6, 1.6, TEAL)


def art_envoy(x, y):
    """A sealed letter stamped with a red cross: an envoy sent home."""
    rect(x + 4, y + 14, 66, 44, WHITE)
    rect(x + 4, y + 14, 66, 3, INK)
    rect(x + 4, y + 55, 66, 3, INK)
    rect(x + 4, y + 14, 3, 44, INK)
    rect(x + 67, y + 14, 3, 44, INK)
    seg(x + 7, y + 17, x + 37, y + 38, 2.4, GREY)
    seg(x + 67, y + 17, x + 37, y + 38, 2.4, GREY)
    seg(x + 52, y + 44, x + 66, y + 58, 4, RED)
    seg(x + 66, y + 44, x + 52, y + 58, 4, RED)
    put_text(x + 2, y + 64, "72 HRS", 1, RED)


ART = {"chart": art_chart, "cyclone": art_cyclone,
       "probe": art_probe, "envoy": art_envoy}

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

MARGIN = 30
CONTENT = EDGE - 2 * MARGIN


def compose_page():
    rect(0, 0, EDGE, EDGE, PAPER)

    # masthead
    put_text(MARGIN, 22, TOP_KICKER, 2, GREY, centre_in=(0, EDGE))
    put_text(MARGIN, 44, PAPER_TITLE, 10, INK, centre_in=(0, EDGE))
    rect(MARGIN, 122, CONTENT, 5, RED)
    rect(MARGIN, 131, CONTENT, 2, INK)
    rect(0, 142, EDGE, 54, INK)
    put_text(MARGIN, 154, DATE_LINE, 5, PAPER, centre_in=(0, EDGE))

    # lead story
    ly = 212
    put_text(MARGIN, ly, LEAD_KICKER, 2, RED, bold=True)
    put_lines(MARGIN, ly + 22, LEAD_HEAD, 5, INK, 8)
    put_lines(MARGIN, ly + 118, LEAD_BODY, 2, INK, 5)
    summit_art(618, ly, 376, 200)
    rect(MARGIN, 424, CONTENT, 2, INK)

    # world court band
    cy = 432
    rect(MARGIN, cy, CONTENT, 150, COURT_BG)
    rect(MARGIN, cy, CONTENT, 3, NAVY)
    scales_art(MARGIN + 14, cy + 25, 100)
    tx = MARGIN + 140
    put_text(tx, cy + 14, COURT_KICKER, 2, NAVY, bold=True)
    put_lines(tx, cy + 36, COURT_HEAD, 4, INK, 6)
    put_lines(tx, cy + 104, COURT_BODY, 2, INK, 5)
    rect(MARGIN, 590, CONTENT, 2, INK)

    # four panels in a 2x2 grid
    grid_y, cell_h = 598, 140
    cell_w = (CONTENT - 20) // 2
    stripes = (RED, TEAL, NAVY, GOLD)
    for idx, (kicker, head, body, icon) in enumerate(PANELS):
        row, col = divmod(idx, 2)
        x = MARGIN + col * (cell_w + 20)
        y = grid_y + row * (cell_h + 10)
        rect(x, y, cell_w, cell_h, PANEL_BG)
        rect(x, y, cell_w, 4, stripes[idx])
        ART[icon](x + cell_w - 86, y + 30)
        put_text(x + 14, y + 10, kicker, 2, GREY, bold=True)
        put_lines(x + 14, y + 28, head, 3, INK, 5)
        put_lines(x + 14, y + 84, body, 2, INK, 3)

    # two mini stories
    mini_y = 900
    for i, packed in enumerate(MINIS):
        x = MARGIN + i * (cell_w + 20)
        rect(x, mini_y + 3, 12, 12, RED)
        put_lines(x + 22, mini_y, packed, 2, INK, 4, bold=True)

    # ticker
    tick_y = 942
    rect(MARGIN, tick_y, CONTENT, 2, INK)
    put_text(MARGIN, tick_y + 8, TICKER[0], 2, INK, centre_in=(0, EDGE))
    put_text(MARGIN, tick_y + 26, TICKER[1], 2, INK, centre_in=(0, EDGE))

    # footer
    foot_y = 988
    rect(MARGIN, foot_y, CONTENT, 3, RED)
    put_text(MARGIN, foot_y + 7, FOOTER_LINE, 2, GREY, centre_in=(0, EDGE))


# ---------------------------------------------------------------------------
# Reduction and PNG encoding.  Fixed filter and compression level, so the
# emitted bytes are a pure function of the canvas.
# ---------------------------------------------------------------------------

def reduce_canvas():
    out = bytearray(EDGE * EDGE * 3)
    for yy in range(EDGE):
        for xx in range(EDGE):
            acc = [0, 0, 0]
            for dy in range(ZOOM):
                base = ((yy * ZOOM + dy) * BIG + xx * ZOOM) * 3
                for dx in range(ZOOM):
                    at = base + dx * 3
                    acc[0] += canvas[at]
                    acc[1] += canvas[at + 1]
                    acc[2] += canvas[at + 2]
            at = (yy * EDGE + xx) * 3
            out[at] = acc[0] // 4
            out[at + 1] = acc[1] // 4
            out[at + 2] = acc[2] // 4
    return out


def encode_png(pixels):
    stride = EDGE * 3
    rows = []
    for yy in range(EDGE):
        rows.append(b"\x00" + bytes(pixels[yy * stride:(yy + 1) * stride]))
    raw = b"".join(rows)

    def chunk(tag, payload):
        body = tag + payload
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", EDGE, EDGE, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def run():
    compose_page()
    png = encode_png(reduce_canvas())
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("entry.png written: %d bytes (%dx%d)" % (len(png), EDGE, EDGE))


if __name__ == "__main__":
    run()
