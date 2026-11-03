#!/usr/bin/env python3
"""Generate the HUD damage schema (MEC-55) into pack/ and its glyph table
into ui/schemafont.tc.

    python3 pack/src/schema_assets.py

Needs Pillow. Each class gets a paper-doll schema, one glyph per part in
display order (hull, torso, main gun, secondary gun, augment modules 1 and 2,
then thigh and shin per leg), drawn white so the HUD marker color tints it
by HP. Seen from the pilot's seat: the mech's left is on the left. Plus the
shield bar (Electrostatic Dome charge): a frame glyph and fill glyphs for
10..100%.

The schema hangs below the HUD's top-right anchor: a bitmap glyph can only
rise by its own height (ascent <= height), so every glyph bakes its vertical
place into its ascent, TOP canvas units below the anchor. Horizontal places
are laid out by the server with spacing glyphs, from the table.
"""

import json
import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_assets import render, save  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "pack" / "assets"
TC_OUT = ROOT / "ui" / "schemafont.tc"

TEXELS = 3      # texels per canvas unit
PAD = 1         # transparent margin, canvas units, on every side
TOP = 150       # schema top, canvas units below the anchor
WIDTH = 72      # schema width, canvas units
BASE = 0xE100   # first code point; class k part i = BASE + 32 k + i
SHIELD = 0xE1F0  # frame; fills at SHIELD + 1 .. SHIELD + 10
SHIELD_RECT = (-12, 12, 6, 60)  # x (from the schema's left edge), y, w, h

CLASSES = ["walker", "sprinter", "crawler", "spider"]


def legs_rows(rows, left_shin_x, left_thigh_x, right_thigh_x, right_shin_x, w_thigh, w_shin, h):
    """Thigh and shin rects of side-by-side legs, one row per left/right
    pair, in leg order (left, right, left, right, ...)."""
    out = []
    for y in rows:
        out += [(left_thigh_x, y, w_thigh, h), (left_shin_x, y, w_shin, h)]
        out += [(right_thigh_x, y, w_thigh, h), (right_shin_x, y, w_shin, h)]
    return out


# Part rects (x, y, w, h) in schema units, display order. Guns: the main gun
# is on the mech's right on bipeds, centered on crawlers and spiders; the
# secondary on the left.
LAYOUTS = {
    "walker": [
        (18, 22, 36, 22), (20, 0, 32, 18), (56, 2, 10, 30), (6, 2, 10, 30), (6, 34, 10, 10), (56, 34, 10, 10),
        (20, 48, 12, 17), (20, 67, 12, 17), (40, 48, 12, 17), (40, 67, 12, 17),
    ],
    "sprinter": [
        (22, 20, 28, 20), (24, 0, 24, 16), (52, 2, 8, 26), (12, 2, 8, 26), (10, 30, 9, 9), (53, 30, 9, 9),
        (24, 44, 9, 19), (24, 65, 9, 19), (39, 44, 9, 19), (39, 65, 9, 19),
    ],
    "crawler": [
        (14, 36, 44, 18), (20, 18, 32, 14), (31, 0, 10, 16), (6, 16, 10, 16), (2, 38, 10, 12), (60, 38, 10, 12),
        *legs_rows([58, 67, 76], 0, 16, 42, 58, 14, 14, 8),
    ],
    "spider": [
        (20, 34, 32, 16), (24, 20, 24, 12), (31, 0, 10, 18), (10, 18, 10, 12), (6, 36, 10, 10), (56, 36, 10, 10),
        *legs_rows([54, 68], 0, 18, 40, 56, 14, 16, 12),
    ],
}


def part_glyph(w: int, h: int, fill_alpha: int = 150):
    """A rounded part plate: translucent fill, bright outline, w x h units."""
    size = ((w + 2 * PAD) * TEXELS, (h + 2 * PAD) * TEXELS)

    def draw(d: ImageDraw.ImageDraw, s: int):
        m = PAD * TEXELS * s
        box = (m, m, size[0] * s - m - 1, size[1] * s - m - 1)
        r = min(2 * TEXELS * s, (box[2] - box[0]) // 3, (box[3] - box[1]) // 3)
        d.rounded_rectangle(box, r, fill=(255, 255, 255, fill_alpha), outline=(255, 255, 255, 255), width=TEXELS * s // 2 + s)

    return render(size, draw)


def advance(img, height_units: int) -> int:
    """BitmapProvider advance: (int)(0.5 + content width * scale) + 1."""
    scale = height_units / img.height
    cols = [x for x in range(img.width) if any(img.getpixel((x, y))[3] for y in range(img.height))]
    return int(0.5 + (cols[-1] + 1) * scale) + 1


def provider(file: str, ch: int, height: int, top: int) -> dict:
    """Bitmap provider for one glyph whose top edge (with its margin) is
    `top` units below the line: the glyph top lands at 7 - ascent."""
    return {"type": "bitmap", "file": file, "height": height, "ascent": 7 - top, "chars": [chr(ch)]}


def main() -> None:
    providers = []
    table = {}
    for k, cls in enumerate(CLASSES):
        rows = []
        for i, (x, y, w, h) in enumerate(LAYOUTS[cls]):
            img = part_glyph(w, h)
            rel = f"mech/textures/font/schema/{cls}_{i}.png"
            save(img, rel)
            ch = BASE + 32 * k + i
            providers.append(provider(f"mech:font/schema/{cls}_{i}.png", ch, h + 2 * PAD, TOP + y - PAD))
            rows.append((ch, x - PAD, advance(img, h + 2 * PAD)))
        table[cls] = rows

    sx, sy, sw, sh = SHIELD_RECT
    frame = part_glyph(sw, sh, fill_alpha=40)
    save(frame, "mech/textures/font/schema/shield_frame.png")
    providers.append(provider("mech:font/schema/shield_frame.png", SHIELD, sh + 2 * PAD, TOP + sy - PAD))
    shield = [(SHIELD, sx - PAD, advance(frame, sh + 2 * PAD))]
    for n in range(1, 11):
        fh = max(1, round(sh * n / 10))
        img = part_glyph(sw - 2, fh, fill_alpha=255)
        save(img, f"mech/textures/font/schema/shield_{n}.png")
        providers.append(provider(f"mech:font/schema/shield_{n}.png", SHIELD + n, fh + 2 * PAD, TOP + sy + sh - fh - PAD))
        shield.append((SHIELD + n, sx + 1 - PAD, advance(img, fh + 2 * PAD)))

    font = ASSETS / "mech" / "font" / "schema.json"
    font.write_text(json.dumps({"providers": providers}, indent=2, ensure_ascii=True) + "\n")

    def tc_rows(rows):
        return ", ".join(f'["\\u{ch:04X}", {x}, {adv}]' for ch, x, adv in rows)

    lines = [
        "// Generated by pack/src/schema_assets.py; do not edit.",
        "// Damage schema glyphs (font mech:schema): [char, x, advance] in canvas units,",
        f"// x from the schema's left edge; the schema is {WIDTH} units wide and its",
        f"// glyphs sit {TOP} units below the HUD anchor (baked into their ascent).",
        "",
        "/** Schema glyphs of class cls, one per part in display order. */",
        "function schemaGlyphs(cls: str): list {",
    ]
    for cls in CLASSES:
        lines += [f'    if (cls == "{cls}") {{', f"        return [{tc_rows(table[cls])}];", "    }"]
    lines += [
        "    return [];",
        "}",
        "",
        "/** Shield bar glyphs: [frame, 10%, 20%, ..., 100%], each [char, x, advance]. */",
        "function shieldGlyphs(): list {",
        f"    return [{tc_rows(shield)}];",
        "}",
        "",
        "/** Schema width in canvas units. */",
        "function schemaWidth(): num {",
        f"    return {WIDTH};",
        "}",
        "",
    ]
    TC_OUT.write_text("\n".join(lines))
    print(f"schema: {sum(len(v) for v in LAYOUTS.values())} part glyphs, 11 shield glyphs -> {TC_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
