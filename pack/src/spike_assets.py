#!/usr/bin/env python3
"""Generate the Stage 1 pack spike assets (MEC-17) into pack/assets/.

    python3 pack/src/spike_assets.py

Needs Pillow and ffmpeg (with libvorbis). Writes:
  mech:item/test_part texture   placeholder part: tinted arm, joint housing, light strips
  mech:font/panel, cursor       glyph bitmaps for font mech:ui
  mech:test/beep.ogg            sound event mech:test.beep
  minecraft boss_bar sprites    all transparent, so boss bars show only their text
  minecraft hud sprites         hotbar and crosshair, all transparent
The JSON files (item definition, model, font, sounds.json) are written by hand
and live next to these in pack/assets/.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Reserved alphas for emissive pixels, read by core/item.fsh (PLAN.md, Model
# rules): 250 full bright, 251 full bright and pulsing. Any alpha other than
# 0/255 sends the face to the translucent item pipeline, so marked pixels sit
# on their own faces.
EMISSIVE_ALPHA = 250
EMISSIVE_PULSE_ALPHA = 251

BOSS_BAR_SPRITES = [
    f"{color}_{part}"
    for color in ("blue", "green", "pink", "purple", "red", "white", "yellow",
                  "notched_6", "notched_10", "notched_12", "notched_20")
    for part in ("background", "progress")
]


def save(img: Image.Image, rel: str) -> None:
    path = ASSETS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def test_part() -> None:
    """256x256 sheet (16 texels per model unit). Regions in model units
    (x0, y0, x1, y1), times 16 in texels:
    (0,0,3,16) arm sides, brushed metal, tinted by custom model data color 0;
    (4,0,10,6) joint housing; (10,0,12,6) shader emissive strip, alpha 250 on
    top and 251 (pulsing) below; (12,0,14,6) light_emission comparison
    strip; (4,6,7,9) arm end cap."""
    import random

    rng = random.Random(7)
    k = 16
    img = Image.new("RGBA", (16 * k, 16 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Arm: brushed metal (fine vertical streaks), darker toward the edges.
    w = 3 * k
    for x in range(w):
        edge = abs(x - (w - 1) / 2) / ((w - 1) / 2)
        base = 214 - 38 * edge ** 2 + rng.uniform(-6, 6)
        for y in range(16 * k):
            v = int(base + rng.uniform(-3, 3))
            img.putpixel((x, y), (v, v, min(255, v + 4), 255))
    for py in (3 * k, 8 * k, 13 * k):  # panel seams with a lit lower lip
        d.rectangle((0, py - 1, w - 1, py), fill=(118, 120, 126, 255))
        d.line((0, py + 1, w - 1, py + 1), fill=(236, 238, 242, 255))
        for bx in (8, w - 9):  # bolts
            d.ellipse((bx - 3, py + 6, bx + 3, py + 12), fill=(150, 152, 158, 255), outline=(96, 98, 104, 255))

    # Joint housing: gunmetal with a machined ring and a hub.
    jx0, jy0, jx1, jy1 = 4 * k, 0, 10 * k, 6 * k
    for y in range(jy0, jy1):
        t = (y - jy0) / (jy1 - jy0)
        v = int(78 - 22 * t)
        d.line((jx0, y, jx1 - 1, y), fill=(v, v, v + 6, 255))
    cx, cy, r = (jx0 + jx1) / 2, (jy0 + jy1) / 2, 2.3 * k
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(132, 136, 146, 255), width=5)
    d.ellipse((cx - r + 9, cy - r + 9, cx + r - 9, cy + r - 9), fill=(44, 45, 50, 255))
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(110, 112, 120, 255), outline=(160, 164, 172, 255), width=2)
    d.rectangle((jx0, jy0, jx1 - 1, jy1 - 1), outline=(104, 106, 114, 255), width=3)

    # Shader strip: steady cyan (250) on top, pulsing amber (251) below.
    sx0, sx1 = 10 * k, 12 * k
    for y in range(0, 3 * k):
        glow = 1.0 - abs(((y % k) / k) - 0.5) * 0.4
        d.line((sx0, y, sx1 - 1, y), fill=(int(70 * glow), int(225 * glow), int(255 * glow), EMISSIVE_ALPHA))
    for y in range(3 * k, 6 * k):
        d.line((sx0, y, sx1 - 1, y), fill=(255, 130, 50, EMISSIVE_PULSE_ALPHA))

    # light_emission comparison strip (plain opaque orange).
    d.rectangle((12 * k, 0, 14 * k - 1, 6 * k - 1), fill=(255, 150, 40, 255))

    # End cap.
    d.rectangle((4 * k, 6 * k, 7 * k - 1, 9 * k - 1), fill=(186, 188, 194, 255), outline=(140, 142, 148, 255), width=3)
    save(img, "mech/textures/item/test_part.png")


# UI glyphs are high resolution: drawn at SUPERSAMPLE x and downsampled, a
# few texels per canvas unit, with a transparent MARGIN so the text shader's
# filtered sampling never reaches a neighbouring glyph in the font atlas.
# A glyph image must stay under 255 px a side (FontTexture pages are 256 px
# with 1 px spacing); larger art is split into several glyphs.
SUPERSAMPLE = 4
MARGIN = 2


def render(size: tuple[int, int], draw_fn) -> Image.Image:
    """Draws at SUPERSAMPLE x with draw_fn(draw, scale), then downsamples
    with premultiplied alpha so edges do not darken."""
    big = Image.new("RGBA", (size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), SUPERSAMPLE)
    return big.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def glyph_layout(img: Image.Image, height: int, ascent: int) -> dict:
    """Where a single glyph lands in canvas units, as Minecraft lays it out:
    BitmapProvider scale and advance, a one-line text display (x from
    1 - width / 2, y from -9) and the glyph top at 7 - ascent."""
    scale = height / img.height
    cols = [x for x in range(img.width) if any(img.getpixel((x, y))[3] for y in range(img.height))]
    advance = int(0.5 + (cols[-1] + 1) * scale) + 1
    x0 = 1 - advance / 2
    y0 = -9 + 7 - ascent
    return {"scale": scale, "advance": advance, "x0": x0, "y0": y0}


def glyphs() -> None:
    # Panel: 64 x 32 canvas units at 3.94 texels per unit (252 x 126 px).
    pw, ph = 252, 126

    def panel_fn(d, s):
        m = MARGIN * s
        box = (m, m, pw * s - m - 1, ph * s - m - 1)
        radius = 10 * s
        # Vertical gradient fill, clipped to the rounded rectangle.
        fill = Image.new("RGBA", (pw * s, ph * s), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fill)
        for y in range(ph * s):
            t = y / (ph * s)
            fd.line([(0, y), (pw * s, y)], fill=(int(16 - 6 * t), int(30 - 10 * t), int(44 - 12 * t), int(205 + 30 * t)))
        mask = Image.new("L", (pw * s, ph * s), 0)
        ImageDraw.Draw(mask).rounded_rectangle(box, radius, fill=255)
        d._image.paste(fill, (0, 0), mask)
        # Soft inner glow along the top edge.
        d.rounded_rectangle((box[0] + 3 * s, box[1] + 3 * s, box[2] - 3 * s, box[1] + 18 * s), 7 * s, fill=(120, 220, 255, 22))
        # Border, then brighter corner brackets.
        d.rounded_rectangle(box, radius, outline=(110, 215, 255, 235), width=2 * s)
        arm = 22 * s
        w = 3 * s
        bright = (225, 248, 255, 255)
        for cx, sx in ((box[0], 1), (box[2], -1)):
            for cy, sy in ((box[1], 1), (box[3], -1)):
                d.line([(cx + sx * radius, cy), (cx + sx * (radius + arm), cy)], fill=bright, width=w)
                d.line([(cx, cy + sy * radius), (cx, cy + sy * (radius + arm // 2))], fill=bright, width=w)
                d.arc((min(cx, cx + sx * 2 * radius), min(cy, cy + sy * 2 * radius),
                       max(cx, cx + sx * 2 * radius), max(cy, cy + sy * 2 * radius)),
                      {(1, 1): 180, (-1, 1): 270, (-1, -1): 0, (1, -1): 90}[(sx, sy)],
                      {(1, 1): 270, (-1, 1): 360, (-1, -1): 90, (1, -1): 180}[(sx, sy)],
                      fill=bright, width=w)

    panel = render((pw, ph), panel_fn)
    save(panel, "mech/textures/font/panel.png")

    # Cursor: 12 x 12 canvas units at 8 texels per unit (96 x 96 px), tip at
    # texel (MARGIN, MARGIN).
    cs = 96

    def cursor_fn(d, s):
        tip = (MARGIN * s, MARGIN * s)
        pts = [(0, 0), (0, 64), (17, 49), (29, 76), (41, 70), (29, 44), (51, 44)]
        poly = [(tip[0] + x * s, tip[1] + y * s) for x, y in pts]
        shadow = [(x + 3 * s, y + 4 * s) for x, y in poly]
        d.polygon(shadow, fill=(0, 0, 0, 90))
        d.polygon(poly, fill=(245, 250, 255, 255), outline=(10, 18, 26, 255), width=3 * s)

    cursor = render((cs, cs), cursor_fn)
    save(cursor, "mech/textures/font/cursor.png")

    # Layout facts the DF code depends on (spike/pack.tc).
    pl = glyph_layout(panel, 32, 16)
    left, top = pl["x0"] + MARGIN * pl["scale"], pl["y0"] + MARGIN * pl["scale"]
    right, bottom = pl["x0"] + (pw - MARGIN) * pl["scale"], pl["y0"] + (ph - MARGIN) * pl["scale"]
    print(f"panel: visible rect x {left:.3f}..{right:.3f}, y {top:.3f}..{bottom:.3f} canvas units")
    cl = glyph_layout(cursor, 12, 12)
    tip_x, tip_y = cl["x0"] + MARGIN * cl["scale"], cl["y0"] + MARGIN * cl["scale"]
    print(f"cursor: tip at canvas {tip_x:.4f}, {tip_y:.4f}; display translation "
          f"x {-tip_x / 40:.5f}, y {tip_y / 40:.5f} blocks")


# Vanilla HUD sprites made transparent, with their sizes (gui/sprites/hud):
# the hotbar, and the crosshair (combat draws its own).
HOTBAR_SPRITES = {
    "crosshair": (15, 15),
    "crosshair_attack_indicator_background": (16, 4),
    "crosshair_attack_indicator_full": (16, 16),
    "crosshair_attack_indicator_progress": (16, 4),
    "hotbar": (182, 22),
    "hotbar_selection": (24, 23),
    "hotbar_offhand_left": (29, 24),
    "hotbar_offhand_right": (29, 24),
    "hotbar_attack_indicator_background": (18, 18),
    "hotbar_attack_indicator_progress": (18, 18),
}


def hotbar() -> None:
    for name, size in HOTBAR_SPRITES.items():
        save(Image.new("RGBA", size, (0, 0, 0, 0)), f"minecraft/textures/gui/sprites/hud/{name}.png")


def boss_bars() -> None:
    blank = Image.new("RGBA", (182, 5), (0, 0, 0, 0))
    for name in BOSS_BAR_SPRITES:
        save(blank, f"minecraft/textures/gui/sprites/boss_bar/{name}.png")


def beep() -> None:
    out = ASSETS / "mech/sounds/test/beep.ogg"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=880:duration=0.25",
         "-af", "afade=t=in:d=0.01,afade=t=out:st=0.2:d=0.05", "-ac", "1", "-ar", "44100",
         "-c:a", "libvorbis", "-q:a", "4", "-fflags", "+bitexact", "-map_metadata", "-1", str(out)],
        check=True,
    )


if __name__ == "__main__":
    test_part()
    glyphs()
    boss_bars()
    hotbar()
    beep()
    print(f"wrote spike assets under {ASSETS}")
