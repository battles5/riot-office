"""Draw the artwork: README banner, app icon and the Windows setup wizard images.

    python assets/make_art.py   -> assets/banner.png, icon.png, icon.ico, wizard_side.bmp, wizard_small.bmp

Synthwave style: night sky, striped sun, neon perspective grid, the name in neon.
Uses Windows' Segoe UI Black Italic / Bahnschrift when present, DejaVu Sans Bold Oblique otherwise.
"""

import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PINK, CYAN, YELLOW, PURPLE = (255, 41, 117), (45, 226, 230), (255, 214, 64), (176, 38, 255)
FONT_CANDIDATES = {
    "title": ["C:/Windows/Fonts/seguibli.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"],
    "body": ["C:/Windows/Fonts/bahnschrift.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES[kind]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def gradient(w: int, h: int, stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """A vertical gradient through ``stops`` (position 0-1, colour)."""
    column = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / max(h - 1, 1)
        for (k0, c0), (k1, c1) in zip(stops, stops[1:]):
            if k0 <= k <= k1:
                f = (k - k0) / ((k1 - k0) or 1)
                column.putpixel((0, y), tuple(int(a + (b - a) * f) for a, b in zip(c0, c1)))
                break
    return column.resize((w, h))


def glow_paste(canvas: Image.Image, mask: Image.Image, colour, core, radii=((24, 200), (8, 255))) -> None:
    """Paste ``mask`` in ``core`` colour with a blurred ``colour`` halo around it."""
    w, h = canvas.size
    for radius, strength in radii:
        halo = ImageChops.multiply(mask.filter(ImageFilter.GaussianBlur(radius)), Image.new("L", (w, h), strength))
        canvas.paste(Image.new("RGB", (w, h), colour), (0, 0), halo)
    canvas.paste(Image.new("RGB", (w, h), core), (0, 0), mask)


def scene(w: int, h: int, horizon: float, sun_x: float, sun_r: float, stars: int, seed: int = 7) -> Image.Image:
    """Sky, stars, striped sun and the neon grid."""
    hy = int(h * horizon)
    img = gradient(w, h, [(0, (13, 2, 33)), (horizon, (72, 14, 102)), (horizon + 0.001, (24, 4, 44)), (1, (8, 1, 18))])
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(stars):
        x, y, r = rnd.randrange(w), rnd.randrange(max(int(hy * 0.85), 1)), rnd.choice((1, 1, 2, 3))
        d.ellipse([x, y, x + r, y + r], fill=(255, 255, 255))

    cx, r = int(w * sun_x), int(h * sun_r)
    sun_mask = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sun_mask)
    sd.ellipse([cx - r, hy - r, cx + r, hy + r], fill=255)
    sd.rectangle([0, hy, w, h], fill=0)
    y, gap, band = hy - r * 0.55, max(r * 0.04, 2.0), r * 0.15
    while y < hy:
        sd.rectangle([0, y, w, y + gap], fill=0)
        y += band
        gap *= 1.4
        band *= 0.82
    sun = gradient(w, h, [(0, YELLOW), (horizon, PINK), (1, PINK)])
    halo = ImageChops.multiply(sun_mask.filter(ImageFilter.GaussianBlur(max(r // 4, 2))), Image.new("L", (w, h), 120))
    img.paste(Image.new("RGB", (w, h), (255, 60, 140)), (0, 0), halo)
    img.paste(sun, (0, 0), sun_mask)

    grid = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(grid)
    line = max(w // 640, 1)
    for i in range(-40, 41):
        gd.line([(cx + i * w * 0.012, hy), (cx + i * w * 0.12, h)], fill=255, width=line)
    y, step = hy, max(h / 300, 1.5)
    while y < h:
        gd.line([(0, y), (w, y)], fill=255, width=line)
        step *= 1.32
        y += step
    img.paste(Image.new("RGB", (w, h), (255, 46, 220)), (0, 0), grid.filter(ImageFilter.GaussianBlur(3)))
    img.paste(Image.new("RGB", (w, h), (255, 120, 235)), (0, 0), grid)
    return img


def banner() -> None:
    ss = 2
    w, h = 1280 * ss, 400 * ss
    img = scene(w, h, horizon=0.66, sun_x=0.5, sun_r=0.42, stars=160)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((w // 2, int(h * 0.36)), "RIOT OFFICE", font=load_font("title", 150 * ss), fill=255, anchor="mm")
    glow_paste(img, mask, PINK, (255, 220, 235), radii=((28 * ss, 210), (10 * ss, 255)))
    sub = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sub).text((w // 2, int(h * 0.58)), " ".join("LOUD COLOURS, LOCAL FILES"),
                             font=load_font("body", 30 * ss), fill=255, anchor="mm")
    glow_paste(img, sub, CYAN, (220, 255, 255), radii=((10 * ss, 220),))
    img.resize((w // ss, h // ss), Image.LANCZOS).save(HERE / "banner.png", optimize=True)


def icon_image(size: int = 512) -> Image.Image:
    """A rounded tile with the sunset and a neon "R"."""
    img = scene(size, size, horizon=0.68, sun_x=0.5, sun_r=0.36, stars=40, seed=3)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).text((size // 2, int(size * 0.40)), "R", font=load_font("title", int(size * 0.62)), fill=255, anchor="mm")
    glow_paste(img, mask, PINK, (255, 225, 238), radii=((size // 24, 230), (size // 64, 255)))
    corners = Image.new("L", (size, size), 0)
    ImageDraw.Draw(corners).rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 6, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), corners)
    return out


def icons() -> None:
    big = icon_image(512)
    big.resize((256, 256), Image.LANCZOS).save(HERE / "icon.png", optimize=True)
    big.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def wizard() -> None:
    """Inno Setup images: 164x314 side panel and 55x58 header icon (24-bit BMP)."""
    side = scene(164 * 2, 314 * 2, horizon=0.78, sun_x=0.5, sun_r=0.2, stars=60, seed=11)
    mask = Image.new("L", side.size, 0)
    d = ImageDraw.Draw(mask)
    d.text((side.width // 2, int(side.height * 0.22)), "RIOT", font=load_font("title", 76), fill=255, anchor="mm")
    d.text((side.width // 2, int(side.height * 0.34)), "OFFICE", font=load_font("title", 56), fill=255, anchor="mm")
    glow_paste(side, mask, PINK, (255, 220, 235), radii=((14, 220), (5, 255)))
    side.resize((164, 314), Image.LANCZOS).save(HERE / "wizard_side.bmp")
    small = Image.new("RGB", (55, 58), (255, 255, 255))
    small.paste(icon_image(220).resize((52, 52), Image.LANCZOS), (1, 3), icon_image(220).resize((52, 52), Image.LANCZOS))
    small.save(HERE / "wizard_small.bmp")


if __name__ == "__main__":
    banner()
    icons()
    wizard()
    print("artwork written in", HERE)
