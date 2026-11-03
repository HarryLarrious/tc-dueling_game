#!/usr/bin/env python3
"""Generate the Stage 1 pack spike assets (MEC-17) into pack/assets/.

    python3 pack/src/spike_assets.py

Needs Pillow and ffmpeg (with libvorbis). Writes:
  mech:item/test_part texture   placeholder part: tinted arm, joint housing, light strips
  mech:font/panel, cursor       glyph bitmaps for font mech:ui
  mech:test/beep.ogg            sound event mech:test.beep
  minecraft boss_bar sprites    all transparent, so boss bars show only their text
  minecraft hud hotbar sprites  all transparent, so the hotbar frame never shows
The JSON files (item definition, model, font, sounds.json) are written by hand
and live next to these in pack/assets/.
"""

import subprocess
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Reserved alpha for emissive pixels (see PLAN.md, Model rules). Any alpha other
# than 0/255 sends the face to the translucent item pipeline, so marked pixels
# sit on their own faces.
EMISSIVE_ALPHA = 250

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
    """16x16 sheet. Regions (x0, y0, x1, y1):
    (0,0,3,16) arm sides, light grey, tinted by custom model data color 0;
    (4,0,10,6) joint housing; (10,0,12,6) emissive strip (reserved alpha);
    (12,0,14,6) light_emission comparison strip; (4,6,7,9) arm end cap."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(16):
        for x in range(3):
            px[x, y] = (205, 205, 205, 255)
        px[0, y] = px[2, y] = (180, 180, 180, 255)
    for y in (3, 8, 13):  # panel lines
        for x in range(3):
            px[x, y] = (150, 150, 150, 255)
    for y in range(6):
        for x in range(4, 10):
            edge = x in (4, 9) or y in (0, 5)
            px[x, y] = (95, 95, 102, 255) if edge else (62, 62, 68, 255)
    for y in range(6):
        for x in range(10, 12):
            px[x, y] = (80, 230, 255, EMISSIVE_ALPHA)
        for x in range(12, 14):
            px[x, y] = (255, 150, 40, 255)
    for y in range(6, 9):
        for x in range(4, 7):
            px[x, y] = (180, 180, 180, 255)
    save(img, "mech/textures/item/test_part.png")


def glyphs() -> None:
    panel = Image.new("RGBA", (64, 32), (10, 22, 32, 200))
    p = panel.load()
    for x in range(64):
        p[x, 0] = p[x, 31] = (120, 220, 255, 255)
    for y in range(32):
        p[0, y] = p[63, y] = (120, 220, 255, 255)
    for cx, cy in ((1, 1), (62, 1), (1, 30), (62, 30)):  # corner accents
        for d in range(4):
            p[cx + (d if cx == 1 else -d), cy] = (255, 255, 255, 255)
            p[cx, cy + (d if cy == 1 else -d)] = (255, 255, 255, 255)
    save(panel, "mech/textures/font/panel.png")

    # Arrow cursor, tip at the top-left pixel.
    rows = [
        "W.......",
        "WW......",
        "WFW.....",
        "WFFW....",
        "WFFFW...",
        "WFFWWW..",
        "WWW.W...",
        "W....W..",
    ]
    cursor = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    c = cursor.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "W":
                c[x, y] = (20, 20, 20, 255)
            elif ch == "F":
                c[x, y] = (255, 255, 255, 255)
    save(cursor, "mech/textures/font/cursor.png")


# Vanilla hotbar sprites and their sizes (gui/sprites/hud).
HOTBAR_SPRITES = {
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
