# -*- coding: utf-8 -*-
"""
Builds the contribution heatmap strip that sits under the profile card:

    heatmap-dark.svg   -> shown when GitHub is in dark mode
    heatmap-light.svg  -> shown when GitHub is in light mode

Reads the real contribution calendar from the public profile page, paints it
with GitHub's own level palette, then animates it: a wave sweeps left to
right lighting every active day bright green, and a jet flies the lane below
the grid, firing at the busiest days and setting off blast rings.

    python heatmap.py

No API token needed - the calendar HTML is public. Re-run it (or let the
daily workflow run it) to refresh the grid.
"""
import io
import os
import re
import urllib.request

USER = "MoufeeAlDoushari"
URL = "https://github.com/users/%s/contributions" % USER

W, H = 1180, 290
CARD = (16, 16, 1148, 258, 18)
CELL, PITCH = 15.0, 19.6
GX, GY = 72.0, 92.0                 # grid origin
COLS, DAYS = 53, 7
LOOP = 20.0                         # seconds for one jet round trip
JET_Y = 250.0
SHOTS = 10                          # how many cells the jet actually targets

THEMES = {
    "dark": dict(
        bg="#050816", panel="#0B1120", border="#FFFFFF", border_op=".08",
        text="#E5E7EB", muted="#64748B", label="#7DD3FC",
        levels=["#1C2536", "#0E4429", "#006D32", "#26A641", "#39D353"],
        flash="#7EE787", ring="#56D364", empty_ring="#1E293B",
        jet="#58A6FF", jet2="#388BFD", jet3="#C9E6FF", flame="#F0883E",
        dot="#8B949E",
    ),
    "light": dict(
        bg="#FFFFFF", panel="#F8FAFC", border="#0F172A", border_op=".10",
        text="#0F172A", muted="#475569", label="#0284C7",
        levels=["#E4E8EE", "#9BE9A8", "#40C463", "#30A14E", "#216E39"],
        flash="#39D353", ring="#16A34A", empty_ring="#E2E8F0",
        jet="#1F6FEB", jet2="#3B82F6", jet3="#1E3A8A", flame="#EA580C",
        dot="#94A3B8",
    ),
}

MONO = ("ui-monospace,SFMono-Regular,Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ------------------------------------------------------------------ data
def fetch_calendar():
    """[(row, col, date, level, count)] straight off the public profile page."""
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-heatmap"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")

    # the real per-day counts only live in the screen-reader tooltips
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


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kt(t):
    return round(max(0.0, min(1.0, t / LOOP)), 5)


# ----------------------------------------------------------------- build
def build(theme, cells, total):
    T = THEMES[theme]
    o = io.StringIO()
    w = o.write
    bd = 'stroke="%s" stroke-opacity="%s"' % (T["border"], T["border_op"])

    maxcol = max(c[1] for c in cells)
    col0 = maxcol - (COLS - 1)          # keep the most recent 53 weeks

    def cx(col):
        return GX + (col - col0) * PITCH

    def cy(row):
        return GY + row * PITCH

    # When the sweep reaches a given column (jet flies out over the first half)
    def col_time(col):
        return 0.6 + ((col - col0) / float(COLS - 1)) * (LOOP * 0.5 - 1.2)

    active = [c for c in cells if c[3] > 0 and c[1] >= col0]
    # the jet only shoots at the busiest days, otherwise it is noise
    targets = sorted(active, key=lambda c: (-c[3], c[1]))[:SHOTS]
    targets.sort(key=lambda c: c[1])

    w('<?xml version="1.0" encoding="UTF-8"?>\n')
    w('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d" fill="none" role="img" '
      'aria-label="%s contributions in the last year">\n'
      % (W, H, W, H, total))

    w("<defs>\n")
    w('<linearGradient id="hstreak" x1="0" y1="0" x2="1" y2="0">'
      '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
      '<stop offset="1" stop-color="%s" stop-opacity=".55"/></linearGradient>\n'
      % (T["jet"], T["jet"]))
    w('<clipPath id="hcard"><rect x="%d" y="%d" width="%d" height="%d" rx="%d"/>'
      '</clipPath>\n' % CARD)
    # one square, re-used by every quiet day in the grid
    w('<rect id="c" width="%.0f" height="%.0f" rx="3"/>\n' % (CELL, CELL))
    w("</defs>\n")

    w('<rect width="%d" height="%d" fill="%s"/>\n' % (W, H, T["bg"]))
    w('<g clip-path="url(#hcard)">\n')
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>\n'
      % (CARD[0], CARD[1], CARD[2], CARD[3], CARD[4], T["panel"]))

    # ---- header
    w('<text x="%.0f" y="48" font-family="%s" font-size="11" letter-spacing="2" '
      'fill="%s">CONTRIBUTION.GRID</text>\n' % (GX - 16, MONO, T["label"]))
    w('<text x="1126" y="48" font-family="%s" font-size="13" text-anchor="end" '
      'fill="%s">%s contributions in the last year</text>\n'
      % (MONO, T["muted"], total))
    w('<line x1="%.0f" y1="62" x2="1126" y2="62" stroke="%s" stroke-opacity="%s"/>\n'
      % (GX - 16, T["border"], T["border_op"]))

    # ---- month labels
    seen = set()
    for row, col, date, _lvl, _n in sorted(cells, key=lambda c: c[1]):
        if row != 0 or col < col0:
            continue
        m = int(date[5:7])
        if m in seen:
            continue
        seen.add(m)
        w('<text x="%.1f" y="84" font-family="%s" font-size="10.5" fill="%s" '
          'opacity=".8">%s</text>\n' % (cx(col), MONO, T["muted"], MONTHS[m - 1]))

    # ---- day labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        w('<text x="%.1f" y="%.1f" font-family="%s" font-size="10.5" '
          'text-anchor="end" fill="%s" opacity=".8">%s</text>\n'
          % (GX - 10, cy(row) + 11, MONO, T["muted"], name))

    # ---- the grid itself
    # Quiet days are the overwhelming majority and never change, so they are
    # emitted as <use> of one shared square, grouped by colour. Only the days
    # that actually light up need a rect of their own.
    quiet = {}
    for row, col, date, lvl, _n in cells:
        if col < col0 or lvl > 0:
            continue
        quiet.setdefault(lvl, []).append((cx(col), cy(row)))
    for lvl, pts in sorted(quiet.items()):
        w('<g fill="%s">' % T["levels"][lvl])
        for x, y in pts:
            w('<use href="#c" x="%.1f" y="%.1f"/>' % (x, y))
        w('</g>\n')

    for row, col, date, lvl, _n in cells:
        if col < col0 or lvl == 0:
            continue
        base = T["levels"][lvl]
        # the activation wave: flash as the sweep passes this column
        t0 = col_time(col)
        w('<rect x="%.1f" y="%.1f" width="%.0f" height="%.0f" rx="3" fill="%s">'
          '<animate attributeName="fill" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;%s;1" values="%s;%s;%s;%s;%s" calcMode="linear"/>'
          '</rect>\n'
          % (cx(col), cy(row), CELL, CELL, base, LOOP,
             kt(t0), kt(t0 + 0.35), kt(t0 + 1.5), base, base,
             T["flash"], base, base))

    # ---- bullets and blast rings for the targeted days
    w('<g>\n')
    for row, col, _date, _lvl, _n in targets:
        x, y = cx(col) + CELL / 2, cy(row) + CELL / 2
        hit = col_time(col)
        fire = max(0.05, hit - 0.55)
        w('<circle r="2.1" fill="%s" opacity="0">'
          '<animate attributeName="opacity" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;%s;1" values="0;1;1;0;0"/>'
          '<animate attributeName="cx" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="%.1f;%.1f;%.1f;%.1f"/>'
          '<animate attributeName="cy" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="%.1f;%.1f;%.1f;%.1f"/>'
          '</circle>\n'
          % (T["ring"], LOOP, kt(fire), kt(fire + 0.02), kt(hit),
             LOOP, kt(fire), kt(hit), x, x, x, x,
             LOOP, kt(fire), kt(hit), JET_Y, JET_Y, y, y))
        # blast ring
        w('<circle cx="%.1f" cy="%.1f" r="0" fill="none" stroke="%s" '
          'stroke-width="1.6" opacity="0">'
          '<animate attributeName="r" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="0;1;13;13"/>'
          '<animate attributeName="opacity" dur="%ss" repeatCount="indefinite" '
          'keyTimes="0;%s;%s;1" values="0;.9;0;0"/></circle>\n'
          % (x, y, T["ring"], LOOP, kt(hit), kt(hit + 0.7),
             LOOP, kt(hit), kt(hit + 0.7)))
    w('</g>\n')

    # ---- ambient blinking dots
    for i, (dx, dy, dur) in enumerate(((34, 40, 1.2), (34, 236, 1.7),
                                       (1146, 44, 1.5), (1146, 232, 2.0))):
        w('<circle cx="%d" cy="%d" r="1.4" fill="%s">'
          '<animate attributeName="opacity" values=".2;1;.2" dur="%ss" '
          'repeatCount="indefinite"/></circle>\n' % (dx, dy, T["dot"], dur))

    # ---- the jet
    x0, x1 = GX - 24, GX + (COLS - 1) * PITCH + 24
    w('<g><g>'
      '<polygon points="0,-15 8,6 4,3 -4,3 -8,6" fill="%s" stroke="%s" stroke-width="1"/>'
      '<polygon points="-8,6 -14,12 -4,7" fill="%s"/>'
      '<polygon points="8,6 14,12 4,7" fill="%s"/>'
      '<circle cx="0" cy="-5" r="2.2" fill="%s"/>'
      '<polygon points="-3,7 3,7 0,15" fill="%s">'
      '<animate attributeName="opacity" values=".5;1;.6;1" dur=".18s" '
      'repeatCount="indefinite"/></polygon>'
      '</g>'
      '<animateTransform attributeName="transform" type="translate" dur="%ss" '
      'repeatCount="indefinite" keyTimes="0;0.5;1" values="%.1f,%.1f;%.1f,%.1f;%.1f,%.1f"/>'
      '</g>\n'
      % (T["jet"], T["jet2"], T["jet2"], T["jet2"], T["jet3"], T["flame"],
         LOOP, x0, JET_Y, x1, JET_Y, x0, JET_Y))

    w('</g>\n')
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" %s/>\n'
      % (CARD + (bd,)))
    w('</svg>\n')
    return o.getvalue()


def main():
    cells = fetch_calendar()
    total = sum(c[4] for c in cells)
    print("parsed %d days, %d contributions" % (len(cells), total))
    for theme in ("dark", "light"):
        path = "heatmap-%s.svg" % theme
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(theme, cells, total))
        print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
