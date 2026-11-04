#!/usr/bin/env python3
"""Generate the HUD minimap art (MEC-57) into pack/ and its glyph table into
ui/minimapfont.tc.

    python3 pack/src/minimap_assets.py

Needs Pillow. All art is white; the HUD marker color tints it.

  frame    the round minimap: translucent disc, grid and rim (the map's
           top-down image replaces the disc with MEC-64)
  dots     a party dot for every canvas unit of height across the disc,
           font mech:minimap/d<j> (j = 0 .. 2R): a bitmap glyph's height on
           screen is baked into its ascent, so each height is its own font
           (one shared PNG)
  arrows   the player's heading in 16 directions (22.5 degrees apart) for
           every ARROW_STEP units of height, font mech:minimap/a<j>, char
           ARROW_BASE + k pointing along Minecraft yaw 22.5 k (yaw 0 = +Z =
           down on the map: north is up)

The minimap hangs below the HUD's top-left anchor like the schema: every
glyph's top is baked into its ascent (top lands at 7 - ascent). The canvas
is always 360 units tall, so CENTER_Y from the top is a fixed distance
above the bottom edge.
"""

import json
import math
import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_assets import render, save  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "pack" / "assets"
TC_OUT = ROOT / "ui" / "minimapfont.tc"

PAD = 1            # transparent margin, canvas units, on every side
R = 40             # disc radius, canvas units
# Disc center from the anchor (screen top-left), clear of every class's
# bottom-left cockpit frame strut (pack/src/cockpit_assets.py).
CENTER_X = 86
CENTER_Y = 270
FRAME_TX = 2       # frame texels per canvas unit
DOT = 4            # dot diameter, canvas units
DOT_TX = 4
ARROW = 10         # arrow size, canvas units
ARROW_TX = 3
ARROW_STEP = 2     # arrow heights every ARROW_STEP canvas units
FRAME_CH = 0xE300
DOT_CH = 0xE310
ARROW_BASE = 0xE3A0  # arrow k = ARROW_BASE + k


def advance(img, height_units: int) -> int:
    """BitmapProvider advance: (int)(0.5 + content width * scale) + 1."""
    scale = height_units / img.height
    cols = [x for x in range(img.width) if any(img.getpixel((x, y))[3] for y in range(img.height))]
    return int(0.5 + (cols[-1] + 1) * scale) + 1


def provider(file: str, ch: int, height: int, top: float) -> dict:
    """Bitmap provider for one glyph whose top edge (with its margin) is
    `top` units below the line: the glyph top lands at 7 - ascent."""
    return {"type": "bitmap", "file": file, "height": height, "ascent": 7 - round(top), "chars": [chr(ch)]}


def frame():
    n = 2 * (R + PAD)
    size = (n * FRAME_TX, n * FRAME_TX)

    def draw(d: ImageDraw.ImageDraw, s: int):
        k = FRAME_TX * s
        c = (R + PAD) * k
        r = R * k
        d.ellipse((c - r, c - r, c + r, c + r), fill=(255, 255, 255, 70))
        # Grid: two rings and the cross through the center.
        for f in (1 / 3, 2 / 3):
            q = r * f
            d.ellipse((c - q, c - q, c + q, c + q), outline=(255, 255, 255, 60), width=max(1, s))
        d.line((c - r, c, c + r, c), fill=(255, 255, 255, 60), width=max(1, s))
        d.line((c, c - r, c, c + r), fill=(255, 255, 255, 60), width=max(1, s))
        # Rim with a north tick.
        d.ellipse((c - r, c - r, c + r, c + r), outline=(255, 255, 255, 230), width=int(1.2 * k))
        d.polygon([(c - 2.5 * k, c - r + 0.5 * k), (c + 2.5 * k, c - r + 0.5 * k), (c, c - r + 4.5 * k)], fill=(255, 255, 255, 255))

    return render(size, draw)


def dot():
    n = DOT + 2 * PAD
    size = (n * DOT_TX, n * DOT_TX)

    def draw(d: ImageDraw.ImageDraw, s: int):
        k = DOT_TX * s
        m = PAD * k
        d.ellipse((m, m, m + DOT * k, m + DOT * k), fill=(255, 255, 255, 255))

    return render(size, draw)


def arrow(k: int):
    n = ARROW + 2 * PAD
    size = (n * ARROW_TX, n * ARROW_TX)
    yaw = math.radians(22.5 * k)
    # Map direction of yaw on screen (x right = +X, y down = +Z).
    fx, fy = -math.sin(yaw), math.cos(yaw)
    rx, ry = -fy, fx

    def draw(d: ImageDraw.ImageDraw, s: int):
        u = ARROW_TX * s
        c = n * u / 2
        half = ARROW / 2 * u
        tip = (c + fx * half, c + fy * half)
        back = (c - fx * half * 0.7, c - fy * half * 0.7)
        notch = (c - fx * half * 0.25, c - fy * half * 0.25)
        left = (back[0] + rx * half * 0.75, back[1] + ry * half * 0.75)
        right = (back[0] - rx * half * 0.75, back[1] - ry * half * 0.75)
        d.polygon([tip, left, notch, right], fill=(255, 255, 255, 255))

    return render(size, draw)


def main() -> None:
    providers = []
    out = ASSETS / "mech" / "textures" / "font" / "minimap"
    for old in out.glob("*.png") if out.exists() else []:
        old.unlink()
    fonts = ASSETS / "mech" / "font" / "minimap"
    fonts.mkdir(parents=True, exist_ok=True)
    for old in fonts.glob("*.json"):
        old.unlink()

    def write_font(path, provs):
        path.write_text(json.dumps({"providers": provs}, indent=2, ensure_ascii=True) + "\n")

    img = frame()
    save(img, "mech/textures/font/minimap/frame.png")
    fh = 2 * (R + PAD)
    providers.append(provider("mech:font/minimap/frame.png", FRAME_CH, fh, CENTER_Y - R - PAD))
    frame_row = (FRAME_CH, CENTER_X - R - PAD, advance(img, fh))

    img = dot()
    save(img, "mech/textures/font/minimap/dot.png")
    dh = DOT + 2 * PAD
    dot_adv = advance(img, dh)
    for j in range(2 * R + 1):
        write_font(fonts / f"d{j}.json",
                   [provider("mech:font/minimap/dot.png", DOT_CH, dh, CENTER_Y - R + j - DOT / 2 - PAD)])

    arrows = []
    ah = ARROW + 2 * PAD
    for k in range(16):
        img = arrow(k)
        save(img, f"mech/textures/font/minimap/arrow_{k}.png")
        arrows.append((ARROW_BASE + k, advance(img, ah)))
    steps = 2 * R // ARROW_STEP
    for j in range(steps + 1):
        top = CENTER_Y - R + j * ARROW_STEP - ah / 2
        write_font(fonts / f"a{j}.json",
                   [provider(f"mech:font/minimap/arrow_{k}.png", ARROW_BASE + k, ah, top) for k in range(16)])

    write_font(ASSETS / "mech" / "font" / "minimap.json", providers)

    def ch(c):
        return f'"\\u{c:04X}"'

    lines = [
        "// Generated by pack/src/minimap_assets.py; do not edit.",
        "// Minimap glyphs (font mech:minimap), hanging below the HUD's top-left",
        f"// anchor: a disc of radius {R} centered {CENTER_X} units right of and",
        f"// {CENTER_Y} units below the anchor. [char, x, advance] in canvas units.",
        "",
        "/** The minimap disc: [char, x, advance]. */",
        "function minimapFrame(): list {",
        f"    return [{ch(frame_row[0])}, {frame_row[1]}, {frame_row[2]}];",
        "}",
        "",
        f"/** The party dot: [char, diameter, advance]. Font mech:minimap/d<j> (j = 0",
        f" * .. {2 * R}) centers it {CENTER_Y - R} + j units below the anchor. */",
        "function minimapDot(): list {",
        f"    return [{ch(DOT_CH)}, {DOT}, {dot_adv}];",
        "}",
        "",
        "/** Heading arrows, entry k + 1 pointing along yaw 22.5 k: [char, advance].",
        f" * Font mech:minimap/a<j> (j = 0 .. {steps}) centers them {CENTER_Y - R} +",
        f" * {ARROW_STEP} j units below the anchor; each is {ah} units wide. */",
        "function minimapArrows(): list {",
        "    return [" + ", ".join(f"[{ch(c)}, {a}]" for c, a in arrows) + "];",
        "}",
        "",
        "/** Arrow height step and glyph width in canvas units: [step, width]. */",
        "function minimapArrowSize(): list {",
        f"    return [{ARROW_STEP}, {ah}];",
        "}",
        "",
        "/** Disc radius and center from the anchor: [radius, x, y]. */",
        "function minimapGeometry(): list {",
        f"    return [{R}, {CENTER_X}, {CENTER_Y}];",
        "}",
        "",
    ]
    TC_OUT.write_text("\n".join(lines))
    print(f"minimap: frame, {2 * R + 1} dot heights, {steps + 1} x {len(arrows)} arrows -> {TC_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
