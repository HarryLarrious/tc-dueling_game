#!/usr/bin/env python3
"""Generate the placeholder mech part texture (MEC-32) into pack/assets/.

    python3 pack/src/placeholder_assets.py

Needs Pillow. Writes mech:item/skel_panel, a light neutral panel that the
skeleton models tint per class and part (custom model data color 0). The
models mech:skel_box and mech:skel_segment are hand-written JSON.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def panel() -> None:
    size = 64
    img = Image.new("RGBA", (size, size), (228, 230, 234, 255))
    d = ImageDraw.Draw(img)
    for y in range(size):  # soft vertical gradient
        v = int(236 - 18 * y / size)
        d.line((0, y, size - 1, y), fill=(v, v, v + 3, 255))
    d.rectangle((0, 0, size - 1, size - 1), outline=(150, 152, 158, 255), width=2)
    d.rectangle((6, 6, size - 7, size - 7), outline=(196, 198, 204, 255), width=1)
    for cx, cy in ((10, 10), (size - 11, 10), (10, size - 11), (size - 11, size - 11)):
        d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(170, 172, 178, 255))
    out = ASSETS / "mech/textures/item/skel_panel.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)


if __name__ == "__main__":
    panel()
    print(f"wrote placeholder texture under {ASSETS}")
