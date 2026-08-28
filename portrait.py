# -*- coding: utf-8 -*-
"""avatar.png -> ASCII portraits, one per theme.

ascii_portrait.txt        for dark.svg  (bright pixels -> dense glyphs)
ascii_portrait_light.txt  for light.svg (dark pixels  -> dense glyphs)

Re-run after replacing avatar.png; adjust CROP/FOCUS if the new photo
frames the head differently.
"""
import os
import sys
import urllib.request

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

SRC = "avatar.png"
AVATAR_URL = "https://avatars.githubusercontent.com/u/164407769?v=4&s=460"
OUT = "ascii_portrait.txt"
OUT_LIGHT = "ascii_portrait_light.txt"

# head-and-shoulders crop out of the full-body avatar (left, top, right, bottom)
CROP = (230, 44, 338, 200)
ROWS = 52
CHAR_W, LINE_H = 4.44, 8.63     # must match the SVG's mono metrics
RAMP = " .:-=+*#%@"             # sparse -> dense, i.e. light -> dark

# tone controls
CONTRAST = 1.52
BRIGHT = 0.80
GAMMA = 0.92
VIGNETTE = 0.97                 # fade the busy cafe background away
# where the head sits in the crop: (cx, cy, rx, ry) in 0-1 units
FOCUS = (0.48, 0.46, 0.40, 0.46)


def main(crop=CROP, rows=ROWS, contrast=CONTRAST, vignette=VIGNETTE,
         invert=False, out=OUT):
    if not os.path.exists(SRC):
        print("fetching %s ..." % AVATAR_URL)
        urllib.request.urlretrieve(AVATAR_URL, SRC)
    im = Image.open(SRC).convert("RGB").crop(crop)
    w, h = im.size
    cols = max(1, round(rows * (LINE_H / CHAR_W) * (w / h)))

    g = ImageOps.grayscale(im)
    g = g.filter(ImageFilter.MedianFilter(3))       # knock back photo noise
    g = ImageOps.autocontrast(g, cutoff=2)
    # local contrast first: this is what makes eyes, brows and the nose
    # shadow survive the downsample instead of averaging into one bright mass
    g = g.filter(ImageFilter.UnsharpMask(radius=6, percent=205, threshold=2))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = ImageEnhance.Brightness(g).enhance(BRIGHT)

    small = g.resize((cols, rows), Image.LANCZOS)
    px = small.load()

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            v = px[x, y] / 255.0
            v = pow(v, GAMMA)
            # Elliptical vignette centred on the FACE rather than on the
            # frame, so the cafe wall behind him stops competing with it.
            dx = (x / cols - FOCUS[0]) / FOCUS[2]
            dy = (y / rows - FOCUS[1]) / FOCUS[3]
            r = (dx * dx + dy * dy) ** 0.5
            t = min(1.0, max(0.0, (r - 0.80) / 0.55))
            fade = vignette * (t * t * (3 - 2 * t))          # smoothstep
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
