# -*- coding: utf-8 -*-
"""portrait_src.jpg -> ASCII portraits, one per theme.

ascii_portrait.txt        for dark.svg
ascii_portrait_light.txt  for light.svg

The art is a full-frame tonal map: every cell of the grid gets a glyph, the
wall behind him included, so VISUAL.MAP holds a solid rectangle of portrait
edge to edge rather than a cut-out floating in the middle of the panel.

The ramp runs dark -> dense. He is the dark half of this photo - navy suit,
dark hair - so that is what puts the weight on him and lets the lit wall fall
away to dots. It holds on both cards: dense glows on the dark one and inks on
the light one, and the subject wants to be the loud part of either, so the two
files come out identical. They are still written separately so the themes can
be pulled apart again without touching build_profile.py.

Luminance alone cannot finish the job here - his skin reads about as bright as
the wall behind it - so BACKDROP leans on the subject mask below to press the
wall down the ramp. It presses, it does not erase: the wall still renders, as
the sparse dot texture the frame needs to stay full.

The photo itself is not committed - drop yours in beside this script as
portrait_src.jpg and run it. Both .txt files ARE committed, so the card can
be rebuilt with build_profile.py without the photo or Pillow.

Swapping the photo means re-fitting CROP to the new framing, then the HEAD /
SHOULDER_* numbers that say where the subject sits inside it. Keep CROP near
ASPECT: that is what makes ROWS rows come out COLS columns wide, and those
proportions are what decide how much of the panel the art covers.
"""
import os
import sys

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

SRC = "portrait_src.jpg"        # the studio portrait this art is traced from
OUT = "ascii_portrait.txt"
OUT_LIGHT = "ascii_portrait_light.txt"

# Head-and-shoulders crop out of the full frame (left, top, right, bottom):
# hair clear of the top edge, shoulders running out of both bottom corners.
CROP = (709, 706, 2170, 2137)
ROWS, COLS = 53, 92
CHAR_W, LINE_H = 4.44, 7.55     # must match the SVG's mono metrics
ASPECT = ROWS * LINE_H / (COLS * CHAR_W)
RAMP = " .:-=+*#%@"             # sparse -> dense

# tone controls
CUTOFF = 1                      # autocontrast clip, percent per end
CONTRAST = 1.30
GAMMA = 0.72                    # <1 fills his face in, >1 thins the frame out
FLOOR, CEIL = 0.06, 0.97        # ramp window - FLOOR keeps the wall off blank
BACKDROP = 0.78                 # how far off-subject tone is pressed down
BLUR = 12                       # px, just under a cell - see note in main()

# Subject mask, in crop-relative 0-1 units: an ellipse on the head plus a
# widening wedge for the torso, feathered so neither edge shows as a seam.
HEAD = (0.517, 0.269, 0.205, 0.230)     # cx, cy, rx, ry - hair, not skull
SHOULDER_Y = 0.50                       # where the neck/torso starts
SHOULDER_CX = 0.520
SHOULDER_W0, SHOULDER_W1 = 0.12, 0.44   # half-width at the neck / at the hem
FEATHER = 0.07                          # softness of the mask edge


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def subject_mask(u, v):
    """1 on him, 0 on the wall, feathered in between."""
    dx = (u - HEAD[0]) / HEAD[2]
    dy = (v - HEAD[1]) / HEAD[3]
    head = 1.0 - smoothstep(1.0 - FEATHER, 1.0 + FEATHER,
                            (dx * dx + dy * dy) ** 0.5)

    t = min(1.0, max(0.0, (v - SHOULDER_Y) / (1.0 - SHOULDER_Y)))
    hw = SHOULDER_W0 + (SHOULDER_W1 - SHOULDER_W0) * t
    torso = (smoothstep(SHOULDER_Y - 0.06, SHOULDER_Y + 0.06, v)
             * (1.0 - smoothstep(hw - FEATHER, hw + FEATHER, abs(u - SHOULDER_CX))))
    return max(head, torso)


def main(crop=CROP, rows=ROWS, contrast=CONTRAST, gamma=GAMMA,
         backdrop=BACKDROP, out=OUT):
    if not os.path.exists(SRC):
        raise SystemExit("put the source photo at %s first" % SRC)
    im = Image.open(SRC).convert("RGB").crop(crop)
    w, h = im.size
    cols = max(1, round(rows * (LINE_H / CHAR_W) * (w / float(h))))

    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=CUTOFF)
    # local contrast first: this is what makes brows, the nose shadow and the
    # lapels survive the downsample instead of averaging into one flat mass
    g = g.filter(ImageFilter.UnsharpMask(radius=6, percent=150, threshold=2))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    # The wall is a perforated panel whose holes land about two cells apart -
    # right at the grid's Nyquist limit, which moires into a herringbone over
    # the whole background. Blurring them out just before the downsample is
    # what keeps the wall a flat field.
    g = g.filter(ImageFilter.GaussianBlur(BLUR))

    small = g.resize((cols, rows), Image.LANCZOS)
    px = small.load()

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            d = 1.0 - px[x, y] / 255.0          # dark pixel -> dense glyph
            d = pow(min(1.0, max(0.0, d)), gamma)
            fade = backdrop * (1.0 - subject_mask((x + 0.5) / cols,
                                                  (y + 0.5) / rows))
            d *= 1.0 - fade
            d = FLOOR + d * (CEIL - FLOOR)
            row.append(RAMP[int(round(min(1.0, max(0.0, d)) * (len(RAMP) - 1)))])
        lines.append("".join(row).rstrip())

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return lines


if __name__ == "__main__":
    a = sys.argv[1:]
    crop = tuple(int(x) for x in a[:4]) if len(a) >= 4 else CROP
    rows = int(a[4]) if len(a) > 4 else ROWS
    con = float(a[5]) if len(a) > 5 else CONTRAST
    gam = float(a[6]) if len(a) > 6 else GAMMA
    bak = float(a[7]) if len(a) > 7 else BACKDROP
    art = main(crop, rows, con, gam, bak, out=OUT)
    main(crop, rows, con, gam, bak, out=OUT_LIGHT)
    print("wrote %s and %s (%d cols x %d rows)"
          % (OUT, OUT_LIGHT, max(len(l) for l in art), len(art)))
