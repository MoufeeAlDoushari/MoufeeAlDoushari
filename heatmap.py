# -*- coding: utf-8 -*-
"""
Builds the contribution strip that sits under the profile card:

    heatmap-dark.svg   -> shown when GitHub is in dark mode
    heatmap-light.svg  -> shown when GitHub is in light mode

Geometry and styling follow the reference strip exactly: a 513x170 viewBox,
a flat background with no card or border, 34 weeks of 11px cells on a 14px
pitch, GitHub's light-green level palette (so empty days read near-white and
active days read green), and no text anywhere.

A jet flies the lane below the grid; every active day flashes bright green as
it passes, going out and coming back, and the busiest days take a shot.

    python heatmap.py

No API token needed - the calendar HTML is public.
"""
import io
import os
import re
import urllib.request

USER = "MoufeeAlDoushari"
URL = "https://github.com/users/%s/contributions" % USER

W, H = 513, 170
CELL, PITCH = 11, 14
GX, GY = 20, 15                     # grid origin
COLS, DAYS = 34, 7                  # the strip shows the most recent 34 weeks
LOOP = 20.0                         # seconds for one jet round trip
JET_Y = 140
JET_X0, JET_X1 = 35, 478
SHOTS = 8                           # how many days the jet actually targets

# GitHub's light-green ramp, used on both themes - that is what gives the
# near-white empty cell and the green activation.
LEVELS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
FLASH = "#39d353"
RING = "#56d364"

THEMES = {
    "dark":  dict(bg="#0d1117", dot="#8b949e"),
    "light": dict(bg="#ffffff", dot="#57606a"),
}

# blinking specks, exactly where the reference puts them
DOTS = [(8, 20, 1.2), (8, 60, 1.6), (8, 100, 2.0),
        (505, 25, 1.2), (505, 70, 1.6), (505, 110, 2.0),
        (30, 164, 1.2), (483, 164, 1.6)]


# ------------------------------------------------------------------ data
def fetch_calendar():
    """[(row, col, date, level, count)] straight off the public profile page."""
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-heatmap"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")

    counts = {}
    for tip in re.findall(r"<tool-tip[^>]*>[^<]*</tool-tip>", html):
        ref = re.search(r'for="(contribution-day-component-\d+-\d+)"', tip)
        num = re.search(r">\s*(\d[\d,]*) contribution", tip)
        if ref:
            counts[ref.group(1)] = int(num.group(1).replace(",", "")) if num else 0

    cells = []
    for td in re.findall(r"<td[^>]*class=\"ContributionCalendar-day\"[^>]*>", html):
        cid = re.search(r'id="(contribution-day-component-(\d+)-(\d+))"', td)
        date = re.search(r'data-date="([\d-]+)"', td)
        lvl = re.search(r'data-level="(\d+)"', td)
        if not (cid and date and lvl):
            continue
        cells.append((int(cid.group(2)), int(cid.group(3)), date.group(1),
                      int(lvl.group(1)), counts.get(cid.group(1), 0)))
    if not cells:
        raise SystemExit("could not parse the contribution calendar")
    return cells


def kt(t):
    return round(max(0.0, min(1.0, t)), 5)


# ----------------------------------------------------------------- build
def build(theme, cells):
    T = THEMES[theme]
    o = io.StringIO()
    w = o.write

    col0 = max(c[1] for c in cells) - (COLS - 1)

    def cx(col):
        return GX + (col - col0) * PITCH

    def cy(row):
        return GY + row * PITCH

    # fraction of the loop at which the jet passes a column on the way out;
    # it passes again, in reverse, at 1 - that
    def col_time(col):
        return 0.04 + ((col - col0) / float(COLS - 1)) * 0.44

    active = [c for c in cells if c[3] > 0 and c[1] >= col0]
    targets = sorted(active, key=lambda c: (-c[3], c[1]))[:SHOTS]
    targets.sort(key=lambda c: c[1])

    w('<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">\n' % (W, H))
    w('<defs><pattern id="q" patternUnits="userSpaceOnUse" x="%d" y="%d" '
      'width="%d" height="%d"><rect width="%d" height="%d" rx="2" ry="2" '
      'fill="%s"/></pattern></defs>\n'
      % (GX, GY, PITCH, PITCH, CELL, CELL, LEVELS[0]))
    w('<rect x="0" y="0" width="%d" height="%d" fill="%s"/>\n' % (W, H, T["bg"]))

    for x, y, dur in DOTS:
        w('<circle cx="%d" cy="%d" r="1.1" fill="%s">'
          '<animate attributeName="opacity" values="0.2;1;0.2" dur="%ss" '
          'repeatCount="indefinite"/></circle>\n' % (x, y, T["dot"], dur))

    # ---- grid: the quiet days are a plain lattice, so one pattern covers them
    w('<g id="grid">\n')
    w('<rect x="%d" y="%d" width="%d" height="%d" fill="url(#q)"/>\n'
      % (GX, GY, COLS * PITCH, DAYS * PITCH))
    present = set((r, c) for r, c, _d, _l, _n in cells if c >= col0)
    for col in range(col0, col0 + COLS):
        for row in range(DAYS):
            if (row, col) not in present:      # days that have not happened yet
                w('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>\n'
                  % (cx(col), cy(row), CELL, CELL, T["bg"]))

    for row, col, _date, lvl, _n in cells:
        if col < col0 or lvl == 0:
            continue
        base = LEVELS[lvl]
        t = col_time(col)
        w('<rect x="%d" y="%d" width="%d" height="%d" rx="2" ry="2" fill="%s">'
          '<animate attributeName="fill" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;%s;%s;1" values="%s;%s;%s;%s;%s;%s"/></rect>\n'
          % (cx(col), cy(row), CELL, CELL, base, LOOP,
             kt(t), kt(t + 0.006), kt(1 - t - 0.006), kt(1 - t),
             base, base, FLASH, base, FLASH, base))
    w('</g>\n')

    # ---- bullets
    w('<g id="bullets">\n')
    for row, col, _date, _lvl, _n in targets:
        x, y = cx(col) + CELL / 2.0, cy(row) + CELL / 2.0
        hit = col_time(col)
        fire = max(0.004, hit - 0.022)
        w('<circle r="1.5" fill="%s" opacity="0">'
          '<animate attributeName="opacity" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;%s;1" values="0;1;1;0;0"/>'
          '<animate attributeName="cx" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="%.1f;%.1f;%.1f;%.1f"/>'
          '<animate attributeName="cy" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="%d;%d;%.1f;%.1f"/></circle>\n'
          % (RING, LOOP, kt(fire), kt(fire + 0.002), kt(hit),
             LOOP, kt(fire), kt(hit), x, x, x, x,
             LOOP, kt(fire), kt(hit), JET_Y, JET_Y, y, y))
    w('</g>\n')

    # ---- blast rings
    w('<g id="blasts">\n')
    for row, col, _date, _lvl, _n in targets:
        x, y = cx(col) + CELL / 2.0, cy(row) + CELL / 2.0
        hit = col_time(col)
        w('<circle cx="%.1f" cy="%.1f" r="0" fill="none" stroke="%s" '
          'stroke-width="1.6" opacity="0">'
          '<animate attributeName="r" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="0;1;9;9"/>'
          '<animate attributeName="opacity" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="0;1;0;0"/></circle>\n'
          % (x, y, RING, LOOP, kt(hit), kt(hit + 0.018),
             LOOP, kt(hit), kt(hit + 0.018)))
    w('</g>\n')

    # ---- the jet
    w('<g id="jet">\n  <g transform="translate(0,0)">\n'
      '    <polygon points="0,-16 8,6 4,3 -4,3 -8,6" fill="#58a6ff" '
      'stroke="#1f6feb" stroke-width="1"/>\n'
      '    <polygon points="-8,6 -14,12 -4,7" fill="#388bfd"/>\n'
      '    <polygon points="8,6 14,12 4,7" fill="#388bfd"/>\n'
      '    <circle cx="0" cy="-6" r="2.2" fill="#c9e6ff"/>\n'
      '    <polygon points="-3,7 3,7 0,15" fill="#f0883e">\n'
      '      <animate attributeName="opacity" values="0.5;1;0.6;1" dur="0.18s" '
      'repeatCount="indefinite"/>\n    </polygon>\n  </g>\n'
      '  <animateTransform attributeName="transform" attributeType="XML" '
      'type="translate"\n    dur="%ss" repeatCount="indefinite"\n'
      '    keyTimes="0;0.5;1"\n'
      '    values="%d,%d;%d,%d;%d,%d"/>\n</g>\n'
      % (LOOP, JET_X0, JET_Y, JET_X1, JET_Y, JET_X0, JET_Y))

    w('</svg>\n')
    return o.getvalue()


def main():
    cells = fetch_calendar()
    print("parsed %d days, %d contributions"
          % (len(cells), sum(c[4] for c in cells)))
    for theme in ("dark", "light"):
        path = "heatmap-%s.svg" % theme
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(theme, cells))
        print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
