#!/usr/bin/env python3
"""Tumen Tur mark + lockups. One silhouette, one colour, Cyrillic wordmark."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
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


def _centerline_lake(*, chunky: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parametric Baikal: checkmark axis, south basin, Olkhon waist.

    Returns centerline, west half-widths, east half-widths in local units.
    """
    # 8 structural stations along the lake (south → north).
    # x = along-axis, y = crescent toward SE (the «галочка» bend).
    if not chunky:
        stations = np.array(
            [
                #    x     y     west   east
                [0.00, 0.00, 0.054, 0.060],
                [0.12, 0.008, 0.074, 0.078],
                [0.26, 0.024, 0.062, 0.068],
                [0.38, 0.048, 0.026, 0.052],  # Olkhon waist — keep sharp
                [0.48, 0.082, 0.046, 0.062],  # kink toward NE
                [0.64, 0.132, 0.050, 0.054],
                [0.84, 0.188, 0.044, 0.044],
                [1.00, 0.236, 0.040, 0.040],
            ]
        )
    else:
        stations = np.array(
            [
                [0.00, 0.00, 0.080, 0.086],
                [0.13, 0.008, 0.108, 0.112],
                [0.27, 0.022, 0.088, 0.094],
                [0.39, 0.048, 0.028, 0.070],
                [0.50, 0.080, 0.068, 0.082],
                [0.66, 0.126, 0.074, 0.076],
                [0.84, 0.176, 0.064, 0.064],
                [1.00, 0.218, 0.058, 0.058],
            ]
        )

    t = np.linspace(0, 1, 160)
    xs = np.interp(t, np.linspace(0, 1, len(stations)), stations[:, 0])
    ys = np.interp(t, np.linspace(0, 1, len(stations)), stations[:, 1])
    ww = np.interp(t, np.linspace(0, 1, len(stations)), stations[:, 2])
    ew = np.interp(t, np.linspace(0, 1, len(stations)), stations[:, 3])
    ww, ew = _smooth(ww, 7), _smooth(ew, 7)
    center = np.stack([xs, ys], axis=1)
    return center, ww, ew


def baikal_polygon(n: int = 280, *, chunky: bool = False) -> np.ndarray:
    center, ww, ew = _centerline_lake(chunky=chunky)
    d = np.gradient(center, axis=0)
    hyp = np.clip(np.linalg.norm(d, axis=1), 1e-6, None)
    tan = d / hyp[:, None]
    # Normal: rotate tangent +90° (toward +y / east).
    nrm = np.stack([-tan[:, 1], tan[:, 0]], axis=1)

    west = center - nrm * ww[:, None]
    east = center + nrm * ew[:, None]

    def arc_cap(p_a: np.ndarray, p_b: np.ndarray, outward: np.ndarray) -> np.ndarray:
        mid = (p_a + p_b) * 0.5
        v0 = p_a - mid
        def rot(v, ang):
            c, s = math.cos(ang), math.sin(ang)
            return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])
        sign = 1.0 if np.dot(rot(v0, math.pi / 2), outward) >= np.dot(rot(v0, -math.pi / 2), outward) else -1.0
        return np.array([mid + rot(v0, sign * math.pi * k / 10) for k in range(1, 10)])

    north_cap = arc_cap(west[-1], east[-1], tan[-1])
    south_cap = arc_cap(east[0], west[0], -tan[0])
    poly = np.vstack([west, north_cap, east[::-1], south_cap])
    k = 3
    pad = k // 2
    ext = np.vstack([poly[-pad:], poly, poly[:pad]])
    ker = np.ones(k) / k
    poly = np.stack(
        [np.convolve(ext[:, 0], ker, mode="valid"), np.convolve(ext[:, 1], ker, mode="valid")],
        axis=1,
    )

    ang = math.radians(-34 if not chunky else -36)
    c, s = math.cos(ang), math.sin(ang)
    poly = poly @ np.array([[c, -s], [s, c]]).T
    mn, mx = poly.min(0), poly.max(0)
    poly = (poly - mn) / (mx - mn)
    return poly


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
    mode = "RGBA"
    img = Image.new(mode, (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pts = poly_to_pixels(baikal_polygon(chunky=chunky), size, margin=margin)
    draw.polygon(pts, fill=(*fill, 255))
    return img


def svg_path(poly: np.ndarray, size: int = 1000, margin: float = 0.14) -> str:
    pts = np.array(poly_to_pixels(poly, size, margin=margin), dtype=float)
    # Smooth to cubics with Catmull-Rom-ish midpoints (simple polyline is enough
    # and safer for embroidery). Keep as closed polygon path.
    cmds = [f"M {pts[0,0]:.1f} {pts[0,1]:.1f}"]
    for x, y in pts[1:]:
        cmds.append(f"L {x:.1f} {y:.1f}")
    cmds.append("Z")
    return " ".join(cmds)


def write_svg(path: Path, d: str, fill: str, bg: str | None, size: int = 1000) -> None:
    bg_rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    path.write_text(
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  {bg_rect}
  <path fill="{fill}" d="{d}"/>
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

    poly = baikal_polygon(chunky=False)
    poly_s = baikal_polygon(chunky=True)
    d = svg_path(poly)
    d_s = svg_path(poly_s)

    write_svg(SVG / "znak.svg", d, hex_of(BAIKAL), None)
    write_svg(SVG / "znak-chernyj.svg", d, hex_of(BLACK), hex_of(WHITE))
    write_svg(SVG / "znak-belyj.svg", d, hex_of(WHITE), hex_of(DARK))
    write_svg(SVG / "znak-favicon.svg", d_s, hex_of(BAIKAL), None)

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

    # Round comparison if the earlier AI rasters are on disk
    rounds = [
        Path("/opt/cursor/artifacts/assets/tumen-mark-a1-black.png"),
        Path("/opt/cursor/artifacts/assets/tumen-mark-a2-black.png"),
        Path("/opt/cursor/artifacts/assets/tumen-mark-a3-black.png"),
        PNG / "01-znak-chernyj-na-belom.png",
    ]
    if all(p.exists() for p in rounds):
        cmp = sheet((1400, 400), WHITE)
        cd = ImageDraw.Draw(cmp)
        labels = ["A1 карта", "A2 пальцы", "A3 толще", "A финал"]
        for i, (p, lab) in enumerate(zip(rounds, labels)):
            im = Image.open(p).convert("RGBA")
            box = (30 + i * 340, 50, 30 + i * 340 + 320, 370)
            cd.rectangle(box, outline=(220, 220, 220), width=1)
            paste_c(cmp, im, box)
            cd.text((box[0], 18), lab, font=font_s, fill=BLACK)
        cmp.save(PROOF / "A-krugi-sravnenie.png")

    print("built", PNG)
    print("name", NAME, [hex(ord(c)) for c in NAME])


if __name__ == "__main__":
    main()
