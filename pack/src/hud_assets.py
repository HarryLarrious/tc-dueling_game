#!/usr/bin/env python3
"""Generate the combat HUD assets (MEC-53) into pack/ and the width table
into ui/hudfont.tc.

    python3 pack/src/hud_assets.py [--vanilla <26.3 client jar>]

Needs fontTools, freetype-py and Pillow.

  mech:rajdhani-hud.ttf       Rajdhani SemiBold subset to printable ASCII
                              (OFL 1.1, no Reserved Font Name; the license
                              ships as font/rajdhani-ofl.txt)
  mech:hud/<size>_<row>       HUD text fonts: size s (7), m (10) or l (16)
                              canvas units, moved down by row * ROW_STEP
                              units (row n<k> = up k rows); a boss bar title
                              is one line, so rows are how panels get lines
  minecraft hud sprites       hearts, food, armor, air, XP, jump and locator
                              bars (and their player dots) and effect
                              backgrounds, all transparent
  ui/hudfont.tc               HUD_CHARS and each size's advances in quarter
                              units, exactly as the client lays them out
                              (FreeType hinted advance at size * oversample
                              pixels per em, divided by the oversample)

Sprite sizes come from the vanilla jar when --vanilla is given, otherwise
from SPRITES below.
"""

import argparse
import io
import json
import zipfile
from pathlib import Path

import freetype
from fontTools import subset
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "pack" / "assets"
FONT_SRC = ASSETS / "mech" / "font" / "rajdhani-semibold.ttf"
FONT_HUD = ASSETS / "mech" / "font" / "rajdhani-hud.ttf"
TC_OUT = ROOT / "ui" / "hudfont.tc"

OVERSAMPLE = 4
SIZES = {"s": 7, "m": 10, "l": 16}
ROW_STEP = 4
ROWS = 18
HUD_CHARS = "".join(chr(c) for c in range(0x20, 0x7F))
# FreeType load flags TrueTypeGlyphProvider uses (26.3).
LOAD_FLAGS = 4194312

# Vanilla HUD sprites hidden by the pack (hotbar and crosshair are hidden by
# spike_assets.py). Name -> size, from the 26.3 client jar.
SPRITES = {
    "air": (9, 9), "air_bursting": (9, 9), "air_empty": (9, 9),
    "armor_empty": (9, 9), "armor_full": (9, 9), "armor_half": (9, 9),
    "effect_background": (24, 24), "effect_background_ambient": (24, 24),
    "experience_bar_background": (182, 5), "experience_bar_progress": (182, 5),
    "food_empty": (9, 9), "food_empty_hunger": (9, 9), "food_full": (9, 9),
    "food_full_hunger": (9, 9), "food_half": (9, 9), "food_half_hunger": (9, 9),
    "jump_bar_background": (182, 5), "jump_bar_cooldown": (182, 5), "jump_bar_progress": (182, 5),
    "locator_bar_arrow_down": (7, 10), "locator_bar_arrow_up": (7, 10), "locator_bar_background": (12, 5),
    "locator_bar_dot/bowtie": (9, 9), "locator_bar_dot/default_0": (9, 9), "locator_bar_dot/default_1": (9, 9),
    "locator_bar_dot/default_2": (9, 9), "locator_bar_dot/default_3": (9, 9),
}
HEART_KINDS = ["absorbing", "frozen", "poisoned", "withered", ""]
HEART_PARTS = ["full", "half"]


def heart_sprites() -> dict:
    """Every heart sprite name -> (9, 9)."""
    names = ["container", "container_blinking", "container_hardcore", "container_hardcore_blinking",
             "vehicle_container", "vehicle_full", "vehicle_half"]
    for kind in HEART_KINDS:
        prefix = f"{kind}_" if kind else ""
        for hard in ["", "hardcore_"]:
            for part in HEART_PARTS:
                for blink in ["", "_blinking"]:
                    names.append(f"{prefix}{hard}{part}{blink}")
    return {f"heart/{n}": (9, 9) for n in names}


def sprites_from_jar(jar: Path) -> dict:
    """Sizes of the hidden sprites read from the client jar."""
    out = {}
    prefix = "assets/minecraft/textures/gui/sprites/hud/"
    with zipfile.ZipFile(jar) as z:
        for name in z.namelist():
            if not (name.startswith(prefix) and name.endswith(".png")):
                continue
            rel = name[len(prefix):-4]
            if rel.startswith(("hotbar", "crosshair")):
                continue
            out[rel] = Image.open(io.BytesIO(z.read(name))).size
    return out


def hide_sprites(sizes: dict) -> None:
    for rel, size in sorted(sizes.items()):
        path = ASSETS / "minecraft" / "textures" / "gui" / "sprites" / "hud" / f"{rel}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", size, (0, 0, 0, 0)).save(path)


def subset_font() -> None:
    opts = subset.Options()
    opts.layout_features = []
    opts.hinting = True
    opts.name_IDs = ["*"]
    font = subset.load_font(str(FONT_SRC), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=HUD_CHARS)
    sub.subset(font)
    subset.save_font(font, str(FONT_HUD), opts)


def row_name(row: int) -> str:
    return f"n{-row}" if row < 0 else str(row)


def write_fonts() -> None:
    out = ASSETS / "mech" / "font" / "hud"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    for key, size in SIZES.items():
        for row in range(-ROWS, ROWS + 1):
            provider = {"type": "ttf", "file": "mech:rajdhani-hud.ttf", "size": size,
                        "oversample": OVERSAMPLE, "shift": [0, row * ROW_STEP]}
            (out / f"{key}_{row_name(row)}.json").write_text(json.dumps({"providers": [provider]}, indent=2) + "\n")


def advances() -> dict:
    """Quarter-unit advance of every HUD char, per size."""
    face = freetype.Face(str(FONT_HUD))
    out = {}
    for key, size in SIZES.items():
        ppem = round(size * OVERSAMPLE)
        face.set_pixel_sizes(ppem, ppem)
        quarters = []
        for ch in HUD_CHARS:
            face.load_char(ch, LOAD_FLAGS)
            adv = face.glyph.advance.x / 64 / OVERSAMPLE
            q = adv * 4
            if abs(q - round(q)) > 1e-6:
                raise SystemExit(f"advance of {ch!r} at size {size} is {adv}, not a quarter unit")
            quarters.append(int(round(q)))
        out[key] = quarters
    return out


def tc_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_tc(adv: dict) -> None:
    TC_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "// Generated by pack/src/hud_assets.py from mech:rajdhani-hud.ttf; do not edit.",
        "// Advances of the HUD fonts (mech:hud/<size>_<row>) in quarter canvas units,",
        "// exactly as the client lays text out, so the server can measure and rewind.",
        "",
        "/** The characters the HUD fonts have, in table order. */",
        "function hudChars(): str {",
        f"    return {tc_string(HUD_CHARS)};",
        "}",
        "",
        "/** Quarter-unit advances of hudChars() in HUD font size s, m or l. */",
        "function hudAdvances(size: str): list {",
    ]
    for key in SIZES:
        values = ", ".join(str(v) for v in adv[key])
        lines += [f"    if (size == {tc_string(key)}) {{", f"        return [{values}];", "    }"]
    lines += ["    return [];", "}", ""]
    TC_OUT.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", type=Path, help="26.3 client jar for sprite sizes")
    args = ap.parse_args()
    sizes = sprites_from_jar(args.vanilla) if args.vanilla else {**SPRITES, **heart_sprites()}
    hide_sprites(sizes)
    subset_font()
    write_fonts()
    write_tc(advances())
    print(f"hud: {len(sizes)} sprites hidden, {len(SIZES) * (2 * ROWS + 1)} fonts, width table -> {TC_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
