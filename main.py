"""AERFALL — travel poster for a place that isn't there.

Procedural poster, 1024x1024, PIL + stdlib only. Deterministic: one fixed
seed drives every random choice; no time, no network, no input files.

The wonder: in Aerfall the falls rise. A luminous column of water climbs
out of a dark valley pool, up through a dusk cloud bank, into the sky.
Palette is driven by that wonder: violet dusk sky, warm gold horizon,
silver-white falling-up water, deep teal valley.
"""

import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W = H = 1024
SEED = 20261121
OUT = "/output/entry.png"

# Palette (2-3 colours driving everything, per the brief).
SKY_TOP = (26, 18, 64)       # deep indigo
SKY_MID = (88, 54, 122)      # violet
SKY_LOW = (198, 122, 106)    # rose-gold dusk near the horizon
SUN_CORE = (255, 233, 184)   # pale gold
FALL_CORE = (238, 240, 255)  # silver-white rising water
FALL_EDGE = (150, 160, 220)  # violet mist
VALLEY_FAR = (46, 82, 88)    # hazy teal ridge
VALLEY_NEAR = (13, 42, 46)   # dark teal foreground ridge
POOL_DARK = (10, 26, 32)     # mirror pool
INK = (247, 234, 208)        # ivory type
GOLD = (232, 190, 120)       # gold rule / glow


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, stops):
    """Vertical multi-stop gradient. stops: [(0.0, rgb), ..., (1.0, rgb)]."""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    n = len(stops)
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(n - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = lerp(c0, c1, f)
                break
        else:
            col = stops[-1][1]
        for x in range(w):
            px[x, y] = col
    return img


def radial_glow(size, colour, inner=1.0):
    """Soft radial glow: bright centre fading to transparent edges."""
    w, h = size
    glow = Image.new("L", size, 0)
    px = glow.load()
    cx, cy = w / 2.0, h / 2.0
    rmax = math.hypot(cx, cy)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / rmax
            v = max(0.0, 1.0 - d) ** 2 * 255 * inner
            px[x, y] = int(v)
    layer = Image.new("RGB", size, colour)
    out = Image.new("RGB", size, (0, 0, 0))
    out.paste(layer, (0, 0), glow)
    return out, glow


def find_font(bold=True, size=100):
    """Serif font, best-effort search; falls back to PIL's default font."""
    cands = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ]
    if not bold:
        cands = [c.replace("-Bold", "") for c in cands] + cands
    for path in cands:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_tracked(draw, cx, y, text, font, fill, tracking=0.12):
    """Centre text with letter tracking; returns width used."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * font.size * max(len(text) - 1, 0)
    x = cx - total / 2.0
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += wch + tracking * font.size
    return total


def main():
    rng = random.Random(SEED)
    img = vgrad((W, H), [
        (0.00, SKY_TOP),
        (0.42, SKY_MID),
        (0.60, SKY_LOW),
        (0.62, (214, 150, 120)),
        (1.00, (24, 30, 40)),
    ])
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Low sun with bloom, half-hidden behind the cloud bank. ---
    sun_x, sun_y = 712, 552
    glow_img, glow_mask = radial_glow((560, 560), (255, 196, 120), inner=0.9)
    img.paste(ImageChops.screen(img.crop(
        (sun_x - 280, sun_y - 280, sun_x + 280, sun_y + 280)),
        glow_img), (sun_x - 280, sun_y - 280), glow_mask)
    # Soft-edged disc so the sun glows instead of sitting like a coin.
    sun_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sun_layer).ellipse(
        [sun_x - 46, sun_y - 46, sun_x + 46, sun_y + 46],
        fill=SUN_CORE + (255,))
    sun_layer = sun_layer.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(img.convert("RGBA"), sun_layer)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Far hazy ridge, softened by distance. ---
    ridge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ridge)
    pts = [(0, 700)]
    x = 0
    while x <= W:
        pts.append((x, 640 + rng.uniform(-14, 14)))
        x += 64
    pts += [(W, 700), (W, H), (0, H)]
    rd.polygon(pts, fill=VALLEY_FAR + (255,))
    ridge = ridge.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), ridge)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Cloud bank the falls rise into (y ~470-620). ---
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for _ in range(46):
        cx = rng.uniform(60, W - 60)
        cy = rng.uniform(470, 610)
        rx = rng.uniform(60, 170)
        ry = rng.uniform(16, 42)
        shade = rng.choice([(235, 225, 245), (216, 200, 232), (244, 214, 196)])
        cd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                   fill=shade + (rng.randint(130, 185),))
    clouds = clouds.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, clouds)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- The rising falls: luminous column + two side streams. ---
    def stream(cx0, top, bottom, width, brightness):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        phase = rng.uniform(0, 6.28)
        for y in range(top, bottom, 4):
            t = (y - top) / max(bottom - top, 1)
            sway = math.sin(y / 170.0 + phase) * 26 * (1.0 - t * 0.5)
            wob = math.sin(y / 53.0 + phase * 2) * 8
            w = width * (0.55 + 0.45 * (1.0 - t)) + wob
            cx = cx0 + sway
            alpha = int(brightness * (0.55 + 0.45 * math.sin(t * math.pi)))
            ld.line([(cx - w / 2, y), (cx + w / 2, y)],
                    fill=FALL_CORE + (alpha,), width=4)
            ld.line([(cx - w / 2 - 14, y), (cx + w / 2 + 14, y)],
                    fill=FALL_EDGE + (int(alpha * 0.6),), width=4)
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        # Three bright threads inside the band, so it reads as flowing
        # water instead of one thin line.
        core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd2 = ImageDraw.Draw(core)
        for off, al in ((-20, 0.55), (0, 0.95), (20, 0.55)):
            for y in range(top, bottom, 3):
                t = (y - top) / max(bottom - top, 1)
                sway = math.sin(y / 170.0 + phase) * 26 * (1.0 - t * 0.5)
                cd2.line([(cx0 + sway + off - 6, y), (cx0 + sway + off + 6, y)],
                         fill=(255, 255, 255, int(brightness * al)), width=3)
        core = core.filter(ImageFilter.GaussianBlur(2))
        return Image.alpha_composite(layer, core)

    img = Image.alpha_composite(img, stream(512, 448, 948, 150, 245))
    img = Image.alpha_composite(img, stream(330, 580, 930, 56, 150))
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Spray and drifting mist where the column meets the clouds. ---
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for _ in range(26):
        cx = rng.uniform(400, 624)
        cy = rng.uniform(430, 500)
        rx = rng.uniform(30, 90)
        ry = rng.uniform(10, 26)
        md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                   fill=(240, 238, 255, rng.randint(60, 110)))
    mist = mist.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, mist)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Near valley slopes framing the falls (dark teal). ---
    slopes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(slopes)
    left = [(0, H), (0, 742)]
    x = 0
    while x <= 400:
        left.append((x, 742 - (x / 400.0) * 130 + rng.uniform(-22, 22)))
        x += 40
    left += [(430, 948), (380, H)]
    sd.polygon(left, fill=(20, 56, 60, 255))
    right = [(W, H), (W, 760)]
    x = W
    while x >= 624:
        right.append((x, 760 - ((W - x) / 400.0) * 150 + rng.uniform(-22, 22)))
        x -= 40
    right += [(600, 952), (648, H)]
    sd.polygon(right, fill=(20, 56, 60, 255))
    slopes = slopes.filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img, slopes)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Mirror pool at the foot of the falls (foreground). ---
    pool = Image.new("RGB", (W, 190), POOL_DARK)
    pd = ImageDraw.Draw(pool)
    for y in range(190):
        t = y / 189.0
        pd.line([(0, y), (W, y)],
                fill=lerp((16, 34, 44), (52, 40, 66), t))
    # Reflection of the falls: bright vertical streak, blurred.
    refl = Image.new("RGBA", (W, 190), (0, 0, 0, 0))
    rfd = ImageDraw.Draw(refl)
    for y in range(0, 190, 3):
        wob = math.sin(y / 40.0) * 10
        rfd.line([(512 - 34 + wob, y), (512 + 34 + wob, y)],
                 fill=(220, 226, 255, int(150 * (1 - y / 190.0))), width=3)
    refl = refl.filter(ImageFilter.GaussianBlur(4))
    pool = Image.alpha_composite(pool.convert("RGBA"), refl)
    img.paste(pool.convert("RGB"), (0, H - 190))
    draw = ImageDraw.Draw(img, "RGBA")
    # Ripple lines on the pool (dim, short — they read as scratches if loud).
    for _ in range(14):
        y = rng.uniform(H - 180, H - 12)
        x0 = rng.uniform(60, 700)
        ln = rng.uniform(30, 90)
        draw.line([(x0, y), (x0 + ln, y)],
                  fill=(200, 205, 235, rng.randint(18, 45)), width=2)

    # --- Grain (fixed-seed) + vignette for texture, not flat vector. ---
    # Soft grain: a small noise tile upscaled (smooth, PNG-friendly) at low
    # amplitude. Full-resolution noise would blow the 1 MiB gate.
    img = img.convert("RGB")
    small = Image.frombytes("L", (512, 512), rng.randbytes(512 * 512))
    noise = small.resize((W, H), Image.BICUBIC).point(
        lambda v: 128 + (v - 128) // 16)
    img = ImageChops.add(img, Image.merge("RGB", (noise, noise, noise)),
                         scale=1, offset=-128)
    # Re-tone: pull the added grey back toward the scene (soft light feel).
    img = Image.blend(img, img.filter(ImageFilter.GaussianBlur(1)), 0.35)
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, W + 220, H + 220], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    black = Image.new("RGB", (W, H), (8, 6, 18))
    img = Image.composite(img, black, vig)
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Type: name carries the mood (ivory + gold glow), tagline below. ---
    img = img.convert("RGBA")
    name_font = find_font(bold=True, size=118)
    tag_font = find_font(bold=False, size=30)
    # Glow pass behind the name.
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    draw_tracked(gd, W / 2, 108, "AERFALL", name_font,
                 fill=(255, 214, 140, 255), tracking=0.16)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_tracked(draw, W / 2, 108, "AERFALL", name_font, fill=INK + (255,),
                 tracking=0.16)
    # Gold rule.
    draw.line([(W / 2 - 150, 252), (W / 2 + 150, 252)], fill=GOLD + (255,),
              width=3)
    draw_tracked(draw, W / 2, 272, "WHERE THE FALLS RISE INTO THE CLOUDS",
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
