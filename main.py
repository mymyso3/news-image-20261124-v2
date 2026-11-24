#!/usr/bin/env python3
"""news-image-20261124-v2: one image summing up Tuesday 24 November 2026.

Pure Python 3 standard library. A hand-made 5x7 bitmap font, a small
vector drawing layer, and a hand-rolled PNG encoder. No network, no
clock, no randomness: two runs write byte-identical files.

Layout (1024 x 1024): masthead, four lead stories with drawn pictures,
a schematic world map, a UTC timeline, then the remaining 36 stories
in a dense region-grouped grid, each with a verification mark:
filled dot = confirmed, half dot = reported, ring = claim.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 231)
INK = (26, 26, 26)
INK_SOFT = (74, 74, 66)
RED = (179, 38, 30)
BLUE = (29, 78, 137)
TEAL = (14, 110, 110)
GOLD = (176, 124, 22)
RULE = (26, 26, 26)
CARD = (255, 253, 247)
SHADE = (232, 226, 212)
SEA = (198, 220, 228)
LAND = (214, 196, 158)
LAND2 = (190, 178, 140)

# ---------------------------------------------------------------- font
# 5x7 glyphs, one row per string, '#' = ink. Uppercase only; input is
# upper-cased by the text helpers. Digits and common punctuation included.
GLYPHS = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    '<': ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
}


def glyph(ch):
    return GLYPHS.get(ch, GLYPHS['?'])


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = s.split(' ')
    lines, cur = [], ''
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += ' ' + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c, fill=True):
        if fill:
            for yy in range(y, y + h):
                base = (yy * self.w + x) * 3
                row = bytes(c) * w
                self.px[base:base + 3 * w] = row
        else:
            self.hline(x, y, w, c)
            self.hline(x, y + h - 1, w, c)
            self.vline(x, y, h, c)
            self.vline(x + w - 1, y, h, c)

    def hline(self, x, y, w, c):
        if 0 <= y < self.h:
            x0, x1 = max(0, x), min(self.w, x + w)
            if x1 > x0:
                base = (y * self.w + x0) * 3
                self.px[base:base + 3 * (x1 - x0)] = bytes(c) * (x1 - x0)

    def vline(self, x, y, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            self.put(x, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.put(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.put(xx, yy, c)

    def poly(self, pts, c, fill=True):
        """Scanline polygon fill (or outline when fill=False)."""
        if fill:
            ys = [p[1] for p in pts]
            for y in range(min(ys), max(ys) + 1):
                xs = []
                n = len(pts)
                for i in range(n):
                    x0, y0 = pts[i]
                    x1, y1 = pts[(i + 1) % n]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        t = (y - y0) / (y1 - y0)
                        xs.append(x0 + t * (x1 - x0))
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    self.hline(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, c)
        else:
            n = len(pts)
            for i in range(n):
                self.line(pts[i][0], pts[i][1], pts[(i + 1) % n][0],
                          pts[(i + 1) % n][1], c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = glyph(ch)
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == '1':
                        self.rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_centred(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)


# ---------------------------------------------------------------- png
def png_bytes(cv):
    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', idat) + chunk(b'IEND', b''))

# ---------------------------------------------------------------- stories
# (region, headline, detail, mark)  mark: C = confirmed, R = reported,
# K = claim. Every story was verified against a report dated 24 Nov 2026
# (or first reported that day); see SOURCES.md for the outlet per story.
# Counts: Asia 10, Europe 10, Africa 4, North America 8,
# South America 3, Middle East 2, Oceania 3 = 40 stories, 7 regions.
LEADS = [
    ("ASIA", "CANDY FACTORY FIRE KILLS 24",
     "BANTEN, INDONESIA; ~30 STILL MISSING", "C"),
    ("AFRICA", "UKRAINE SINKS RUSSIAN FRIGATE",
     "SEA DRONES OFF LIBYA, KYIV CLAIMS", "K"),
    ("EUROPE", "EU 22ND SANCTIONS PACKAGE",
     "~60 BANKS OFF SWIFT; 70+ SHIPS LISTED", "C"),
    ("NORTH AMERICA", "DOJ SEEKS $1.1BN CRYPTO FORFEITURE",
     "NK HACKERS' BINANCE THEFT, US SAYS", "C"),
]

STORIES = [
    # Asia (9 more)
    ("ASIA", "TRUMP OFFERS MANILA $2.4BN AID",
     "SELF-DEFENCE PACKAGE, WITH A CATCH", "R"),
    ("ASIA", "CHINA SENTENCES OFFICIAL TO DEATH",
     "SPYING, LEAKING STATE SECRETS", "C"),
    ("ASIA", "PRABOWO NAMES VP PICKS",
     "LOYALIST AND TYCOON'S COUSIN", "R"),
    ("ASIA", "NEPAL PM IN INDIA FOR TALKS",
     "ECONOMY AND ENERGY ON AGENDA", "C"),
    ("ASIA", "THAI COURT UPHOLDS MP VERDICT",
     "OPPOSITION LAWMAKER LOSES APPEAL", "C"),
    ("ASIA", "INDONESIA TREASON CHARGES",
     "6 HELD OVER SPYING ON PRABOWO", "C"),
    ("ASIA", "SEOUL MINISTER QUITS IN AI CHEAT",
     "EXAM SCANDAL HITS ENTRANCE TEST", "C"),
    ("ASIA", "DHAKA VOWS TO ARREST HASINA",
     "IF EX-PM RETURNS FROM INDIA", "R"),
    ("ASIA", "6,000 COPS FOR MANILA STRIKE",
     "2-DAY TRANSPORT STOPPAGE", "C"),
    # Europe (9 more)
    ("EUROPE", "HACKED DATA: 500,000 DEAD",
     "RUSSIAN WAR TOLL NEAR 500,000", "R"),
    ("EUROPE", "RUSSIA MAY LAUNCH SPACE WEAPON",
     "ALLIES WARN OF DECEMBER LAUNCH", "R"),
    ("EUROPE", "GTA VI HACKER FREED",
     "KURTAJ, 21: 7 YEARS, TIME SERVED", "C"),
    ("EUROPE", "UK CONCERT EVACUATED",
     "THOUSANDS OUT, UNKNOWN SUBSTANCE", "C"),
    ("EUROPE", "KYIV REGION STRIKES KILL 14",
     "RUSSIAN ATTACKS, UKRAINE SAYS", "C"),
    ("EUROPE", "MOSCOW WARNS ESTONIA",
     "'VERGE OF OPEN WAR', RUSSIA CLAIMS", "K"),
    ("EUROPE", "BURNHAM: NO EU RETURN W/O VOTE",
     "'UNTHINKABLE' WITHOUT REFERENDUM", "R"),
    ("EUROPE", "MACRON EYES CHARTER CHANGE",
     "TO CURB SPENDING", "R"),
    ("EUROPE", "EURO STOXX JUMPS 2.23%",
     "BROAD EUROPEAN MARKET REBOUND", "C"),
    # Africa (3 more)
    ("AFRICA", "DRONES HIT HOMES, UN SITE IN SUDAN",
     "KHARTOUM STRIKES, STAFF INSIDE", "C"),
    ("AFRICA", "NIGERIA BOAT TOLL RISES TO 29",
     "BAYELSA ACCIDENT, GOVERNOR SAYS", "C"),
    ("AFRICA", "CAS TO RULE ON SENEGAL TROPHY",
     "AFCON APPEAL DECIDED TUESDAY", "R"),
    # North America (7 more)
    ("NORTH AMERICA", "NVIDIA REHIRES HUANG AS CEO",
     "SHARES +31.5%; NASDAQ +6.5%", "C"),
    ("NORTH AMERICA", "TRUMP SLAMS NEWSOM AT DOJ",
     "SPEECH TARGETS CRIME, DEMOCRATS", "C"),
    ("NORTH AMERICA", "TRUMP ORDERS EXECUTIONS SPED UP",
     "FEDERAL DEATH ROW ACCELERATED", "C"),
    ("NORTH AMERICA", "REP. GOMEZ RESIGNS",
     "ETHICS PANEL FOUND MISCONDUCT", "C"),
    ("NORTH AMERICA", "STATES SUE MUSK OVER GROK IMAGES",
     "SEXUALIZED AI PICTURES AT ISSUE", "C"),
    ("NORTH AMERICA", "CANADA PM'S TRUMP IMPERSONATOR",
     "COMIC JOINS PM ON STAGE AT GALA", "C"),
    ("NORTH AMERICA", "US ADDS MEGASPEED TO SANCTIONS",
     "NVIDIA-LINKED CHIPMAKER LISTED", "C"),
    # South America (3)
    ("SOUTH AMERICA", "HEGSETH IN CARACAS FOR DEAL",
     "US-VENEZUELA MILITARY COOPERATION", "R"),
    ("SOUTH AMERICA", "BOVESPA SLIDES BELOW 165,000",
     "DOLLAR TOPS 6 REAIS IN BRAZIL", "C"),
    ("SOUTH AMERICA", "BRAZIL HELD 5 IN COCAINE BUST",
     "660KG SEIZED AFTER PILOT'S CRASH", "C"),
    # Middle East (2)
    ("MIDDLE EAST", "ISRAEL RIVALS CLASH OVER IRAN",
     "COALITION TALKS NEAR, EISENKOT IN", "R"),
    ("MIDDLE EAST", "DUBAI UP 1.30%; CAIRO DOWN 2.85%",
     "SIX GULF MARKETS END LOWER", "C"),
    # Oceania (3)
    ("OCEANIA", "REDDIT FIGHTS UNDER-16 BAN",
     "AUSTRALIA'S BAN CHALLENGED", "C"),
    ("OCEANIA", "HEATWAVE GRIPS CAPE YORK",
     "VANUATU M6.5; NO DAMAGE REPORTED", "C"),
    ("OCEANIA", "AUCKLAND COULD SAVE $17BN",
     "COMPACT GROWTH CUTS ENERGY BILL", "R"),
]

REGION_ORDER = ["ASIA", "EUROPE", "AFRICA", "NORTH AMERICA",
                "SOUTH AMERICA", "MIDDLE EAST", "OCEANIA"]
REGION_COLOUR = {
    "ASIA": RED, "EUROPE": BLUE, "AFRICA": TEAL,
    "NORTH AMERICA": (120, 60, 140), "SOUTH AMERICA": (30, 120, 60),
    "MIDDLE EAST": GOLD, "OCEANIA": (200, 90, 20),
}

# UTC timeline: (approx UTC hour, label). Times are reporting windows,
# not exact event times; the caption on the page says so.
TIMELINE = [
    (1, "MANILA STRIKE"),
    (4, "SEOUL MINISTER QUITS"),
    (7, "INDONESIA FIRE TOLL 24"),
    (9, "EU SANCTIONS PRESENTED"),
    (11, "KYIV STRIKES KILL 14"),
    (14, "FRIGATE SUNK OFF LIBYA"),
    (18, "NVIDIA REHIRES HUANG"),
    (21, "DOJ SEEKS $1.1BN"),
]


# ---------------------------------------------------------------- pictograms
def draw_mark(cv, x, y, mark, r=6):
    """Verification mark: C filled, R half-filled, K ring."""
    if mark == "C":
        cv.circle(x, y, r, INK, fill=True)
    elif mark == "R":
        cv.circle(x, y, r, INK, fill=False)
        for yy in range(y - r + 1, y + r):
            for xx in range(x - r + 1, x + 1):
                if (xx - x) ** 2 + (yy - y) ** 2 <= (r - 1) ** 2:
                    cv.put(xx, yy, INK)
    else:
        cv.circle(x, y, r, INK, fill=False)


def pic_flame(cv, x, y, s, c):
    cv.poly([(x + 4 * s, y + 10 * s), (x + 2 * s, y + 5 * s),
             (x + 5 * s, y + 3 * s), (x + 4 * s, y),
             (x + 7 * s, y + 3 * s), (x + 9 * s, y + 6 * s),
             (x + 7 * s, y + 10 * s)], c)
    cv.poly([(x + 4 * s, y + 10 * s), (x + 5 * s, y + 7 * s),
             (x + 6 * s, y + 10 * s)], GOLD)


def pic_ship(cv, x, y, s, c):
    cv.rect(x, y + 6 * s, 12 * s, 3 * s, c)
    cv.poly([(x, y + 6 * s), (x + 12 * s, y + 6 * s),
             (x + 10 * s, y + 9 * s), (x + 2 * s, y + 9 * s)], c)
    cv.rect(x + 4 * s, y + 3 * s, 4 * s, 3 * s, c)
    cv.line(x + 6 * s, y + 3 * s, x + 6 * s, y, c)
    cv.poly([(x + 6 * s, y), (x + 9 * s, y + 2 * s),
             (x + 6 * s, y + 2 * s)], RED)
    cv.line(x, y + 10 * s, x + 12 * s, y + 10 * s, BLUE)
    cv.line(x + 1 * s, y + 11 * s, x + 11 * s, y + 11 * s, BLUE)


def pic_bank(cv, x, y, s, c):
    cv.poly([(x, y + 3 * s), (x + 6 * s, y), (x + 12 * s, y + 3 * s)], c)
    for i in range(4):
        cv.rect(x + i * 3 * s, y + 4 * s, s, 5 * s, c)
    cv.rect(x, y + 9 * s, 12 * s, s, c)
    cv.rect(x, y + 10 * s, 12 * s, s, c)


def pic_coin(cv, x, y, s, c):
    cv.circle(x + 6 * s, y + 6 * s, 6 * s, c, fill=True)
    cv.circle(x + 6 * s, y + 6 * s, 4 * s, PAPER, fill=True)
    cv.circle(x + 6 * s, y + 6 * s, 4 * s, c, fill=False)
    cv.text(x + 4 * s, y + 3 * s, "$", 1, c)


def pic_chip(cv, x, y, s, c):
    cv.rect(x + 2 * s, y + 2 * s, 8 * s, 8 * s, c)
    cv.rect(x + 4 * s, y + 4 * s, 4 * s, 4 * s, PAPER)
    for i in range(3):
        cv.rect(x + (3 + i * 3) * s, y, s, 2 * s, c)
        cv.rect(x + (3 + i * 3) * s, y + 10 * s, s, 2 * s, c)
        cv.rect(x, y + (3 + i * 3) * s, 2 * s, s, c)
        cv.rect(x + 10 * s, y + (3 + i * 3) * s, 2 * s, s, c)


def pic_satellite(cv, x, y, s, c):
    cv.rect(x + 5 * s, y + 4 * s, 3 * s, 4 * s, c)
    cv.rect(x, y + 5 * s, 4 * s, 2 * s, BLUE)
    cv.rect(x + 9 * s, y + 5 * s, 4 * s, 2 * s, BLUE)
    cv.line(x + 2 * s, y + 2 * s, x + 5 * s, y + 5 * s, c)
    cv.line(x + 10 * s, y + 2 * s, x + 8 * s, y + 4 * s, c)


def pic_gavel(cv, x, y, s, c):
    cv.rect(x + 2 * s, y + 2 * s, 7 * s, 3 * s, c)
    cv.line(x + 5 * s, y + 5 * s, x + 9 * s, y + 9 * s, c)
    cv.rect(x + 8 * s, y + 9 * s, 4 * s, s, c)


def pic_ballot(cv, x, y, s, c):
    cv.rect(x + 2 * s, y + 4 * s, 8 * s, 6 * s, c)
    cv.rect(x + 4 * s, y + 2 * s, 4 * s, 2 * s, c)
    cv.poly([(x + 4 * s, y + 7 * s), (x + 5 * s, y + 8 * s),
             (x + 8 * s, y + 5 * s)], PAPER)


def pic_wave(cv, x, y, s, c):
    for i in range(3):
        yy = y + (2 + i * 3) * s
        for xx in range(12):
            off = 0 if (xx // 3) % 2 == 0 else s
            cv.rect(x + xx * s, yy + off, s, s, c)


def pic_sun(cv, x, y, s, c):
    cv.circle(x + 6 * s, y + 6 * s, 3 * s, c, fill=True)
    for i in range(8):
        ang = i * math.pi / 4
        x0 = int(x + 6 * s + 4 * s * math.cos(ang))
        y0 = int(y + 6 * s + 4 * s * math.sin(ang))
        x1 = int(x + 6 * s + 6 * s * math.cos(ang))
        y1 = int(y + 6 * s + 6 * s * math.sin(ang))
        cv.line(x0, y0, x1, y1, c)


LEAD_PICS = [pic_flame, pic_ship, pic_bank, pic_coin]
REGION_PICS = {"ASIA": pic_flame, "EUROPE": pic_bank, "AFRICA": pic_wave,
               "NORTH AMERICA": pic_chip, "SOUTH AMERICA": pic_ballot,
               "MIDDLE EAST": pic_sun, "OCEANIA": pic_satellite}

# ---------------------------------------------------------------- layout
MARGIN = 20
COL_W = 241
COL_GAP = 4


def draw_masthead(cv):
    cv.hline(MARGIN, 12, W - 2 * MARGIN, INK)
    cv.rect(MARGIN, 16, W - 2 * MARGIN, 2, INK)
    cv.text_centred(W // 2, 26, "THE WORLD IN ONE PAGE", 4, INK)
    cv.text_centred(W // 2, 60, "TUESDAY 24 NOVEMBER 2026", 3, RED)
    cv.text_centred(W // 2, 86, "40 STORIES  -  7 REGIONS  -  ONE PAGE  -  SURGE EDITION",
                    2, INK_SOFT)
    cv.rect(MARGIN, 104, W - 2 * MARGIN, 2, INK)
    cv.hline(MARGIN, 110, W - 2 * MARGIN, INK)


def draw_lead(cv, x, y, w, idx, story):
    region, head, detail, mark = story
    cv.rect(x, y, w, 160, CARD)
    cv.rect(x, y, w, 160, RULE, fill=False)
    # picture band
    cv.rect(x + 1, y + 1, w - 2, 66, SHADE)
    pic = LEAD_PICS[idx]
    pic(cv, x + w // 2 - 30, y + 10, 5, REGION_COLOUR[region])
    cv.text(x + 10, y + 72, region, 1, REGION_COLOUR[region])
    draw_mark(cv, x + w - 16, y + 76, mark, r=5)
    lines = wrap_text(head, 18)
    yy = y + 88
    for ln in lines[:2]:
        cv.text(x + 10, yy, ln, 2, INK)
        yy += 16
    cv.text(x + 10, y + 140, detail, 1, INK_SOFT)


def draw_leads(cv):
    y = 118
    for i, story in enumerate(LEADS):
        x = MARGIN + i * (COL_W + COL_GAP)
        draw_lead(cv, x, y, COL_W, i, story)


def draw_map(cv):
    x0, y0, mw, mh = MARGIN, 282, W - 2 * MARGIN, 100
    cv.rect(x0, y0, mw, mh, SEA)
    cv.rect(x0, y0, mw, mh, RULE, fill=False)
    cv.text(x0 + 8, y0 + 6, "WORLD MAP - WHERE IT HAPPENED", 1, INK_SOFT)

    def P(px, py):
        return (x0 + 8 + int(px * (mw - 16) / 1000.0),
                y0 + 22 + int(py * (mh - 30) / 110.0))

    def land(pts, colour=LAND):
        cv.poly([P(a, b) for a, b in pts], colour)

    # Schematic continents (equirectangular, deliberately simplified).
    land([(40, 8), (300, 6), (330, 30), (290, 62), (210, 78), (120, 82),
          (60, 60), (30, 30)])                                    # N America
    land([(315, 62), (360, 58), (375, 90), (345, 108), (315, 96)])  # S America
    land([(470, 6), (565, 4), (575, 28), (545, 44), (490, 46),
          (465, 28)], LAND2)                                       # Europe
    land([(480, 52), (585, 50), (600, 78), (565, 106), (505, 104),
          (478, 78)])                                              # Africa
    land([(575, 4), (950, 2), (965, 40), (920, 66), (820, 72),
          (700, 70), (600, 48)])                                    # Asia
    land([(880, 84), (960, 82), (965, 102), (895, 106)])            # Oceania
    # Story dots: (map x, map y, region)
    dots = [(835, 58, "ASIA"), (520, 56, "AFRICA"), (505, 22, "EUROPE"),
            (175, 38, "NORTH AMERICA"), (350, 82, "SOUTH AMERICA"),
            (620, 52, "MIDDLE EAST"), (915, 92, "OCEANIA"),
            (890, 40, "ASIA"), (545, 26, "EUROPE"), (250, 55, "NORTH AMERICA")]
    for dx, dy, reg in dots:
        px, py = P(dx, dy)
        cv.circle(px, py, 5, REGION_COLOUR[reg], fill=True)
        cv.circle(px, py, 5, INK, fill=False)
    labels = [(150, 88, "NORTH AMERICA"), (380, 85, "S. AMERICA"),
              (430, 22, "EUROPE"), (520, 108, "AFRICA"),
              (780, 80, "ASIA"), (630, 80, "MIDDLE EAST"),
              (920, 98, "OCEANIA")]
    for lx, ly, lab in labels:
        px, py = P(lx, ly)
        cv.text(px, py, lab, 1, INK)


def draw_timeline(cv):
    x0, y0, tw = MARGIN, 386, W - 2 * MARGIN
    cv.text(x0, y0, "THE DAY IN UTC - REPORTED ORDER", 2, INK)
    cv.text(x0, y0 + 18, "TIMES ARE APPROXIMATE REPORTING WINDOWS, NOT EVENT TIMES",
            1, INK_SOFT)
    bar_y = y0 + 36
    cv.rect(x0, bar_y, tw, 3, INK)
    for h in range(0, 25, 4):
        hx = x0 + int(h * tw / 24.0)
        cv.vline(hx, bar_y - 4, 11, INK)
        lx = max(x0, min(x0 + tw - 30, hx - 8))
        cv.text(lx, bar_y + 10, "%02d:00" % h, 1, INK_SOFT)
    for i, (hour, label) in enumerate(TIMELINE):
        hx = x0 + int(hour * tw / 24.0)
        cv.circle(hx, bar_y + 1, 5, RED, fill=True)
        cv.circle(hx, bar_y + 1, 5, INK, fill=False)
        lw = text_width(label, 1)
        lx = hx - lw // 2
        lx = max(x0, min(x0 + tw - lw, lx))
        ly = bar_y + 24 if i % 2 == 0 else bar_y + 38
        cv.text(lx, ly, label, 1, INK)
    cv.hline(x0, y0 + 88, tw, RULE)


def draw_grid(cv):
    y = 490
    by_region = {r: [] for r in REGION_ORDER}
    for s in STORIES:
        by_region[s[0]].append(s)
    # 4 columns x 9 rows; stories flow region by region, column by column.
    ordered = []
    for r in REGION_ORDER:
        ordered.extend(by_region[r])
    assert len(ordered) == 36, len(ordered)
    row_h, rows = 52, 9
    for i, story in enumerate(ordered):
        col, row = i % 4, i // 4
        x = MARGIN + col * (COL_W + COL_GAP)
        yy = y + row * (row_h + 2)
        region, head, detail, mark = story
        cv.rect(x, yy, COL_W, row_h, CARD)
        cv.rect(x, yy, COL_W, row_h, RULE, fill=False)
        cv.rect(x, yy, 4, row_h, REGION_COLOUR[region])
        num = "%02d" % (i + 5)
        cv.text(x + 10, yy + 4, num, 1, REGION_COLOUR[region])
        draw_mark(cv, x + COL_W - 12, yy + 8, mark, r=4)
        lines = wrap_text(head, 18)
        ly = yy + 12
        for ln in lines[:2]:
            cv.text(x + 10, ly, ln, 2, INK)
            ly += 16
        cv.text(x + 10, yy + row_h - 8, detail, 1, INK_SOFT)


def draw_footer(cv):
    y = 990
    cv.hline(MARGIN, y - 8, W - 2 * MARGIN, RULE)
    cv.text(MARGIN, y + 2, "KEY: (DOT) CONFIRMED  (HALF) REPORTED  (RING) CLAIM  -  "
            "ALL STORIES FIRST REPORTED 24 NOV 2026 - SEE SOURCES.MD", 1, INK_SOFT)


def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_leads(cv)
    draw_map(cv)
    draw_timeline(cv)
    draw_grid(cv)
    draw_footer(cv)
    return cv


def main():
    outdir = os.environ.get("OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
