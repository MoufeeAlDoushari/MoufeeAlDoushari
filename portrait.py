# -*- coding: utf-8 -*-
"""portrait_src.jpg -> ASCII portraits, one per theme.

ascii_portrait.txt        for dark.svg  (bright pixels -> dense glyphs)
ascii_portrait_light.txt  for light.svg (dark pixels  -> dense glyphs)

The photo itself is not committed - drop yours in beside this script as
portrait_src.jpg and run it. Both .txt files ARE committed, so the card can
be rebuilt with build_profile.py without the photo or Pillow.

Swapping the photo means re-fitting two things to the new framing: CROP,
and the HEAD / SHOULDER_* numbers that describe where the subject sits
inside that crop.
"""
import os
import sys

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

SRC = "portrait_src.jpg"        # the studio portrait this art is traced from
OUT = "ascii_portrait.txt"
OUT_LIGHT = "ascii_portrait_light.txt"

# head-and-shoulders crop out of the full frame (left, top, right, bottom)
CROP = (911, 540, 1994, 1790)
ROWS = 52
CHAR_W, LINE_H = 4.44, 8.63     # must match the SVG's mono metrics
RAMP = " .:-=+*#%@"             # sparse -> dense, i.e. light -> dark

# tone controls
CONTRAST = 1.30
BRIGHT = 1.20
GAMMA = 1.16
VIGNETTE = 1.0                  # how hard the background is pushed away

# Subject mask, in crop-relative 0-1 units. The wall behind him is BRIGHTER
# than he is, so a plain vignette cannot separate them - anything outside this
# shape is pushed to the empty end of the ramp instead.
HEAD = (0.487, 0.448, 0.252, 0.276)     # cx, cy, rx, ry - the real hairline

# The two themes want opposite errors on this mask. On the dark card the wall
# is bright, so anything of it left inside the mask lights up - the mask has to
# sit INSIDE the hairline, and the hair it clips was going to render empty
# anyway. On the light card the wall renders as blank paper, so the mask can
# sit outside the hairline and keep the whole head.
MASK_SCALE = {"dark": 0.90, "light": 1.08}
SHOULDER_Y = 0.62                       # where the neck/torso starts
SHOULDER_CX = 0.475
SHOULDER_W0, SHOULDER_W1 = 0.14, 0.46   # half-width at the neck / at the shoulders
FEATHER = 0.055                         # softness of the mask edge


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def subject_mask(u, v, k=1.0):
    """1 on him, 0 on the wall, feathered in between."""
    dx = (u - HEAD[0]) / (HEAD[2] * k)
    dy = (v - HEAD[1]) / (HEAD[3] * k)
    head = 1.0 - smoothstep(1.0 - FEATHER, 1.0 + FEATHER,
                            (dx * dx + dy * dy) ** 0.5)

    t = min(1.0, max(0.0, (v - SHOULDER_Y) / (1.0 - SHOULDER_Y)))
    hw = (SHOULDER_W0 + (SHOULDER_W1 - SHOULDER_W0) * t) * k
    torso = (smoothstep(SHOULDER_Y - 0.05, SHOULDER_Y + 0.05, v)
             * (1.0 - smoothstep(hw - FEATHER, hw + FEATHER, abs(u - SHOULDER_CX))))
    return max(head, torso)


def main(crop=CROP, rows=ROWS, contrast=CONTRAST, vignette=VIGNETTE,
         invert=False, out=OUT):
    if not os.path.exists(SRC):
        raise SystemExit("put the source photo at %s first" % SRC)
    im = Image.open(SRC).convert("RGB").crop(crop)
    w, h = im.size
    cols = max(1, round(rows * (LINE_H / CHAR_W) * (w / h)))

    g = ImageOps.grayscale(im)
    g = g.filter(ImageFilter.MedianFilter(3))       # knock back photo noise
    g = ImageOps.autocontrast(g, cutoff=2)
    # local contrast first: this is what makes eyes, brows and the nose
    # shadow survive the downsample instead of averaging into one bright mass
    g = g.filter(ImageFilter.UnsharpMask(radius=6, percent=150, threshold=2))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = ImageEnhance.Brightness(g).enhance(BRIGHT)

    k = MASK_SCALE["light" if invert else "dark"]
    small = g.resize((cols, rows), Image.LANCZOS)
    px = small.load()

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            v = px[x, y] / 255.0
            v = pow(v, GAMMA)
            # Everything off the subject fades out, so only he is drawn.
            fade = vignette * (1.0 - subject_mask((x + 0.5) / cols,
                                                  (y + 0.5) / rows, k))
            if invert:
                # Light card: glyphs are dark ink on white, so MORE ink must
                # mean a DARKER pixel. Background fades towards white.
                vv = v + fade * (1.0 - v)
                d = 1.0 - vv
            else:
                # Dark card: glyphs glow on near-black, so more ink means a
                # BRIGHTER pixel. Background fades towards black.
                vv = v * (1.0 - fade)
                d = vv
            row.append(RAMP[int(round(min(1.0, max(0.0, d)) * (len(RAMP) - 1)))])
        lines.append("".join(row).rstrip())

    # Drop the empty bands above and below him, otherwise the card centres the
    # dead space along with the portrait and he sits low in the panel.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return lines


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4:
        crop = tuple(int(x) for x in a[:4])
    else:
        crop = CROP
    rows = int(a[4]) if len(a) > 4 else ROWS
    con = float(a[5]) if len(a) > 5 else CONTRAST
    vig = float(a[6]) if len(a) > 6 else VIGNETTE
    dark = main(crop, rows, con, vig, invert=False, out=OUT)
    main(crop, rows, con, vig, invert=True, out=OUT_LIGHT)
    print("wrote %s and %s (%d cols x %d rows)"
          % (OUT, OUT_LIGHT, max(len(l) for l in dark), len(dark)))
