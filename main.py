"""TARNMERE — travel poster for a place that isn't there.

Procedural poster, 1024x1024, PIL + stdlib only. Deterministic: one fixed
seed drives every random choice; no time, no network, no input files.

The wonder: in Tarnmere the dusk never leaves the water. Terraced
mirror-pools step down a quiet hillside, and each pool holds the sky —
violet dusk above, rose-gold where the sun went down — so the whole
hillside looks like the sky folded into the ground. Palette is driven by
that wonder: indigo dusk, rose-gold horizon light, silver-violet pools,
dark teal terraces.
"""

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W = H = 1024
SEED = 20261121
OUT = "/output/entry.png"

# Palette — the wonder drives it.
DUSK_TOP = (22, 16, 58)        # deep indigo night falling
DUSK_MID = (74, 44, 108)       # violet dusk
DUSK_LOW = (196, 110, 96)      # rose-gold where the sun went down
SUN = (255, 214, 150)          # low sun, pale gold
POOL_TOP = (214, 150, 128)     # pool mirrors the rose horizon
POOL_MID = (96, 74, 128)       # pool mirrors the violet sky
POOL_BOT = (18, 34, 48)        # pool deepens to dark teal
LIP = (58, 44, 52)             # terrace stone, warm dark
LIP_LIT = (214, 150, 110)      # lip edge catching dusk light
RIDGE = (38, 66, 74)           # hazy far ridge
SHORE = (12, 24, 30)           # dark foreground shore
INK = (248, 238, 214)          # ivory type
ROSE = (236, 176, 128)         # rose-gold rule / glow


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_gradient(size, stops):
    """Vertical multi-stop gradient from a list of (t, rgb)."""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = mix(c0, c1, f)
                break
        for x in range(w):
            px[x, y] = col
    return img


def soft_disc(layer_size, colour, blur):
    """A soft-edged bright disc on a transparent layer."""
    img = Image.new("RGBA", layer_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = layer_size[0] // 2, layer_size[1] // 2
    r = min(layer_size) // 2 - 8
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (255,))
    return img.filter(ImageFilter.GaussianBlur(blur))


def pick_font(bold, size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ]
    if not bold:
        paths = [p.replace("-Bold", "") for p in paths] + paths
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def spaced_text(draw, cx, y, text, font, fill, tracking=0.14):
    """Draw centred text with letter spacing; returns total width."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * font.size * max(len(text) - 1, 0)
    x = cx - total / 2.0
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += wch + tracking * font.size
    return total


def main():
    rng = random.Random(SEED)

    # --- Dusk sky: indigo top, violet middle, rose-gold horizon. ---
    img = sky_gradient((W, H), [
        (0.00, DUSK_TOP),
        (0.30, DUSK_MID),
        (0.44, DUSK_LOW),
        (0.47, (226, 158, 122)),
        (1.00, (20, 26, 36)),
    ]).convert("RGBA")

    # --- Low sun sitting on the horizon, with a wide soft bloom. ---
    sun_x, sun_y = 700, 452
    bloom = soft_disc((640, 640), (255, 178, 110), 60)
    bloom.putalpha(bloom.split()[3].point(lambda v: v // 2))
    img.alpha_composite(bloom, (sun_x - 320, sun_y - 320))
    sun = soft_disc((150, 150), SUN, 10)
    img.alpha_composite(sun, (sun_x - 75, sun_y - 75))

    # --- Dusk clouds: soft ellipses, lit rose underneath, violet above. ---
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for _ in range(34):
        cx = rng.uniform(40, W - 40)
        cy = rng.uniform(300, 440)
        rx = rng.uniform(70, 190)
        ry = rng.uniform(12, 34)
        shade = rng.choice([(238, 214, 220), (210, 186, 220), (246, 200, 178)])
        cd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                   fill=shade + (rng.randint(110, 165),))
    img.alpha_composite(clouds.filter(ImageFilter.GaussianBlur(16)))

    # --- Far hazy ridge under the horizon. ---
    ridge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ridge)
    pts = [(0, 520)]
    x = 0
    while x <= W:
        pts.append((x, 478 + rng.uniform(-10, 10)))
        x += 72
    pts += [(W, 520), (W, H), (0, H)]
    rd.polygon(pts, fill=RIDGE + (255,))
    img.alpha_composite(ridge.filter(ImageFilter.GaussianBlur(5)))

    # --- Terraced mirror-pools: four bands stepping down the hill. ---
    # Each pool is a horizontal mirror of the sky above it: rose near the
    # horizon, violet in the middle, dark teal at its foot. A thin stone
    # lip with a dusk-lit edge separates the bands; the bands grow taller
    # toward the viewer (nearer = bigger).
    bands = [(486, 556), (562, 652), (658, 758), (764, 884)]
    # Each band's reflection sits at a different x, so the bright column
    # cannot join up into one continuous "road" down the poster.
    refl_x = [sun_x - 44, sun_x + 12, sun_x + 48, sun_x - 18]
    for bi, (y0, y1) in enumerate(bands):
        h = y1 - y0
        pool = Image.new("RGB", (W, h))
        pd = ImageDraw.Draw(pool)
        top_mix = mix(POOL_TOP, POOL_MID, bi * 0.14)
        for y in range(h):
            t = y / max(h - 1, 1)
            if t < 0.45:
                col = mix(top_mix, POOL_MID, t / 0.45)
            else:
                col = mix(POOL_MID, POOL_BOT, (t - 0.45) / 0.55)
            pd.line([(0, y), (W, y)], fill=col)
        pool = pool.convert("RGBA")
        pl = ImageDraw.Draw(pool)
        # Sun's reflection: narrow, dim, and broken into shimmering
        # segments — a solid bright column reads as a road, not water.
        rx = refl_x[bi]
        for y in range(0, h, 3):
            if (y // 16) % 3 == 0:
                continue
            wob = math.sin(y / 26.0 + bi * 1.7) * 12
            fade = 1.0 - y / float(h)
            pl.line([(rx - 13 + wob, y), (rx + 13 + wob, y)],
                    fill=(255, 222, 170, int(58 * fade)), width=3)
        # Shimmer: short horizontal strokes, brighter near the top.
        for _ in range(26):
            y = rng.uniform(2, h - 4)
            x0 = rng.uniform(30, W - 160)
            ln = rng.uniform(40, 130)
            al = int(rng.uniform(14, 46) * (1.0 - y / h * 0.6))
            pl.line([(x0, y), (x0 + ln, y)],
                    fill=(226, 214, 240, al), width=2)
        pool = pool.filter(ImageFilter.GaussianBlur(1.2))
        img.paste(pool, (0, y0))
        # Stone lip under the band, top edge lit by the dusk.
        lip = ImageDraw.Draw(img, "RGBA")
        lip.rectangle([0, y1 - 2, W, y1 + 5], fill=LIP + (255,))
        lip.line([(0, y1 - 2), (W, y1 - 2)], fill=LIP_LIT + (100,), width=2)

    # --- A small shelter on the second terrace: one warm window, so the
    # poster promises a stay, not just a view. ---
    hut_x, hut_y = 196, 640
    hut = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hut)
    hd.rectangle([hut_x, hut_y, hut_x + 74, hut_y + 46], fill=(16, 22, 30, 255))
    hd.polygon([(hut_x - 8, hut_y), (hut_x + 37, hut_y - 26),
                (hut_x + 82, hut_y)], fill=(12, 18, 26, 255))
    hd.rectangle([hut_x + 18, hut_y + 16, hut_x + 34, hut_y + 32],
                 fill=(255, 196, 110, 255))
    hd.rectangle([hut_x + 46, hut_y + 16, hut_x + 60, hut_y + 32],
                 fill=(255, 196, 110, 255))
    img.alpha_composite(hut.filter(ImageFilter.GaussianBlur(1)))
    glow = soft_disc((120, 120), (255, 190, 110), 26)
    glow.putalpha(glow.split()[3].point(lambda v: v // 3))
    img.alpha_composite(glow, (hut_x - 23, hut_y - 32))

    # --- Dark foreground shore at the foot of the lowest pool. ---
    shore = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shore)
    pts = [(0, H), (0, 930)]
    x = 0
    while x <= W:
        pts.append((x, 930 + rng.uniform(-8, 8)))
        x += 80
    pts += [(W, H)]
    sd.polygon(pts, fill=SHORE + (255,))
    img.alpha_composite(shore.filter(ImageFilter.GaussianBlur(3)))
    # A few reed silhouettes on the shore, catching the last light.
    rd2 = ImageDraw.Draw(img, "RGBA")
    for _ in range(9):
        x0 = rng.uniform(60, W - 60)
        y0 = rng.uniform(946, 1000)
        lean = rng.uniform(-14, 14)
        rd2.line([(x0, y0), (x0 + lean, y0 - rng.uniform(28, 52))],
                 fill=(30, 46, 44, 255), width=3)

    # --- Grain + vignette: texture so the poster is not flat vector. ---
    img = img.convert("RGB")
    tile = Image.frombytes("L", (512, 512), rng.randbytes(512 * 512))
    noise = tile.resize((W, H), Image.BICUBIC).point(
        lambda v: 128 + (v - 128) // 20)
    img = ImageChops.add(img, Image.merge("RGB", (noise, noise, noise)),
                         scale=1, offset=-128)
    img = Image.blend(img, img.filter(ImageFilter.GaussianBlur(1)), 0.3)
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, W + 220, H + 220], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    img = Image.composite(img, Image.new("RGB", (W, H), (8, 6, 18)), vig)

    # --- Type: the name carries the mood (ivory + rose glow), one line. ---
    img = img.convert("RGBA")
    name_font = pick_font(bold=True, size=118)
    tag_font = pick_font(bold=False, size=30)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd2 = ImageDraw.Draw(halo)
    spaced_text(hd2, W / 2, 96, "TARNMERE", name_font,
                fill=(255, 196, 140, 255), tracking=0.16)
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(12)))
    draw = ImageDraw.Draw(img, "RGBA")
    spaced_text(draw, W / 2, 96, "TARNMERE", name_font, fill=INK + (255,),
                tracking=0.16)
    draw.line([(W / 2 - 150, 240), (W / 2 + 150, 240)], fill=ROSE + (255,),
              width=3)
    spaced_text(draw, W / 2, 260, "WHERE THE SKY LIVES IN STILL WATER",
                tag_font, fill=(233, 222, 200, 235), tracking=0.22)

    # --- Save + gate self-check. ---
    os.makedirs("/output", exist_ok=True)
    img.convert("RGB").save(OUT, "PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}: {W}x{H}, {size} bytes")
    assert size <= 1_048_576, f"PNG too large: {size} bytes"
    return 0


if __name__ == "__main__":
    sys.exit(main())
