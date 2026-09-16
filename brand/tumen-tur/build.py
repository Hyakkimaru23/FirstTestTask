#!/usr/bin/env python3
"""Tumen Tur mark + lockups. One silhouette, one colour, Cyrillic wordmark."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
MASK = ROOT / "source" / "site-baikal-mask.png"
OUT = ROOT / "export"
PNG = OUT / "png"
SVG = OUT / "svg"
PROOF = OUT / "proof"
for d in (PNG, SVG, PROOF):
    d.mkdir(parents=True, exist_ok=True)

BAIKAL = (0x12, 0x4B, 0x56)  # #124B56 — deep water, not cyan, not IT indigo
BLACK = (0x11, 0x11, 0x11)
WHITE = (0xFF, 0xFF, 0xFF)
CREAM = (0xF7, 0xF4, 0xEE)
DARK = (0x0C, 0x2C, 0x30)  # dark water, not navy-IT
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
NAME = "Тумэн Тур"  # U+0422 U+0443 U+043C U+044D U+043D space U+0422 U+0443 U+0440


def _smooth(values: np.ndarray, win: int = 9) -> np.ndarray:
    win = max(3, win | 1)
    k = np.ones(win) / win
    pad = win // 2
    ext = np.pad(values, (pad, pad), mode="edge")
    return np.convolve(ext, k, mode="valid")


def _catmull(points: np.ndarray, samples: int = 12) -> np.ndarray:
    """Closed Catmull-Rom through the given anchors."""
    pts = np.vstack([points[-1], points, points[0], points[1]])
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            out.append(
                0.5
                * (
                    (2 * p1)
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
            )
    return np.array(out)


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def _rot90(v: np.ndarray) -> np.ndarray:
    return np.array([-v[1], v[0]])


def _line_hit(p: np.ndarray, d: np.ndarray, q: np.ndarray, e: np.ndarray) -> np.ndarray:
    a = np.array([d, -e], dtype=float).T
    if abs(np.linalg.det(a)) < 1e-8:
        return (p + q) * 0.5
    t = np.linalg.solve(a, q - p)
    return p + t[0] * d


def _cap(a: np.ndarray, b: np.ndarray, outward: np.ndarray, n: int = 8) -> np.ndarray:
    mid = (a + b) * 0.5
    v0 = a - mid

    def rot(v, ang):
        c, s = math.cos(ang), math.sin(ang)
        return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])

    sign = 1.0 if np.dot(rot(v0, math.pi / 2), outward) >= 0 else -1.0
    return np.array([mid + rot(v0, sign * math.pi * i / n) for i in range(1, n)])


def _offset_poly(pts: np.ndarray, dist: np.ndarray | float) -> np.ndarray:
    """Miter offset. dist may be a scalar or per-vertex half-width."""
    w = np.full(len(pts), float(dist)) if np.isscalar(dist) else np.asarray(dist, dtype=float)
    out = []
    for i, p in enumerate(pts):
        if i == 0:
            t = _unit(pts[1] - pts[0])
            out.append(p + _rot90(t) * w[i])
        elif i == len(pts) - 1:
            t = _unit(pts[-1] - pts[-2])
            out.append(p + _rot90(t) * w[i])
        else:
            t0 = _unit(pts[i] - pts[i - 1])
            t1 = _unit(pts[i + 1] - pts[i])
            n0, n1 = _rot90(t0), _rot90(t1)
            out.append(_line_hit(pts[i - 1] + n0 * w[i], t0, pts[i + 1] + n1 * w[i], -t1))
    return np.array(out)


def baikal_parts(*, chunky: bool = False) -> tuple[np.ndarray, np.ndarray | None]:
    """Baikal as a bent rift: two legs, even band, one Olkhon bay.

    Not a tapered swirl (that read as a turd). Not a pill with a USB slot.
    No inner hole — a slot in a stick is a flash drive.
    """
    # Spine already bent like the map: south more N–S, north kicks NE.
    if not chunky:
        spine = np.array(
            [
                [0.00, 0.00],
                [0.20, 0.022],
                [0.38, 0.088],  # kink / Olkhon
                [0.66, 0.210],
                [1.00, 0.355],
            ],
            dtype=float,
        )
        widths = np.array([0.058, 0.062, 0.050, 0.048, 0.044])  # south basin, not a tadpole
        bay_i = 2
        bay_depth = 0.034
        bay_half = 0.058
    else:
        spine = np.array(
            [
                [0.00, 0.00],
                [0.24, 0.024],
                [0.42, 0.088],
                [0.70, 0.188],
                [1.00, 0.300],
            ],
            dtype=float,
        )
        widths = np.array([0.078, 0.082, 0.066, 0.064, 0.060])
        bay_i = 2
        bay_depth = 0.048
        bay_half = 0.075

    east = _offset_poly(spine, widths)
    west = _offset_poly(spine, -widths)

    # Open Olkhon bay — dent in the west shore, not a hole and not a swirl.
    t_in = _unit(spine[bay_i] - spine[bay_i - 1])
    t_out = _unit(spine[bay_i + 1] - spine[bay_i])
    n_in, n_out = _rot90(t_in), _rot90(t_out)
    n_bay = _unit(n_in + n_out)
    p = spine[bay_i]
    bay = np.array(
        [
            p - t_in * bay_half - n_in * widths[bay_i],
            p - t_in * (bay_half * 0.12) + n_bay * (bay_depth * 0.72),
            p + n_bay * bay_depth,
            p + t_out * (bay_half * 0.12) + n_bay * (bay_depth * 0.72),
            p + t_out * bay_half - n_out * widths[bay_i],
        ]
    )
    west = np.vstack([west[:bay_i], bay, west[bay_i + 1 :]])

    t0 = _unit(spine[1] - spine[0])
    tN = _unit(spine[-1] - spine[-2])
    south_cap = _cap(east[0], west[0], -t0, 9)
    north_cap = _cap(west[-1], east[-1], tN, 9)

    outer = np.vstack([west, north_cap, east[::-1], south_cap])

    ang = math.radians(-42 if not chunky else -44)
    rot = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    outer = outer @ rot.T
    mn, mx = outer.min(0), outer.max(0)
    outer = (outer - mn) / (mx - mn)
    return outer, None


def baikal_polygon(n: int = 280, *, chunky: bool = False) -> np.ndarray:
    outer, _ = baikal_parts(chunky=chunky)
    return outer


def poly_to_pixels(poly: np.ndarray, size: int, margin: float = 0.14) -> list[tuple[int, int]]:
    usable = size * (1 - 2 * margin)
    pts = poly * usable + size * margin
    return [(int(round(x)), int(round(y))) for x, y in pts]


def render_mark(
    size: int,
    fill: tuple[int, int, int],
    bg: tuple[int, int, int] | None,
    *,
    chunky: bool = False,
    margin: float = 0.14,
) -> Image.Image:
    """Site-logo Baikal contour. Do not invent a new blob."""
    from PIL import ImageFilter

    img = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    raw = Image.open(MASK).convert("L")
    arr = np.array(raw)
    # Source is white lake on black.
    if arr.mean() < 127:
        lake = arr
    else:
        lake = arr
    sil = Image.fromarray(lake)
    usable = max(8, int(size * (1 - 2 * margin)))
    sil = sil.resize((usable, usable), Image.Resampling.BILINEAR)
    if chunky:
        sil = sil.filter(ImageFilter.MaxFilter(3 if usable >= 24 else 1))
    pix = np.array(sil)
    rgba = np.zeros((usable, usable, 4), dtype=np.uint8)
    rgba[pix > 90] = (*fill, 255)
    layer = Image.fromarray(rgba, "RGBA")
    img.paste(layer, ((size - usable) // 2, (size - usable) // 2), layer)
    return img


def svg_path(poly: np.ndarray, size: int = 1000, margin: float = 0.14) -> str:
    pts = np.array(poly_to_pixels(poly, size, margin=margin), dtype=float)
    cmds = [f"M {pts[0,0]:.1f} {pts[0,1]:.1f}"]
    for x, y in pts[1:]:
        cmds.append(f"L {x:.1f} {y:.1f}")
    cmds.append("Z")
    return " ".join(cmds)


def write_svg(path: Path, fill: str, bg: str | None, *, chunky: bool = False, size: int = 1000) -> None:
    """Site contour as mask — do not replace with a drawn blob."""
    href = "site-baikal-mask.png"
    dest = path.parent / href
    dest.write_bytes(MASK.read_bytes())
    bg_rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    path.write_text(
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  {bg_rect}
  <mask id="baikal" maskUnits="userSpaceOnUse">
    <image xlink:href="{href}" href="{href}" x="80" y="80" width="840" height="840"/>
  </mask>
  <rect width="{size}" height="{size}" fill="{fill}" mask="url(#baikal)"/>
</svg>
'''
    )


def hex_of(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def draw_name(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    size: int,
    fill: tuple[int, int, int],
    *,
    anchor: str = "lt",
) -> tuple[int, int, int, int]:
    """Set the wordmark: Noto Sans Bold, condensed, tracked, real Cyrillic."""
    font = ImageFont.truetype(FONT, size)
    # Draw into a temp image, then squash horizontally — own cut, not Inter/Arial.
    bbox = font.getbbox(NAME)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tmp = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((-bbox[0] + 4, -bbox[1] + 4), NAME, font=font, fill=(*fill, 255))
    # Optical tracking: add a hair of space via scale + the font's own sidebearings.
    # Condense 8% so it is not Noto «as shipped».
    new_w = max(1, int(tmp.width * 0.90))
    tmp = tmp.resize((new_w, tmp.height), Image.Resampling.LANCZOS)
    # Extra word space: split and re-gap «Тумэн» / «Тур» so Тур is not a suffix.
    # Simpler: the string already has a space; after condense it stays one unit.
    x, y = xy
    tw, th = tmp.size
    if "m" in anchor:
        x -= tw / 2
    if "r" in anchor:
        x -= tw
    if "m" == anchor[0] or anchor.startswith("mm"):
        pass
    if anchor[0] == "m":
        y -= th / 2
    if anchor[0] == "b":
        y -= th
    if anchor in ("mm", "mt"):
        if anchor == "mm":
            y -= th / 2
            x = xy[0] - tw / 2
        if anchor == "mt":
            x = xy[0] - tw / 2
    draw._image.paste(tmp, (int(x), int(y)), tmp)
    return (int(x), int(y), int(x + tw), int(y + th))


def compose_word_image(
    text: str,
    px: int,
    fill: tuple[int, int, int],
    *,
    condense: float = 0.90,
    word_gap_extra: int | None = None,
) -> Image.Image:
    font = ImageFont.truetype(FONT, px)
    parts = text.split(" ")
    glyphs = []
    for part in parts:
        bb = font.getbbox(part)
        im = Image.new("RGBA", (bb[2] - bb[0] + 6, bb[3] - bb[1] + 6), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 3, -bb[1] + 3), part, font=font, fill=(*fill, 255))
        nw = max(1, int(im.width * condense))
        im = im.resize((nw, im.height), Image.Resampling.LANCZOS)
        glyphs.append(im)
    gap = word_gap_extra if word_gap_extra is not None else max(18, px // 4)
    h = max(g.height for g in glyphs)
    w = sum(g.width for g in glyphs) + gap * (len(glyphs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i, g in enumerate(glyphs):
        out.paste(g, (x, (h - g.height) // 2), g)
        x += g.width + (gap if i < len(glyphs) - 1 else 0)
    return out


def sheet(size: tuple[int, int], bg: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", size, bg)


def paste_c(base: Image.Image, overlay: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Paste overlay centered in box (l,t,r,b)."""
    l, t, r, b = box
    cw, ch = r - l, b - t
    im = overlay
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    # scale to fit
    scale = min(cw / im.width, ch / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = l + (cw - nw) // 2
    y = t + (ch - nh) // 2
    base.paste(im, (x, y), im if im.mode == "RGBA" else None)


def lockup_horizontal(fill: tuple[int, int, int], bg: tuple[int, int, int] | None, w=1600, h=420) -> Image.Image:
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    mark = render_mark(340, fill, None, chunky=False, margin=0.08)
    word = compose_word_image(NAME, 118, fill, condense=0.90, word_gap_extra=36)
    # Vertical center as a group.
    total_w = mark.width + 40 + word.width
    x0 = (w - total_w) // 2
    y_mark = (h - mark.height) // 2
    y_word = (h - word.height) // 2 + 6
    img.paste(mark, (x0, y_mark), mark)
    img.paste(word, (x0 + mark.width + 48, y_word), word)
    return img


def lockup_vertical(fill: tuple[int, int, int], bg: tuple[int, int, int] | None, w=1000, h=1200) -> Image.Image:
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    mark = render_mark(520, fill, None, chunky=False, margin=0.10)
    word = compose_word_image(NAME, 92, fill, condense=0.90, word_gap_extra=30)
    total_h = mark.height + 36 + word.height
    y0 = (h - total_h) // 2
    img.paste(mark, ((w - mark.width) // 2, y0), mark)
    img.paste(word, ((w - word.width) // 2, y0 + mark.height + 36), word)
    return img


def lockup_word(fill: tuple[int, int, int], bg: tuple[int, int, int] | None, w=1400, h=360) -> Image.Image:
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    word = compose_word_image(NAME, 128, fill, condense=0.90, word_gap_extra=40)
    img.paste(word, ((w - word.width) // 2, (h - word.height) // 2), word)
    return img


def save_rgb(im: Image.Image, path: Path) -> None:
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        # If fully transparent corners, keep them as the image already has bg.
        if im.getextrema()[3][0] == 255:
            im.convert("RGB").save(path, "PNG", optimize=True)
            return
        bg.paste(im, mask=im.split()[-1])
        bg.save(path, "PNG", optimize=True)
    else:
        im.save(path, "PNG", optimize=True)


def main() -> None:
    assert [hex(ord(c)) for c in NAME] == [
        "0x422",
        "0x443",
        "0x43c",
        "0x44d",
        "0x43d",
        "0x20",
        "0x422",
        "0x443",
        "0x440",
    ], NAME

    write_svg(SVG / "znak.svg", hex_of(BAIKAL), None)
    write_svg(SVG / "znak-chernyj.svg", hex_of(BLACK), hex_of(WHITE))
    write_svg(SVG / "znak-belyj.svg", hex_of(WHITE), hex_of(DARK))
    write_svg(SVG / "znak-favicon.svg", hex_of(BAIKAL), None, chunky=True)

    # A — black mark on white (approval size ~40 mm @ 300 dpi ≈ 472 px; we use 1024).
    a = render_mark(1024, BLACK, WHITE, chunky=False, margin=0.16)
    a.save(PNG / "01-znak-chernyj-na-belom.png")
    render_mark(1024, BAIKAL, WHITE, chunky=False, margin=0.16).save(PNG / "01-znak-cvet-na-belom.png")
    render_mark(1024, BAIKAL, CREAM, chunky=False, margin=0.16).save(PNG / "01-znak-cvet-na-svetlom.png")
    render_mark(1024, WHITE, DARK, chunky=False, margin=0.16).save(PNG / "01-znak-belyj-na-temnom.png")
    # Color on near-black (teal-on-teal fails). White-on-color is the inversion lockup.
    render_mark(1024, BAIKAL, (0x14, 0x14, 0x14), chunky=False, margin=0.16).save(
        PNG / "01-znak-cvet-na-temnom.png"
    )

    # Size proofs
    for s in (160, 64, 48, 32, 24, 16):
        render_mark(s, BLACK, WHITE, chunky=False, margin=0.10).save(PROOF / f"znak-{s}.png")
        render_mark(s, BLACK, WHITE, chunky=True, margin=0.08).save(PROOF / f"favicon-{s}.png")

    # 24 px on a larger canvas so the critique is visible
    proof24 = Image.new("RGB", (480, 200), (255, 255, 255))
    p = render_mark(24, BLACK, WHITE, chunky=False, margin=0.08)
    ps = render_mark(24, BLACK, WHITE, chunky=True, margin=0.06)
    p32 = render_mark(32, BLACK, WHITE, chunky=False, margin=0.08)
    ps32 = render_mark(32, BLACK, WHITE, chunky=True, margin=0.06)
    proof24.paste(p, (40, 88))
    proof24.paste(ps, (120, 88))
    proof24.paste(p32, (200, 84))
    proof24.paste(ps32, (280, 84))
    proof24.save(PROOF / "scale-24-32.png")

    # Lockups 1–4 × 4 colourways
    pairs = {
        "cvet": (BAIKAL, CREAM),
        "chernyj": (BLACK, WHITE),
        "belyj": (WHITE, DARK),
        "inversiya": (WHITE, BAIKAL),  # белое имя на цвете знака, не teal-на-teal
    }
    for key, (fg, bg) in pairs.items():
        lockup_horizontal(fg, bg).save(PNG / f"02-gorizont-{key}.png")
        lockup_vertical(fg, bg).save(PNG / f"03-vertikal-{key}.png")
        lockup_word(fg, bg).save(PNG / f"04-slovo-{key}.png")

    # Favicon / Telegram
    for s, name in ((16, "05-favicon-16"), (24, "05-favicon-24"), (32, "05-favicon-32"), (48, "05-telegram-48")):
        render_mark(s, BAIKAL, None, chunky=True, margin=0.08).save(PNG / f"{name}.png")
        av = render_mark(s, WHITE, BAIKAL, chunky=True, margin=0.16)
        av.save(PNG / f"05-avatar-{s}.png")

    # System overview
    ov = sheet((1800, 1100), CREAM)
    dr = ImageDraw.Draw(ov)
    font_s = ImageFont.truetype(FONT, 22)
    cells = [
        ((40, 40, 420, 420), PNG / "01-znak-chernyj-na-belom.png", "1. знак"),
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
        # draw a plate
        dr.rectangle(box, fill=WHITE if "invers" not in path.name and "belyj" not in path.name else DARK)
        paste_c(ov, im, box)
        if label:
            dr.text((box[0], box[1] - 28), label, font=font_s, fill=BAIKAL)
    ov.save(PNG / "00-sistema-obzor.png")

    # Colour chip + name proof (to confirm Э)
    chip = sheet((900, 280), WHITE)
    cd = ImageDraw.Draw(chip)
    cd.rectangle((40, 40, 160, 160), fill=BAIKAL)
    word = compose_word_image(NAME, 72, BLACK, condense=0.90, word_gap_extra=28)
    chip.paste(word, (200, 70), word)
    codes = " ".join(f"U+{ord(c):04X}" for c in NAME)
    cd.text((200, 180), codes, font=font_s, fill=(80, 80, 80))
    chip.save(PROOF / "wordmark-unicode.png")

    # 40 mm approval frame (300 dpi → 472 px mark on a white field)
    frame = sheet((1100, 1100), WHITE)
    mark40 = render_mark(472, BLACK, None, chunky=False, margin=0.06)
    frame.paste(mark40, ((1100 - mark40.width) // 2, (1100 - mark40.height) // 2 - 20), mark40)
    fd = ImageDraw.Draw(frame)
    fd.rectangle((314, 1048, 786, 1054), fill=BLACK)
    fd.text((314, 1060), "40 mm", font=font_s, fill=(90, 90, 90))
    frame.save(PROOF / "A-chernyj-40mm.png")

    old = PROOF / "old-poop.png"
    if old.exists():
        cmp = sheet((1100, 520), WHITE)
        cd = ImageDraw.Draw(cmp)
        cd.text((40, 20), "было", font=font_s, fill=BLACK)
        cd.text((580, 20), "стало", font=font_s, fill=BLACK)
        paste_c(cmp, Image.open(old).convert("RGBA"), (40, 60, 520, 500))
        paste_c(cmp, Image.open(PNG / "01-znak-chernyj-na-belom.png").convert("RGBA"), (580, 60, 1060, 500))
        cmp.save(PROOF / "A-bylo-stalo.png")

    print("built", PNG)
    print("name", NAME, [hex(ord(c)) for c in NAME])


if __name__ == "__main__":
    main()
