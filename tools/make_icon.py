"""Generate the app logo / icon files in assets/.

    python tools/make_icon.py

Produces:
  assets/icon.png   1024 px master logo (transparent corners)
  assets/icon.ico   multi-size Windows icon (16 - 256 px)
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from gui.diagrams import _layout, _render_solid, _section  # noqa: E402

ASSETS = os.path.join(ROOT, "assets")

NAVY_TOP = (14, 42, 82)
NAVY_BOTTOM = (8, 22, 46)
AMBER = (245, 158, 11)

LOGO_PALETTE = {
    "face_top": (255, 255, 255),
    "face_bottom": (214, 226, 240),
    "side_back": (180, 83, 9),
    "side_front": (251, 176, 59),
    "outline": (8, 22, 46),
}


def _background(size):
    """Rounded square with a diagonal navy gradient and a soft top glow."""
    v = Image.linear_gradient("L")
    grad = Image.blend(v, v.transpose(Image.Transpose.TRANSPOSE), 0.5).resize((size, size))
    bg = Image.composite(Image.new("RGB", (size, size), NAVY_BOTTOM),
                         Image.new("RGB", (size, size), NAVY_TOP), grad)
    glow = Image.new("L", (size, size), 0)
    ImageDraw.Draw(glow).ellipse((-size * 0.2, -size * 0.75, size * 1.2, size * 0.45), fill=38)
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.08))
    bg.paste((255, 255, 255), (0, 0), glow)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size * 0.22, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


def make_logo(size=1024):
    ss = 2
    S = size * ss
    img = _background(S)

    # Amber base line, like the platform of a weighing scale.
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((S * 0.2, S * 0.80, S * 0.8, S * 0.835), radius=S * 0.02, fill=AMBER)

    geom = _section("beam", {"H": 250, "B": 190, "tw": 34, "tf": 38})
    geom["depth"] = 0.34
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    box = int(S * 0.7)
    k = S / 400
    s, fx, fy, dx, dy = _layout(geom, box, box, k, detailed=False)
    part = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    _render_solid(part, geom, s, fx, fy, dx, dy, k * 1.6, pal=LOGO_PALETTE)
    part = part.crop(part.getbbox())
    # Centre the part horizontally, sitting just above the base line.
    layer.paste(part, ((S - part.width) // 2, int(S * 0.75) - part.height), part)

    shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(S * 0.015))
    img.paste((0, 0, 0), (int(S * 0.008), int(S * 0.018)), shadow.point(lambda a: a * 0.45))
    img.alpha_composite(layer)
    return img.resize((size, size), Image.LANCZOS)


def make_small(size):
    """Simplified flat mark for tiny icon sizes, where detail turns to mush."""
    ss = 8
    S = size * ss
    img = _background(S)
    d = ImageDraw.Draw(img)
    u = S / 32
    white = (255, 255, 255, 255)
    d.rectangle((7 * u, 6 * u, 25 * u, 10 * u), fill=white)
    d.rectangle((13.5 * u, 10 * u, 18.5 * u, 22 * u), fill=white)
    d.rectangle((7 * u, 22 * u, 25 * u, 26 * u), fill=white)
    d.rectangle((7 * u, 27.2 * u, 25 * u, 28.4 * u), fill=AMBER + (255,))
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    logo = make_logo(1024)
    logo.save(os.path.join(ASSETS, "icon.png"))

    images = {s: (make_small(s) if s <= 32 else logo.resize((s, s), Image.LANCZOS))
              for s in (16, 20, 24, 32, 40, 48, 64, 128, 256)}
    big = images[256]
    big.save(os.path.join(ASSETS, "icon.ico"), format="ICO",
             sizes=[(s, s) for s in images],
             append_images=[images[s] for s in images if s != 256])
    print("Wrote assets/icon.png and assets/icon.ico")


if __name__ == "__main__":
    main()
