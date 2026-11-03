#!/usr/bin/env python3
"""Generate the cockpit HUD art (MEC-54) into pack/ and its glyph table into
ui/cockpitfont.tc.

    python3 pack/src/cockpit_assets.py

Needs Pillow. All art is white line work with a soft glow; the HUD marker
color tints it.

  mech:cockpit   frame corners per class (4 per class: top-left, top-right,
                 bottom-left, bottom-right, at the screen corners) and one
                 crosshair per gun (centered on the screen center)
  mech:reticle   the gun reticle, centered on its text display's origin

HUD glyphs bake their vertical place into the ascent (ascent <= height, so
a glyph rises at most its own height above the line). Bottom corners
therefore sit BOTTOM_DROP units low: their art keeps that much empty space
at the bottom.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_assets import render, save  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "pack" / "assets"
TC_OUT = ROOT / "ui" / "cockpitfont.tc"

PAD = 1
FRAME_W, FRAME_H, FRAME_TX = 112, 80, 2
BOTTOM_DROP = 8
CROSS, CROSS_TX = 32, 4
RETICLE, RETICLE_TX = 24, 4
FRAME_BASE = 0xE200   # class k corner j = FRAME_BASE + 4 k + j
CROSS_BASE = 0xE240   # gun g = CROSS_BASE + g
RETICLE_CH = 0xE260

CLASSES = ["walker", "sprinter", "crawler", "spider"]
GUNS = ["railgun", "autocannon", "lmg", "cal50", "grenade", "burst"]

# Frame struts per class, as polylines in units from the top-left screen
# corner (x right, y down); mirrored for the other corners.
STRUTS = {
    "walker": [[(0, 74), (22, 46), (27, 0)], [(27, 10), (104, 10)], [(22, 46), (40, 46)]],
    "sprinter": [[(0, 52), (38, 14), (110, 14)], [(38, 14), (44, 0)]],
    "crawler": [[(0, 30), (72, 30), (92, 20), (110, 20)], [(0, 42), (56, 42)], [(72, 30), (72, 0)]],
    "spider": [[(0, 62), (18, 34), (18, 14), (34, 0)], [(18, 34), (48, 34)], [(18, 14), (60, 14)]],
}


def glow_lines(d, s, tx, lines, offset):
    """Holographic line: a wide faint glow, then a thin bright core."""
    for width, alpha in ((7, 45), (4, 90), (1.6, 255)):
        for pts in lines:
            xy = [((x + offset[0]) * tx * s, (y + offset[1]) * tx * s) for x, y in pts]
            d.line(xy, fill=(255, 255, 255, alpha), width=max(1, int(width * s)), joint="curve")


def frame_corner(cls: str, corner: int):
    """corner 0 top-left, 1 top-right, 2 bottom-left, 3 bottom-right."""
    w, h = FRAME_W + 2 * PAD, FRAME_H + 2 * PAD + (BOTTOM_DROP if corner >= 2 else 0)
    lines = []
    for pts in STRUTS[cls]:
        out = []
        for x, y in pts:
            if corner in (1, 3):
                x = FRAME_W - x
            if corner >= 2:
                y = FRAME_H - y
            out.append((x, y))
        lines.append(out)
    return render((w * FRAME_TX, h * FRAME_TX), lambda d, s: glow_lines(d, s, FRAME_TX, lines, (PAD, PAD))), h


def crosshair(gun: str):
    n = CROSS + 2 * PAD
    c = n / 2

    def draw(d, s):
        k = CROSS_TX * s

        def ln(pts, width=1.4):
            for wd, a in ((width * 3, 60), (width, 255)):
                d.line([(x * k, y * k) for x, y in pts], fill=(255, 255, 255, a), width=max(1, int(wd * s)))

        def circle(r, width=1.2, dashes=0):
            box = ((c - r) * k, (c - r) * k, (c + r) * k, (c + r) * k)
            if dashes:
                step = 360 / dashes
                for i in range(dashes):
                    d.arc(box, i * step, i * step + step * 0.55, fill=(255, 255, 255, 255), width=max(1, int(width * k / 2)))
            else:
                d.ellipse(box, outline=(255, 255, 255, 255), width=max(1, int(width * k / 2)))

        if gun == "railgun":
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ln([(c + dx * 3, c + dy * 3), (c + dx * 11, c + dy * 11)])
            d.ellipse(((c - 0.8) * k, (c - 0.8) * k, (c + 0.8) * k, (c + 0.8) * k), fill=(255, 255, 255, 255))
        elif gun == "autocannon":
            circle(7)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ln([(c + dx * 8.5, c + dy * 8.5), (c + dx * 12, c + dy * 12)])
        elif gun == "lmg":
            circle(11, dashes=12)
            d.ellipse(((c - 0.8) * k, (c - 0.8) * k, (c + 0.8) * k, (c + 0.8) * k), fill=(255, 255, 255, 255))
        elif gun == "cal50":
            ln([(c - 6, c + 2), (c, c + 7), (c + 6, c + 2)])
            d.ellipse(((c - 0.8) * k, (c - 0.8) * k, (c + 0.8) * k, (c + 0.8) * k), fill=(255, 255, 255, 255))
        elif gun == "grenade":
            ln([(c, c + 2), (c, c + 13)], 1.0)
            for i, y in enumerate((4, 8, 12)):
                half = 5 - i
                ln([(c - half, c + y), (c + half, c + y)])
            ln([(c - 4, c), (c + 4, c)])
        else:  # burst: four corner brackets
            for sx in (-1, 1):
                for sy in (-1, 1):
                    ln([(c + sx * 9, c + sy * 4), (c + sx * 9, c + sy * 9), (c + sx * 4, c + sy * 9)])

    return render((n * CROSS_TX, n * CROSS_TX), draw)


def reticle():
    n = RETICLE + 2 * PAD
    c = n / 2

    def draw(d, s):
        k = RETICLE_TX * s
        pts = [(c, c - 6), (c + 6, c), (c, c + 6), (c - 6, c)]
        for wd, a in ((4.0, 60), (1.4, 255)):
            for i in range(4):
                a0, b0 = pts[i], pts[(i + 1) % 4]
                mx, my = (a0[0] * 0.35 + b0[0] * 0.65), (a0[1] * 0.35 + b0[1] * 0.65)
                d.line([(a0[0] * k, a0[1] * k), (mx * k, my * k)], fill=(255, 255, 255, a), width=max(1, int(wd * s)))

    return render((n * RETICLE_TX, n * RETICLE_TX), draw)


def advance(img, height_units: int) -> int:
    """BitmapProvider advance: (int)(0.5 + content width * scale) + 1."""
    scale = height_units / img.height
    cols = [x for x in range(img.width) if any(img.getpixel((x, y))[3] for y in range(img.height))]
    return int(0.5 + (cols[-1] + 1) * scale) + 1


def main() -> None:
    cockpit, table_frames, table_cross = [], {}, []
    for k, cls in enumerate(CLASSES):
        rows = []
        for j in range(4):
            img, h = frame_corner(cls, j)
            save(img, f"mech/textures/font/cockpit/{cls}_{j}.png")
            ch = FRAME_BASE + 4 * k + j
            # Top corners: glyph top PAD above the screen top. Bottom corners
            # sit as low as a glyph may (ascent = height): BOTTOM_DROP of
            # their art is the empty space below the screen.
            ascent = 7 + PAD if j < 2 else h
            cockpit.append({"type": "bitmap", "file": f"mech:font/cockpit/{cls}_{j}.png",
                            "height": h, "ascent": ascent, "chars": [chr(ch)]})
            x = -PAD if j in (0, 2) else -(FRAME_W + PAD)
            rows.append((ch, x, advance(img, h)))
        table_frames[cls] = rows
    n = CROSS + 2 * PAD
    for g, gun in enumerate(GUNS):
        img = crosshair(gun)
        save(img, f"mech/textures/font/cockpit/cross_{gun}.png")
        ch = CROSS_BASE + g
        # Centered: glyph top n/2 above the line.
        cockpit.append({"type": "bitmap", "file": f"mech:font/cockpit/cross_{gun}.png",
                        "height": n, "ascent": 7 + n // 2, "chars": [chr(ch)]})
        table_cross.append((gun, ch, -n // 2, advance(img, n)))
    (ASSETS / "mech" / "font" / "cockpit.json").write_text(json.dumps({"providers": cockpit}, indent=2, ensure_ascii=True) + "\n")

    rn = RETICLE + 2 * PAD
    save(reticle(), "mech/textures/font/cockpit/reticle.png")
    # Text display line: glyph top at -2 - ascent from the origin; center it.
    (ASSETS / "mech" / "font" / "reticle.json").write_text(json.dumps({"providers": [
        {"type": "bitmap", "file": "mech:font/cockpit/reticle.png", "height": rn, "ascent": rn // 2 - 2,
         "chars": [chr(RETICLE_CH)]}]}, indent=2, ensure_ascii=True) + "\n")

    def row(ch, x, adv):
        return f'["\\u{ch:04X}", {x}, {adv}]'

    lines = [
        "// Generated by pack/src/cockpit_assets.py; do not edit.",
        "// Cockpit glyphs (font mech:cockpit): [char, x, advance] in canvas units from",
        "// their anchor; vertical places are baked into the glyphs.",
        "",
        "/** Frame corners of class cls: top-left, top-right, bottom-left,",
        " * bottom-right (anchors 0, 2, 6, 8). */",
        "function frameGlyphs(cls: str): list {",
    ]
    for cls in CLASSES:
        lines += [f'    if (cls == "{cls}") {{', f"        return [{', '.join(row(*r) for r in table_frames[cls])}];", "    }"]
    lines += ["    return [];", "}", "", "/** Crosshair of gun id (anchor 4), or the railgun's for an unknown gun. */",
              "function crosshairGlyph(gun: str): list {"]
    for gun, ch, x, adv in table_cross[1:]:
        lines += [f'    if (gun == "{gun}") {{', f"        return {row(ch, x, adv)};", "    }"]
    gun, ch, x, adv = table_cross[0]
    lines += [f"    return {row(ch, x, adv)};", "}", "", "/** The gun reticle glyph (font mech:reticle). */",
              "function reticleChar(): str {", f'    return "\\u{RETICLE_CH:04X}";', "}", ""]
    TC_OUT.write_text("\n".join(lines))
    print(f"cockpit: {len(cockpit)} glyphs + reticle -> {TC_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
