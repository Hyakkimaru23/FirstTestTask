#!/usr/bin/env python3
"""Lockups from the site Baikal contour. Do not invent a new silhouette."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
MASK = ROOT / "source" / "site-baikal-mask.png"
PNG = ROOT / "export" / "png"
SVG = ROOT / "export" / "svg"
PROOF = ROOT / "export" / "proof"
for d in (PNG, SVG, PROOF):
    d.mkdir(parents=True, exist_ok=True)

BAIKAL = (0x12, 0x4B, 0x56)
BLACK = (0x11, 0x11, 0x11)
WHITE = (0xFF, 0xFF, 0xFF)
CREAM = (0xF7, 0xF4, 0xEE)
DARK = (0x0C, 0x2C, 0x30)
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
NAME = "Тумэн Тур"


def render_mark(size, fill, bg, *, chunky=False, margin=0.12):
    canvas = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    sil = Image.open(MASK).convert("L")
    usable = max(16, int(size * (1 - 2 * margin)))
    sil = sil.resize((usable, usable), Image.Resampling.BILINEAR)
    if chunky and usable >= 28:
        sil = sil.filter(ImageFilter.MaxFilter(3))
    pix = np.array(sil)
    rgba = np.zeros((usable, usable, 4), dtype=np.uint8)
    rgba[pix > 90] = (*fill, 255)
    layer = Image.fromarray(rgba, "RGBA")
    canvas.paste(layer, ((size - usable) // 2, (size - usable) // 2), layer)
    return canvas


def word(px, fill):
    font = ImageFont.truetype(FONT, px)
    parts = NAME.split(" ")
    glyphs = []
    for part in parts:
        bb = font.getbbox(part)
        im = Image.new("RGBA", (bb[2] - bb[0] + 6, bb[3] - bb[1] + 6), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 3, -bb[1] + 3), part, font=font, fill=(*fill, 255))
        im = im.resize((max(1, int(im.width * 0.90)), im.height), Image.Resampling.LANCZOS)
        glyphs.append(im)
    gap = max(18, px // 4)
    h = max(g.height for g in glyphs)
    w = sum(g.width for g in glyphs) + gap * (len(glyphs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i, g in enumerate(glyphs):
        out.paste(g, (x, (h - g.height) // 2), g)
        x += g.width + (gap if i < len(glyphs) - 1 else 0)
    return out


def horiz(fill, bg, w=1600, h=420):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    mark = render_mark(340, fill, None, margin=0.06)
    wd = word(118, fill)
    total = mark.width + 40 + wd.width
    x0 = (w - total) // 2
    img.paste(mark, (x0, (h - mark.height) // 2), mark)
    img.paste(wd, (x0 + mark.width + 40, (h - wd.height) // 2 + 6), wd)
    return img


def vert(fill, bg, w=1000, h=1200):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    mark = render_mark(520, fill, None, margin=0.08)
    wd = word(92, fill)
    total = mark.height + 36 + wd.height
    y0 = (h - total) // 2
    img.paste(mark, ((w - mark.width) // 2, y0), mark)
    img.paste(wd, ((w - wd.width) // 2, y0 + mark.height + 36), wd)
    return img


def slovo(fill, bg, w=1400, h=360):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    wd = word(128, fill)
    img.paste(wd, ((w - wd.width) // 2, (h - wd.height) // 2), wd)
    return img


def main():
    assert [hex(ord(c)) for c in NAME] == [
        "0x422", "0x443", "0x43c", "0x44d", "0x43d", "0x20", "0x422", "0x443", "0x440"
    ]
    render_mark(1024, BLACK, WHITE).save(PNG / "01-znak-chernyj-na-belom.png")
    render_mark(1024, BAIKAL, WHITE).save(PNG / "01-znak-cvet-na-belom.png")
    render_mark(1024, BAIKAL, CREAM).save(PNG / "01-znak-cvet-na-svetlom.png")
    render_mark(1024, WHITE, DARK).save(PNG / "01-znak-belyj-na-temnom.png")
    render_mark(1024, BAIKAL, (0x14, 0x14, 0x14)).save(PNG / "01-znak-cvet-na-temnom.png")

    for s in (160, 64, 48, 32, 24, 16):
        render_mark(s, BLACK, WHITE, margin=0.08).save(PROOF / f"znak-{s}.png")
        render_mark(s, BLACK, WHITE, chunky=True, margin=0.06).save(PROOF / f"favicon-{s}.png")

    pairs = {
        "cvet": (BAIKAL, CREAM),
        "chernyj": (BLACK, WHITE),
        "belyj": (WHITE, DARK),
        "inversiya": (WHITE, BAIKAL),
    }
    for key, (fg, bg) in pairs.items():
        horiz(fg, bg).save(PNG / f"02-gorizont-{key}.png")
        vert(fg, bg).save(PNG / f"03-vertikal-{key}.png")
        slovo(fg, bg).save(PNG / f"04-slovo-{key}.png")

    for s, name in ((16, "05-favicon-16"), (24, "05-favicon-24"), (32, "05-favicon-32"), (48, "05-telegram-48")):
        render_mark(s, BAIKAL, None, chunky=True, margin=0.06).save(PNG / f"{name}.png")
        render_mark(s, WHITE, BAIKAL, chunky=True, margin=0.14).save(PNG / f"05-avatar-{s}.png")

    # overview
    ov = Image.new("RGB", (1800, 1100), CREAM)
    dr = ImageDraw.Draw(ov)
    font_s = ImageFont.truetype(FONT, 22)

    def paste_c(base, overlay, box):
        l, t, r, b = box
        cw, ch = r - l, b - t
        if overlay.mode != "RGBA":
            overlay = overlay.convert("RGBA")
        scale = min(cw / overlay.width, ch / overlay.height)
        nw, nh = max(1, int(overlay.width * scale)), max(1, int(overlay.height * scale))
        overlay = overlay.resize((nw, nh), Image.Resampling.LANCZOS)
        base.paste(overlay, (l + (cw - nw) // 2, t + (ch - nh) // 2), overlay)

    cells = [
        ((40, 40, 420, 420), PNG / "01-znak-chernyj-na-belom.png", "1. знак с сайта"),
        ((460, 40, 1320, 300), PNG / "02-gorizont-cvet.png", "2. горизонталь"),
        ((1360, 40, 1760, 520), PNG / "03-vertikal-cvet.png", "3. вертикаль"),
        ((460, 340, 1320, 560), PNG / "04-slovo-cvet.png", "4. слово"),
        ((40, 460, 200, 620), PNG / "05-favicon-32.png", "5. 32 px"),
        ((220, 460, 380, 620), PNG / "05-telegram-48.png", ""),
        ((40, 680, 420, 1060), PNG / "01-znak-belyj-na-temnom.png", "инверсия"),
        ((460, 600, 1320, 860), PNG / "02-gorizont-inversiya.png", ""),
        ((1360, 560, 1760, 1060), PNG / "03-vertikal-inversiya.png", ""),
        ((460, 880, 1320, 1060), PNG / "04-slovo-inversiya.png", ""),
    ]
    for box, path, label in cells:
        im = Image.open(path).convert("RGBA")
        dr.rectangle(box, fill=WHITE if "invers" not in path.name and "belyj" not in path.name else DARK)
        paste_c(ov, im, box)
        if label:
            dr.text((box[0], box[1] - 28), label, font=font_s, fill=BAIKAL)
    ov.save(PNG / "00-sistema-obzor.png")

    frame = Image.new("RGB", (1100, 1100), WHITE)
    mark40 = render_mark(520, BLACK, None, margin=0.04)
    frame.paste(mark40, ((1100 - mark40.width) // 2, (1100 - mark40.height) // 2 - 20), mark40)
    fd = ImageDraw.Draw(frame)
    fd.rectangle((314, 1048, 786, 1054), fill=BLACK)
    fd.text((314, 1060), "40 mm", font=font_s, fill=(90, 90, 90))
    frame.save(PROOF / "A-chernyj-40mm.png")

    # copy mask beside svg
    (SVG / "site-baikal-mask.png").write_bytes(MASK.read_bytes())
    for name, fill, bg in (
        ("znak.svg", "#124B56", None),
        ("znak-chernyj.svg", "#111111", "#FFFFFF"),
        ("znak-belyj.svg", "#FFFFFF", "#0C2C30"),
        ("znak-favicon.svg", "#124B56", None),
    ):
        bg_rect = f'<rect width="1000" height="1000" fill="{bg}"/>' if bg else ""
        (SVG / name).write_text(
            f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1000 1000">
  {bg_rect}
  <mask id="m"><image href="site-baikal-mask.png" x="80" y="80" width="840" height="840"/></mask>
  <rect width="1000" height="1000" fill="{fill}" mask="url(#m)"/>
</svg>
'''
        )
    print("built from site contour")


if __name__ == "__main__":
    main()
