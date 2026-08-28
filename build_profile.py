# -*- coding: utf-8 -*-
"""
Generates the GitHub profile card:

    dark.svg   -> shown when GitHub is in dark mode
    light.svg  -> shown when GitHub is in light mode

Layout is a terminal window: VISUAL.MAP on the left holds an ASCII portrait
built from the GitHub avatar, SYSTEM.INFO on the right holds the CV details
as dot-leader rows.

    python portrait.py        # avatar.png -> ascii_portrait.txt
    python build_profile.py   # -> dark.svg + light.svg

No JavaScript and no external references - GitHub proxies README images
through camo, which strips scripts and blocks external fonts. Motion is SMIL
only, and every reveal keeps its finished state as the base attribute value
so a renderer that ignores animation still shows a complete card.
"""
import io
import os

# ============================== CONFIG ==================================
USER = "MoufeeAlDoushari"
PROMPT = "moufee@devos ~ % ./profile.sh --live"
HOST = "moufee@devos"

ROWS = [
    ("Subject",    "Moufee Al Doushari"),
    ("Role",       "CSE Undergrad · Full-Stack Engineer"),
    ("Origin",     "Dhaka, Bangladesh"),
    ("Education",  "B.Sc. CSE, AUST · CGPA 3.04"),
    ("Status",     "Building • Learning • Shipping"),
    ("ToolChain",  "VS Code, Git, Docker, Postman"),
    ("Core Lang",  "C, C++, Java, C#, Python"),
    ("Frontend",   "React, TypeScript, HTML, CSS, Tailwind"),
    ("Backend",    "Node.js, Express, Flask, FastAPI"),
    ("Database",   "MySQL, PostgreSQL, MongoDB, Redis"),
    ("Mobile",     "Flutter, Dart, Android Studio"),
    ("Infra",      "Docker, AWS S3, JWT, REST APIs"),
]
CONTACT = [
    ("Mail",       "doushari.dipto212@gmail.com"),
    ("Portfolio",  "sites.google.com/view/moufee-al-doushari"),
    ("LinkedIn",   "moufee-al-doushari"),
    ("Github",     "MoufeeAlDoushari"),
]
STATS = [
    ("Codeforces", "Pupil · ICPC Prelim 2024 Honourable Mention"),
    ("Contests",   "Intra AUST 5th (Spring 2025)"),
    ("Projects",   "AponKhoj · Bachelor Solution · Blog Platform"),
]

ART_FILE = {"dark": "ascii_portrait.txt", "light": "ascii_portrait_light.txt"}
# ========================================================================

MONO = ("ui-monospace,SFMono-Regular,Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace")

W, H = 1180, 610
CARD = (16, 16, 1148, 578, 18)
LP = (36, 78, 452, 498, 12)          # VISUAL.MAP
RP = (506, 78, 638, 498, 12)         # SYSTEM.INFO

AFS, ACHW, ALH = 6.7, 4.02, 7.82     # ascii font-size / advance / line-height
ATOT = 16.0                          # ascii reveal loop, seconds

RFS, RCHW = 12.5, 7.5                # info rows
ROW_Y0, ROW_STEP = 126.0, 20.5
LBL_X, DOT_X, VAL_X = 526.0, 636.0, 762.0

THEMES = {
    "dark": dict(
        bg="#050816", panel="#0B1120", inner="#070C1B",
        border="#FFFFFF", border_op=".08",
        text="#E5E7EB", muted="#64748B", dim="#1E293B", label="#7DD3FC",
        a1="#7C3AED", a2="#22D3EE", a3="#10B981", sky="#38BDF8",
        art_stops=[("#22D3EE", "#7C3AED"), ("#38BDF8", "#22D3EE"),
                   ("#7C3AED", "#38BDF8")],
        art_op=".95", glow_std="2.0", glow_n=2,
        scan_op=".10", grid_op=".05", shim_op=".85",
    ),
    "light": dict(
        bg="#FFFFFF", panel="#F8FAFC", inner="#F1F5F9",
        border="#0F172A", border_op=".10",
        text="#0F172A", muted="#475569", dim="#CBD5E1", label="#0284C7",
        a1="#4F46E5", a2="#0891B2", a3="#059669", sky="#0EA5E9",
        art_stops=[("#0891B2", "#4F46E5"), ("#0EA5E9", "#0891B2"),
                   ("#4F46E5", "#0EA5E9")],
        art_op="1", glow_std="1.1", glow_n=1,
        scan_op=".05", grid_op=".035", shim_op=".5",
    ),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kt(t, total):
    return round(max(0.0, min(1.0, t / total)), 5)


def load_art(theme):
    with open(ART_FILE[theme], encoding="utf-8") as f:
        return [l.rstrip("\n").rstrip() for l in f.read().split("\n")]


# ================================ build =================================
def build(theme, art):
    T = THEMES[theme]
    o = io.StringIO()
    w = o.write
    bd = 'stroke="%s" stroke-opacity="%s"' % (T["border"], T["border_op"])

    art_rows = [l for l in art if l.strip()]
    art_cols = max(len(l) for l in art_rows)
    ax = LP[0] + (LP[2] - art_cols * ACHW) / 2.0
    ay = 120.0
    ay += (LP[1] + LP[3] - 14 - (ay + (len(art) - 1) * ALH)) / 2.0

    w('<?xml version="1.0" encoding="UTF-8"?>\n')
    w('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d" fill="none" role="img" '
      'aria-label="%s - developer profile card">\n'
      % (W, H, W, H, esc(ROWS[0][1])))

    # ------------------------------ defs ------------------------------
    w("<defs>\n")
    s0, s1 = zip(*T["art_stops"])
    w('<linearGradient id="art" gradientUnits="userSpaceOnUse" '
      'x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f">' % (ax, ay - 20, ax + art_cols * ACHW, ay + len(art) * ALH))
    for off, seq in ((0, s0), (1, s1)):
        w('<stop offset="%s" stop-color="%s"><animate attributeName="stop-color" '
          'values="%s" dur="9s" repeatCount="indefinite"/></stop>'
          % (off, seq[0], ";".join(list(seq) + [seq[0]])))
    w("</linearGradient>\n")

    w('<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">'
      '<stop offset="0" stop-color="%s"/><stop offset=".5" stop-color="%s"/>'
      '<stop offset="1" stop-color="%s"/></linearGradient>\n'
      % (T["a1"], T["a2"], T["a3"]))

    w('<linearGradient id="shim" gradientUnits="userSpaceOnUse" '
      'x1="-620" y1="0" x2="0" y2="580">'
      '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
      '<stop offset=".45" stop-color="%s" stop-opacity=".85"/>'
      '<stop offset=".55" stop-color="%s" stop-opacity=".85"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/>'
      '<animateTransform attributeName="gradientTransform" type="translate" '
      'from="0 0" to="2400 0" dur="8s" repeatCount="indefinite"/>'
      '</linearGradient>\n' % (T["a2"], T["a2"], T["a1"], T["a1"]))

    w('<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
      '<stop offset=".5" stop-color="%s" stop-opacity="1"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>\n'
      % (T["a2"], T["a2"], T["a2"]))

    w('<radialGradient id="halo"><stop offset="0" stop-color="%s" stop-opacity=".55"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
      % (T["a1"], T["a1"]))
    w('<radialGradient id="halo2"><stop offset="0" stop-color="%s" stop-opacity=".5"/>'
      '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
      % (T["a2"], T["a2"]))

    w('<filter id="glow" x="-40%%" y="-40%%" width="180%%" height="180%%">'
      '<feGaussianBlur stdDeviation="%s" result="b"/><feMerge>%s'
      '<feMergeNode in="SourceGraphic"/></feMerge></filter>\n'
      % (T["glow_std"], '<feMergeNode in="b"/>' * T["glow_n"]))
    w('<filter id="blur"><feGaussianBlur stdDeviation="60"/></filter>\n')
    w('<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
      '<path d="M40 0H0V40" fill="none" stroke="%s" stroke-width=".5"/>'
      '</pattern>\n' % T["border"])

    w('<clipPath id="cCard"><rect x="%d" y="%d" width="%d" height="%d" rx="%d"/></clipPath>\n' % CARD)
    w('<clipPath id="cL"><rect x="%d" y="%d" width="%d" height="%d" rx="%d"/></clipPath>\n' % LP)

    # Scanning reveal: one mask wipes down the portrait, so the art appears
    # line by line as the edge passes it. One mask instead of one clipPath
    # per line keeps the file small enough to sit comfortably in a README.
    top = ay - AFS - 4
    full = len(art) * ALH + 8
    w('<mask id="rv" maskUnits="userSpaceOnUse" x="%d" y="%.1f" width="%d" height="%.1f">'
      '<rect x="%d" y="%.1f" width="%d" height="%.1f" fill="#fff">'
      '<animate attributeName="height" values="0;0;%.1f;%.1f;0;0" '
      'keyTimes="0;%s;%s;%s;%s;1" dur="%ss" repeatCount="indefinite"/>'
      '</rect></mask>\n'
      % (LP[0], top, LP[2], full, LP[0], top, LP[2], full, full, full,
         kt(0.4, ATOT), kt(4.6, ATOT), kt(13.6, ATOT), kt(14.9, ATOT), ATOT))
    w("</defs>\n")

    # ----------------------------- paint ------------------------------
    w('<rect width="%d" height="%d" fill="%s"/>\n' % (W, H, T["bg"]))

    w('<g clip-path="url(#cCard)">\n')
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>\n'
      % (CARD[0], CARD[1], CARD[2], CARD[3], CARD[4], T["panel"]))
    # ambient glows
    w('<g filter="url(#blur)" opacity=".55">'
      '<circle cx="250" cy="150" r="150" fill="url(#halo)">'
      '<animate attributeName="cy" values="150;260;150" dur="17s" repeatCount="indefinite"/></circle>'
      '<circle cx="980" cy="480" r="160" fill="url(#halo2)">'
      '<animate attributeName="cx" values="980;860;980" dur="21s" repeatCount="indefinite"/></circle>'
      '</g>\n')
    # faint grid, as a tile rather than ~44 separate lines
    w('<rect x="16" y="16" width="1148" height="578" fill="url(#grid)" '
      'opacity="%s"/>\n' % T["grid_op"])

    # ---- title bar
    for j, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        w('<circle cx="%d" cy="38" r="5" fill="%s" opacity=".92"/>' % (46 + j * 18, c))
    w('\n<text x="112" y="42" font-family="%s" font-size="12.5" fill="%s" '
      'xml:space="preserve">%s</text>\n' % (MONO, T["muted"], esc(PROMPT)))
    w('<rect x="%.1f" y="32" width="7.5" height="13" fill="%s">'
      '<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.48;.5;.98;1" '
      'dur="1.05s" repeatCount="indefinite"/></rect>\n'
      % (112 + len(PROMPT) * 7.5 + 3, T["a2"]))
    w('<line x1="16" y1="60" x2="1164" y2="60" stroke="%s" stroke-opacity="%s"/>\n'
      % (T["border"], T["border_op"]))

    # ================= LEFT PANEL - VISUAL.MAP ==================
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" %s/>\n'
      % (LP[0], LP[1], LP[2], LP[3], LP[4], T["inner"], bd))
    w('<text x="%d" y="100" font-family="%s" font-size="10.5" letter-spacing="2" '
      'fill="%s">VISUAL.MAP</text>\n' % (LP[0] + 18, MONO, T["label"]))
    w('<g><circle cx="%d" cy="96" r="3.2" fill="%s">'
      '<animate attributeName="opacity" values="1;.2;1" dur="1.5s" repeatCount="indefinite"/>'
      '</circle><text x="%d" y="100" font-family="%s" font-size="10" letter-spacing="1.6" '
      'text-anchor="end" fill="%s">SCANNING</text></g>\n'
      % (LP[0] + LP[2] - 92, T["a3"], LP[0] + LP[2] - 18, MONO, T["muted"]))

    w('<g clip-path="url(#cL)">\n')
    # portrait
    # font/space/fill are set once here and inherited by every line
    w('<g filter="url(#glow)" opacity="%s" mask="url(#rv)" xml:space="preserve" '
      'font-family="%s" font-size="%s" fill="url(#art)" '
      'lengthAdjust="spacingAndGlyphs">\n' % (T["art_op"], MONO, AFS))
    for i, line in enumerate(art):
        if not line.strip():
            continue
        w('<text x="%.1f" y="%.1f" textLength="%.1f">%s</text>\n'
          % (ax, ay + i * ALH, len(line) * ACHW, esc(line)))
    w("</g>\n")
    # scanline sweeping the portrait
    w('<rect x="%d" y="%d" width="%d" height="70" fill="url(#scan)" opacity="%s">'
      '<animateTransform attributeName="transform" type="translate" '
      'values="0 -120;0 540" dur="5s" repeatCount="indefinite"/></rect>\n'
      % (LP[0], LP[1], LP[2], T["scan_op"]))
    w("</g>\n")

    # ================= RIGHT PANEL - SYSTEM.INFO ==================
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" %s/>\n'
      % (RP[0], RP[1], RP[2], RP[3], RP[4], T["inner"], bd))
    w('<text x="%d" y="100" font-family="%s" font-size="10.5" letter-spacing="2" '
      'fill="%s">SYSTEM.INFO</text>\n' % (RP[0] + 18, MONO, T["label"]))
    w('<text x="%d" y="100" font-family="%s" font-size="10" letter-spacing="1.6" '
      'text-anchor="end" fill="%s">github.com/%s</text>\n'
      % (RP[0] + RP[2] - 18, MONO, T["muted"], esc(USER)))

    n = 0

    def line_y():
        return ROW_Y0 + n * ROW_STEP

    def reveal(idx):
        """Fade in, but leave the finished state as the base value."""
        b = 0.75 + idx * 0.075
        tot = b + 0.45
        return ('<animate attributeName="opacity" values="0;0;1" keyTimes="0;%s;1" '
                'dur="%.2fs" fill="freeze"/>' % (round(b / tot, 4), tot))

    def section(title):
        nonlocal n
        y = line_y()
        w('<g opacity="1">%s'
          '<text x="%.1f" y="%.1f" font-family="%s" font-size="11" letter-spacing="1.4" '
          'fill="%s">%s</text>'
          '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity=".55"/>'
          '</g>\n'
          % (reveal(n), LBL_X, y, MONO, T["a3"], esc(title),
             LBL_X + len(title) * 6.8 + 12, y - 4, RP[0] + RP[2] - 18, y - 4, T["dim"]))
        n += 1

    def row(label, value):
        nonlocal n
        y = line_y()
        dots = int((VAL_X - 10 - DOT_X) / RCHW)
        w('<g opacity="1">%s'
          '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s">%s</text>'
          '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s" '
          'textLength="%.1f" lengthAdjust="spacing">%s</text>'
          '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s">%s</text>'
          '</g>\n'
          % (reveal(n),
             LBL_X, y, MONO, RFS, T["label"], esc(label),
             DOT_X, y, MONO, RFS, T["dim"], VAL_X - 10 - DOT_X, "." * dots,
             VAL_X, y, MONO, RFS, T["text"], esc(value)))
        n += 1

    # host line
    y = line_y()
    w('<text x="%.1f" y="%.1f" font-family="%s" font-size="13.5" fill="%s">'
      '<tspan fill="%s">%s</tspan></text>\n'
      % (LBL_X, y, MONO, T["text"], T["a2"], esc(HOST)))
    w('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity=".7"/>\n'
      % (LBL_X + len(HOST) * 8.1 + 12, y - 4, RP[0] + RP[2] - 18, y - 4, T["dim"]))
    n += 1

    for k, v in ROWS:
        row(k, v)
    section("Contact")
    for k, v in CONTACT:
        row(k, v)
    section("Live Stats")
    for k, v in STATS:
        row(k, v)

    w("</g>\n")  # /card clip

    # card border + shimmer
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" %s/>\n' % (CARD + (bd,)))
    w('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" '
      'stroke="url(#shim)" stroke-width="1.4" opacity="%s"/>\n' % (CARD + (T["shim_op"],)))
    w("</svg>\n")
    return o.getvalue()


def main():
    for theme in ("dark", "light"):
        path = theme + ".svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(theme, load_art(theme)))
        print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
