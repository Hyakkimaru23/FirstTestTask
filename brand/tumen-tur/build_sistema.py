#!/usr/bin/env python3
"""Единый логотип Тумэн Тур: контур Байкала с сайта + имя + линейка.

Не рисует новое озеро. Не кладёт Алтай/Монголию картинками в знак.
"""

from __future__ import annotations

import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
PNG = ROOT / "export" / "png"
SVG = ROOT / "export" / "svg"
PROOF = ROOT / "export" / "proof"
for d in (PNG, SVG, PROOF, SRC):
    d.mkdir(parents=True, exist_ok=True)

LOGO = SRC / "logo-saita.png"
MASK_IN = SRC / "site-baikal-mask.png"

BAIKAL = (0x12, 0x4B, 0x56)
BLACK = (0x11, 0x11, 0x11)
WHITE = (0xFF, 0xFF, 0xFF)
CREAM = (0xF7, 0xF4, 0xEE)
DARK = (0x0C, 0x2C, 0x30)
ORANGE = (0xE8, 0x6A, 0x17)  # только кнопка сайта, не знак

NAME = "Тумэн Тур"
LINE = "Байкал · Алтай · Монголия"
FONT_NAME = str(ROOT / "fonts" / "SourceSans3-Bold.ttf")
FONT_LINE = str(ROOT / "fonts" / "SourceSans3-Regular.ttf")
FONT_SEMI = str(ROOT / "fonts" / "SourceSans3-Semibold.ttf")
FONT_UI = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

WAYS = {
    "cvet": (BAIKAL, CREAM),
    "chernyj": (BLACK, WHITE),
    "belyj": (WHITE, DARK),
    "inversiya": (WHITE, BAIKAL),
}


def assert_cyrillic():
    codes = [hex(ord(c)) for c in NAME]
    assert codes == [
        "0x422",
        "0x443",
        "0x43c",
        "0x44d",
        "0x43d",
        "0x20",
        "0x422",
        "0x443",
        "0x440",
    ], codes


def fill_holes(binary: np.ndarray) -> np.ndarray:
    h, w = binary.shape
    inv = ~binary
    seen = np.zeros_like(binary, dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        if inv[0, x]:
            q.append((x, 0))
            seen[0, x] = True
        if inv[h - 1, x]:
            q.append((x, h - 1))
            seen[h - 1, x] = True
    for y in range(h):
        if inv[y, 0]:
            q.append((0, y))
            seen[y, 0] = True
        if inv[y, w - 1]:
            q.append((w - 1, y))
            seen[y, w - 1] = True
    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and inv[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    holes = inv & ~seen
    return binary | holes


def close_1px(binary: np.ndarray) -> np.ndarray:
    im = Image.fromarray((binary.astype(np.uint8) * 255))
    im = im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    return np.array(im) > 128


def extract_site_lake() -> tuple[np.ndarray, tuple[int, int, int, int]]:
    logo = Image.open(LOGO).convert("RGBA")
    arr = np.array(logo)
    r, g, b, a = (arr[:, :, i] for i in range(4))
    blue = (
        (b.astype(np.int16) > r.astype(np.int16) + 28)
        & (b.astype(np.int16) > g.astype(np.int16) + 16)
        & (a > 230)
        & (b.astype(np.int16) > 80)
    )
    h, w = blue.shape
    seen = np.zeros_like(blue, dtype=bool)
    best = None
    best_n = 0
    best_bbox = None
    for y in range(h):
        for x in range(w):
            if not blue[y, x] or seen[y, x]:
                continue
            q = deque([(x, y)])
            seen[y, x] = True
            pts = []
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                for nx, ny in (
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                ):
                    if 0 <= nx < w and 0 <= ny < h and blue[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            # озеро — вытянутый силуэт справа, не круг гор/воды
            bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            cx = sum(xs) / len(pts)
            aspect = bw / max(1, bh)
            if (
                len(pts) > best_n
                and cx > w * 0.45
                and bh > h * 0.55
                and 0.6 < aspect < 1.3
            ):
                best_n = len(pts)
                best = pts
                best_bbox = bbox
    if not best or not best_bbox:
        raise RuntimeError("site lake not found")
    x0, y0, x1, y1 = best_bbox
    pad = 8
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(w - 1, x1 + pad)
    y1 = min(h - 1, y1 + pad)
    crop = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=bool)
    for x, y in best:
        crop[y - y0, x - x0] = True
    crop = fill_holes(crop)
    crop = close_1px(crop)
    crop = open_1px(crop)
    crop = fill_holes(crop)
    crop = largest_cc(crop)
    return crop, (x0, y0, x1, y1)


def open_1px(binary: np.ndarray) -> np.ndarray:
    im = Image.fromarray((binary.astype(np.uint8) * 255))
    im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    return np.array(im) > 128


def largest_cc(binary: np.ndarray) -> np.ndarray:
    h, w = binary.shape
    seen = np.zeros_like(binary, dtype=bool)
    best_pts: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if not binary[y, x] or seen[y, x]:
                continue
            q = deque([(x, y)])
            seen[y, x] = True
            pts = []
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and binary[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            if len(pts) > len(best_pts):
                best_pts = pts
    out = np.zeros_like(binary)
    for x, y in best_pts:
        out[y, x] = True
    return out


def square_pad(binary: np.ndarray, margin: float = 0.08) -> np.ndarray:
    ys, xs = np.where(binary)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    body = binary[y0 : y1 + 1, x0 : x1 + 1]
    bh, bw = body.shape
    side = int(max(bh, bw) / (1 - 2 * margin))
    out = np.zeros((side, side), dtype=bool)
    ox = (side - bw) // 2
    oy = (side - bh) // 2
    out[oy : oy + bh, ox : ox + bw] = body
    return out


def marching_loop(binary: np.ndarray) -> list[tuple[float, float]]:
    """Один замкнутый контур по marching squares. Без дыр — после fill_holes."""
    binary = largest_cc(binary)
    pad = np.pad(binary.astype(np.uint8), 1, constant_values=0)
    h, w = pad.shape
    # midpoints of cell edges, keyed as (ix, iy, edge)
    # case bits: tl=8, tr=4, br=2, bl=1
    table = {
        1: (("W", "S"),),
        2: (("S", "E"),),
        3: (("W", "E"),),
        4: (("N", "E"),),
        5: (("W", "N"), ("S", "E")),
        6: (("N", "S"),),
        7: (("W", "N"),),
        8: (("N", "W"),),
        9: (("N", "S"),),
        10: (("N", "E"), ("W", "S")),
        11: (("N", "E"),),
        12: (("W", "E"),),
        13: (("S", "E"),),
        14: (("W", "S"),),
    }
    mid = {"N": (0.5, 0.0), "E": (1.0, 0.5), "S": (0.5, 1.0), "W": (0.0, 0.5)}

    def pt(cx, cy, edge):
        dx, dy = mid[edge]
        return (round(cx + dx, 2), round(cy + dy, 2))

    adj: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for y in range(h - 1):
        for x in range(w - 1):
            case = (
                (pad[y, x] << 3)
                | (pad[y, x + 1] << 2)
                | (pad[y + 1, x + 1] << 1)
                | pad[y + 1, x]
            )
            if case in table:
                for a, b in table[case]:
                    pa, pb = pt(x, y, a), pt(x, y, b)
                    adj.setdefault(pa, []).append(pb)
                    adj.setdefault(pb, []).append(pa)
    if not adj:
        return []
    start = min(adj, key=lambda p: (p[1], p[0]))
    path = [start]
    prev = None
    used: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    for _ in range(len(adj) + 8):
        cur = path[-1]
        nxts = []
        for nxt in adj[cur]:
            e = (cur, nxt) if cur < nxt else (nxt, cur)
            if e not in used:
                nxts.append(nxt)
        if not nxts:
            break
        nxt = nxts[0]
        if prev is not None and len(nxts) > 1:
            # на седле держим направление
            vx, vy = cur[0] - prev[0], cur[1] - prev[1]
            nxt = max(nxts, key=lambda q: (q[0] - cur[0]) * vx + (q[1] - cur[1]) * vy)
        e = (cur, nxt) if cur < nxt else (nxt, cur)
        used.add(e)
        if nxt == start:
            path.append(nxt)
            break
        path.append(nxt)
        prev = cur
    # снять паддинг
    return [(x - 1.0, y - 1.0) for x, y in path]


def _perp_dist(p, a, b) -> float:
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def rdp(points: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
    if len(points) < 3:
        return list(points)
    start, end = points[0], points[-1]
    idx, dmax = 0, 0.0
    for i in range(1, len(points) - 1):
        d = _perp_dist(points[i], start, end)
        if d > dmax:
            idx, dmax = i, d
    if dmax > eps:
        left = rdp(points[: idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [start, end]


def upsample(binary: np.ndarray, k: int = 3) -> np.ndarray:
    im = Image.fromarray((binary.astype(np.uint8) * 255), "L")
    im = im.resize((binary.shape[1] * k, binary.shape[0] * k), Image.Resampling.NEAREST)
    return np.array(im) > 128


def rdp_target(pts: list[tuple[float, float]], lo=24, hi=40) -> list[tuple[float, float]]:
    """Живой край: 24–40 точек, не пыль PNG и не колбаса."""
    closed = pts[0] == pts[-1]
    body = pts[:-1] if closed else list(pts)
    eps_lo, eps_hi = 0.4, 18.0
    best = body
    for _ in range(22):
        mid = (eps_lo + eps_hi) / 2
        simple = rdp(body + [body[0]], mid)
        if simple[0] == simple[-1]:
            simple = simple[:-1]
        n = len(simple)
        best = simple
        if n > hi:
            eps_lo = mid
        elif n < lo:
            eps_hi = mid
        else:
            break
    if best[0] != best[-1]:
        best = best + [best[0]]
    if not (lo - 4 <= len(best) - 1 <= hi + 8):
        # запас: более грубый проход
        best = rdp(body + [body[0]], 3.2)
        if best[0] != best[-1]:
            best.append(best[0])
    return best


def vectorize(binary: np.ndarray) -> list[tuple[float, float]]:
    hi = upsample(binary, 3)
    raw = marching_loop(hi)
    if len(raw) < 40:
        raise RuntimeError(f"contour too short: {len(raw)}")
    pts = [(x / 3.0, y / 3.0) for x, y in raw]
    return rdp_target(pts, lo=36, hi=42)


def path_to_svg_d(pts: list[tuple[float, float]], scale: float, ox: float, oy: float) -> str:
    """Замкнутый контур кубиками (Catmull–Rom → Bézier), не ломаная из 800 точек."""
    if len(pts) < 4:
        parts = []
        for i, (x, y) in enumerate(pts):
            cmd = "M" if i == 0 else "L"
            parts.append(f"{cmd}{x * scale + ox:.2f},{y * scale + oy:.2f}")
        parts.append("Z")
        return " ".join(parts)
    ring = pts[:-1] if pts[0] == pts[-1] else list(pts)
    n = len(ring)

    def P(i):
        x, y = ring[i % n]
        return (x * scale + ox, y * scale + oy)

    d = [f"M{P(0)[0]:.2f},{P(0)[1]:.2f}"]
    for i in range(n):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 10.0, p1[1] + (p2[1] - p0[1]) / 10.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 10.0, p2[1] - (p3[1] - p1[1]) / 10.0)
        d.append(
            f"C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"
        )
    d.append("Z")
    return " ".join(d)


def fit_path(pts, view=1000, margin=80):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    bw, bh = max(1.0, maxx - minx), max(1.0, maxy - miny)
    usable = view - 2 * margin
    scale = usable / max(bw, bh)
    ox = margin + (usable - bw * scale) / 2 - minx * scale
    oy = margin + (usable - bh * scale) / 2 - miny * scale
    return scale, ox, oy


def sample_closed_cubic(pts: list[tuple[float, float]], steps=6) -> list[tuple[float, float]]:
    """Растр с того же кубика, что в SVG — гладкий край без пиксельной пыли."""
    ring = pts[:-1] if pts and pts[0] == pts[-1] else list(pts)
    n = len(ring)
    if n < 3:
        return list(pts)
    out = []
    for i in range(n):
        p0 = ring[(i - 1) % n]
        p1 = ring[i]
        p2 = ring[(i + 1) % n]
        p3 = ring[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 10.0, p1[1] + (p2[1] - p0[1]) / 10.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 10.0, p2[1] - (p3[1] - p1[1]) / 10.0)
        for s in range(steps):
            t = s / steps
            u = 1 - t
            x = (
                u * u * u * p1[0]
                + 3 * u * u * t * c1[0]
                + 3 * u * t * t * c2[0]
                + t * t * t * p2[0]
            )
            y = (
                u * u * u * p1[1]
                + 3 * u * u * t * c1[1]
                + 3 * u * t * t * c2[1]
                + t * t * t * p2[1]
            )
            out.append((x, y))
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def raster_from_path(pts, size, fill, bg=None, margin=0.10, inflate=0):
    img = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    if len(pts) < 3:
        return img
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    bw, bh = max(1.0, maxx - minx), max(1.0, maxy - miny)
    usable = size * (1 - 2 * margin)
    scale = usable / max(bw, bh)
    ox = (size - bw * scale) / 2 - minx * scale
    oy = (size - bh * scale) / 2 - miny * scale
    poly = [(x * scale + ox, y * scale + oy) for x, y in pts]
    work = size if inflate <= 0 else size + inflate * 4
    if inflate > 0:
        canvas = Image.new("L", (work, work), 0)
        shift = (work - size) / 2
        poly2 = [(x + shift, y + shift) for x, y in poly]
        ImageDraw.Draw(canvas).polygon(poly2, fill=255)
        canvas = canvas.filter(ImageFilter.MaxFilter(inflate * 2 + 1))
        canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
        rgba = np.zeros((size, size, 4), dtype=np.uint8)
        m = np.array(canvas)
        rgba[m > 90] = (*fill, 255)
        layer = Image.fromarray(rgba, "RGBA")
        img.paste(layer, (0, 0), layer)
        return img
    draw = ImageDraw.Draw(img)
    draw.polygon(poly, fill=(*fill, 255))
    return img


def write_znak_svg(pts, path: Path, fill="#124B56", bg=None):
    scale, ox, oy = fit_path(pts)
    d = path_to_svg_d(pts, scale, ox, oy)
    bg_rect = f'<rect width="1000" height="1000" fill="{bg}"/>' if bg else ""
    path.write_text(
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">
  {bg_rect}
  <path fill="{fill}" d="{d}"/>
</svg>
'''
    )


def text_image(text: str, font: ImageFont.FreeTypeFont, fill, tracking=0) -> Image.Image:
    if tracking == 0:
        bb = font.getbbox(text)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 4, -bb[1] + 4), text, font=font, fill=(*fill, 255))
        return im
    glyphs = []
    for ch in text:
        bb = font.getbbox(ch)
        g = Image.new("RGBA", (max(1, bb[2] - bb[0] + 4), bb[3] - bb[1] + 6), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((-bb[0] + 2, -bb[1] + 3), ch, font=font, fill=(*fill, 255))
        glyphs.append(g)
    gap = tracking
    h = max(g.height for g in glyphs)
    w = sum(g.width for g in glyphs) + gap * (len(glyphs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i, g in enumerate(glyphs):
        out.paste(g, (x, (h - g.height) // 2), g)
        x += g.width + (gap if i < len(glyphs) - 1 else 0)
    return out


def wordmark(px: int, fill) -> Image.Image:
    font = ImageFont.truetype(FONT_NAME, px)
    left = text_image("Тумэн", font, fill, tracking=max(1, px // 42))
    right = text_image("Тур", font, fill, tracking=max(1, px // 42))
    gap = max(22, int(px * 0.38))
    h = max(left.height, right.height)
    out = Image.new("RGBA", (left.width + gap + right.width, h), (0, 0, 0, 0))
    out.paste(left, (0, (h - left.height) // 2), left)
    out.paste(right, (left.width + gap, (h - right.height) // 2), right)
    return out


def destline(target_w: int, fill, *, min_px=34, max_px=52) -> Image.Image:
    lo, hi = min_px, max_px
    best = None
    for _ in range(18):
        mid = (lo + hi) // 2
        font = ImageFont.truetype(FONT_SEMI, mid)
        im = text_image(LINE, font, fill, tracking=max(0, mid // 36))
        best = im
        if im.width > target_w * 1.02:
            hi = mid - 1
        elif im.width < target_w * 0.92:
            lo = mid + 1
        else:
            return im
    return best if best is not None else text_image(LINE, ImageFont.truetype(FONT_SEMI, min_px), fill)


def horiz(pts, fill, bg, *, with_line=True, w=1800, h=480):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    name = wordmark(120 if with_line else 128, fill)
    line = destline(name.width, fill) if with_line else None
    if with_line and line is not None:
        text_h = name.height + 18 + line.height
        mark_h = int(text_h * 1.85)
        gap = 52
        block_w = mark_h + gap + max(name.width, line.width)
        x0 = (w - block_w) // 2
        y0 = (h - text_h) // 2
        mark = raster_from_path(pts, mark_h, fill, None, margin=0.02)
        img.paste(mark, (x0, (h - mark_h) // 2), mark)
        tx = x0 + mark_h + gap
        img.paste(name, (tx, y0), name)
        img.paste(line, (tx, y0 + name.height + 18), line)
    else:
        mark_h = int(name.height * 2.75)
        gap = 44
        block_w = mark_h + gap + name.width
        x0 = (w - block_w) // 2
        mark = raster_from_path(pts, mark_h, fill, None, margin=0.02)
        img.paste(mark, (x0, (h - mark_h) // 2), mark)
        img.paste(name, (x0 + mark_h + gap, (h - name.height) // 2), name)
    return img


def vert(pts, fill, bg, w=1000, h=1280):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    mark = raster_from_path(pts, 620, fill, None, margin=0.03)
    name = wordmark(96, fill)
    line = destline(int(name.width * 1.00), fill, min_px=34, max_px=46)
    total = mark.height + 48 + name.height + 14 + line.height
    y = (h - total) // 2
    img.paste(mark, ((w - mark.width) // 2, y), mark)
    y += mark.height + 40
    img.paste(name, ((w - name.width) // 2, y), name)
    y += name.height + 16
    img.paste(line, ((w - line.width) // 2, y), line)
    return img


def slovo(fill, bg, w=1500, h=380):
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    name = wordmark(140, fill)
    img.paste(name, ((w - name.width) // 2, (h - name.height) // 2), name)
    return img


def _stroke_poly(draw, pts, fill, width):
    """Штрих без круглых клякс на концах."""
    if len(pts) < 2:
        return
    half = width / 2.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L * half, dx / L * half
        draw.polygon(
            [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)],
            fill=(*fill, 255),
        )


def pict_altai(size, fill, bg):
    """Три горизонта хребта: лёгкие вздутия, пики не совпадают. Не дом."""
    img = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sw = max(3, size // 42)

    def swell(y, amp, xshift, x0=0.12, x1=0.88, n=18):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = size * (x0 + (x1 - x0) * t)
            # одно мягкое вздутие, не два зубца
            bump = math.sin(math.pi * max(0.0, min(1.0, t * 1.15 - xshift)))
            pts.append((x, size * y - amp * bump * size))
        return pts

    _stroke_poly(d, swell(0.46, 0.055, 0.18, 0.18, 0.84), fill, sw)
    _stroke_poly(d, swell(0.62, 0.070, 0.02, 0.12, 0.88), fill, sw)
    _stroke_poly(d, swell(0.78, 0.018, 0.10, 0.10, 0.90), fill, sw)
    return img


def pict_mongolia(size, fill, bg):
    """Одна линия горизонта. Не юрта, не Соёмбо, не конь."""
    img = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sw = max(3, size // 40)
    _stroke_poly(
        d,
        [
            (size * 0.10, size * 0.57),
            (size * 0.34, size * 0.555),
            (size * 0.58, size * 0.56),
            (size * 0.90, size * 0.55),
        ],
        fill,
        sw,
    )
    return img


def paste_fit(base, overlay, box):
    l, t, r, b = box
    cw, ch = r - l, b - t
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    scale = min(cw / overlay.width, ch / overlay.height)
    nw, nh = max(1, int(overlay.width * scale)), max(1, int(overlay.height * scale))
    overlay = overlay.resize((nw, nh), Image.Resampling.LANCZOS)
    base.paste(overlay, (l + (cw - nw) // 2, t + (ch - nh) // 2), overlay)


def proof_overlay(binary, bbox, pts):
    logo = Image.open(LOGO).convert("RGBA")
    x0, y0, x1, y1 = bbox
    crop = logo.crop((x0, y0, x1 + 1, y1 + 1))
    # оригинал: только озеро в кадре
    arr = np.array(crop)
    lake = np.zeros_like(arr)
    m = binary
    if m.shape[:2] != arr.shape[:2]:
        m = np.array(
            Image.fromarray((binary.astype(np.uint8) * 255)).resize(
                (arr.shape[1], arr.shape[0]), Image.Resampling.NEAREST
            )
        ) > 128
    lake[m] = arr[m]
    orig = Image.fromarray(lake, "RGBA")

    vec = Image.new("RGBA", orig.size, (0, 0, 0, 0))
    ImageDraw.Draw(vec).polygon(pts if pts[0] == pts[-1] else pts + [pts[0]], fill=(0, 0, 0, 255))

    # три панели
    panel_w, panel_h = 720, 780
    board = Image.new("RGB", (panel_w * 3 + 80, panel_h + 120), WHITE)
    lab = ImageFont.truetype(FONT_UI, 22)
    dr = ImageDraw.Draw(board)

    def panel(im, x, title, bg=WHITE):
        cell = Image.new("RGB", (panel_w, panel_h), bg)
        im2 = im.convert("RGBA")
        scale = min((panel_w - 40) / im2.width, (panel_h - 40) / im2.height)
        nw, nh = max(1, int(im2.width * scale)), max(1, int(im2.height * scale))
        im2 = im2.resize((nw, nh), Image.Resampling.NEAREST)
        cell.paste(im2, ((panel_w - nw) // 2, (panel_h - nh) // 2), im2)
        board.paste(cell, (x, 70))
        dr.text((x + 16, 28), title, font=lab, fill=BLACK)

    panel(orig, 20, "1. озеро с logo-saita.png")
    panel(vec, 20 + panel_w + 20, "2. вектор (тот же жест)")

    mix = Image.new("RGBA", orig.size, (255, 255, 255, 255))
    o = np.array(orig)
    v = np.array(vec)
    over = np.ones_like(o)
    over[:, :, 0] = 255
    over[:, :, 1] = 255
    over[:, :, 2] = 255
    over[:, :, 3] = 255
    on = o[:, :, 3] > 40
    vn = v[:, :, 3] > 40
    over[on & ~vn] = (220, 40, 40, 255)  # оригинал без вектора
    over[vn & ~on] = (20, 140, 200, 255)  # вектор без оригинала
    over[on & vn] = (20, 20, 20, 255)
    panel(Image.fromarray(over, "RGBA"), 20 + 2 * (panel_w + 20), "3. красный=сайт, голубой=лишнее")
    board.save(PROOF / "A-naklozhenie.png")


def proof_40mm(pts):
    frame = Image.new("RGB", (1200, 1200), WHITE)
    mark = raster_from_path(pts, 620, BLACK, None, margin=0.04)
    frame.paste(mark, ((1200 - mark.width) // 2, 220), mark)
    d = ImageDraw.Draw(frame)
    font = ImageFont.truetype(FONT_UI, 22)
    d.rectangle((360, 1080, 840, 1086), fill=BLACK)
    d.text((360, 1096), "40 mm  —  контур с tumentur.ru, чёрный", font=font, fill=(90, 90, 90))
    frame.save(PROOF / "A-chernyj-40mm.png")
    raster_from_path(pts, 1024, BLACK, WHITE, margin=0.10).save(PNG / "01-znak-chernyj-na-belom.png")
    raster_from_path(pts, 1024, BLACK, WHITE, margin=0.10).save(SRC / "kontur-s-saita-chernyj.png")


def horiz_at(pts, fill, *, with_line, name_px, mark_h, gap, dest_px=None):
    name = wordmark(name_px, fill)
    line = None
    if with_line:
        font = ImageFont.truetype(FONT_SEMI, dest_px or max(14, int(name_px * 0.48)))
        line = text_image(LINE, font, fill, tracking=0)
        # если линейка заметно короче имени — чуть раздвинуть
        if line.width < name.width * 0.92:
            extra = max(0, int((name.width - line.width) / max(1, len(LINE) - 1)))
            line = text_image(LINE, font, fill, tracking=max(1, extra))
    text_h = name.height + (14 + line.height if line is not None else 0)
    h = max(mark_h, text_h) + 8
    w = mark_h + gap + (max(name.width, line.width if line is not None else 0)) + 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mark = raster_from_path(pts, mark_h, fill, None, margin=0.02)
    img.paste(mark, (0, (h - mark_h) // 2), mark)
    tx = mark_h + gap
    ty = (h - text_h) // 2
    img.paste(name, (tx, ty), name)
    if line is not None:
        img.paste(line, (tx, ty + name.height + 8), line)
    return img


def proof_header(pts):
    """Шапка = знак+имя. Бланк = + линейка читаемым кеглем."""
    bar = Image.new("RGB", (1440, 88), CREAM)
    lock = horiz_at(pts, BAIKAL, with_line=False, name_px=28, mark_h=72, gap=14)
    bar.paste(lock, (24, (88 - lock.height) // 2), lock)
    d = ImageDraw.Draw(bar)
    d.rounded_rectangle((1220, 24, 1408, 64), radius=8, fill=ORANGE)
    f = ImageFont.truetype(FONT_UI, 16)
    d.text((1250, 34), "Оставить заявку", font=f, fill=WHITE)
    bar.save(PROOF / "C-shapaka-bez-linejki.png")
    bar.save(PROOF / "C-shapaka-linejka.png")

    bar2 = Image.new("RGB", (390, 64), CREAM)
    lock2 = horiz_at(pts, BAIKAL, with_line=False, name_px=22, mark_h=48, gap=12)
    bar2.paste(lock2, (10, (64 - lock2.height) // 2), lock2)
    bar2.save(PROOF / "C-mobil-bez-linejki.png")

    blank = Image.new("RGB", (1440, 220), WHITE)
    lock3 = horiz_at(pts, BAIKAL, with_line=True, name_px=36, mark_h=96, gap=20, dest_px=16)
    blank.paste(lock3, (48, (220 - lock3.height) // 2), lock3)
    ImageDraw.Draw(blank).text(
        (48, 16),
        "бланк — линейка только здесь",
        font=ImageFont.truetype(FONT_UI, 16),
        fill=(90, 90, 90),
    )
    blank.save(PROOF / "C-blank-linejka.png")

    cmp = Image.new("RGB", (1600, 280), CREAM)
    old = horiz_at(pts, BAIKAL, with_line=False, name_px=26, mark_h=40, gap=18)
    new = horiz_at(pts, BAIKAL, with_line=False, name_px=28, mark_h=72, gap=14)
    lab = ImageFont.truetype(FONT_UI, 18)
    ImageDraw.Draw(cmp).text((40, 16), "шапка было (росчерк)", font=lab, fill=BAIKAL)
    ImageDraw.Draw(cmp).text((40, 150), "шапка стало (пятно знака)", font=lab, fill=BAIKAL)
    cmp.paste(old, (40, 48), old)
    cmp.paste(new, (40, 186), new)
    cmp.save(PROOF / "C-shapaka-bylo-stalo.png")


def proof_scales(pts):
    row = Image.new("RGB", (720, 160), WHITE)
    x = 24
    for s in (16, 24, 32, 48):
        inf = 2 if s <= 24 else 1
        m = raster_from_path(pts, s, BLACK, WHITE, margin=0.04, inflate=inf)
        cell = Image.new("RGB", (s + 16, s + 16), (235, 235, 235))
        cell.paste(m, (8, 8))
        row.paste(cell, (x, 48))
        ImageDraw.Draw(row).text((x, 16), f"{s} px", font=ImageFont.truetype(FONT_UI, 16), fill=(80, 80, 80))
        x += s + 48
    row.save(PROOF / "A-16-24-32.png")


def proof_dark_and_risks(pts):
    board = Image.new("RGB", (1600, 900), DARK)
    d = ImageDraw.Draw(board)
    f = ImageFont.truetype(FONT_UI, 22)
    f2 = ImageFont.truetype(FONT_LINE, 18)
    mark = raster_from_path(pts, 420, WHITE, None, margin=0.08)
    board.paste(mark, (80, 80), mark)
    lock = horiz(pts, WHITE, None, with_line=True, w=1000, h=280)
    board.paste(lock, (520, 120), lock)
    d.text((80, 540), "D. три риска (без новой метафоры)", font=f, fill=WHITE)
    risks = [
        "1. 24 px — галочка. Байкал узнают не все. Держит имя, не дорисованные горы.",
        "2. Контур озера есть и у ББТ (там — круг-мозаика). Здесь — один силуэт, без круга.",
        "3. Линейка «Байкал · Алтай · Монголия» может прочесться как слоган. Она мельче имени и снаружи знака.",
    ]
    y = 590
    for t in risks:
        d.text((80, y), t, font=f2, fill=(210, 220, 220))
        y += 42
    board.save(PROOF / "D-temnyj-i-riski.png")


def sistema_obzor(pts):
    ov = Image.new("RGB", (2000, 1320), CREAM)
    d = ImageDraw.Draw(ov)
    f = ImageFont.truetype(FONT_UI, 20)

    cells = [
        ((40, 50, 420, 430), PNG / "01-znak-cvet.png", "1. знак"),
        ((450, 50, 1320, 320), PNG / "02-gorizont-linejka-cvet.png", "2. горизонталь с линейкой"),
        ((1340, 50, 1960, 320), PNG / "03-gorizont-mobil-cvet.png", "3. без линейки"),
        ((450, 360, 1100, 880), PNG / "04-vertikal-cvet.png", "4. вертикаль"),
        ((1120, 360, 1960, 620), PNG / "05-slovo-cvet.png", "5. только имя"),
        ((40, 470, 200, 630), PNG / "06-znak-24.png", "6. 24 px"),
        ((210, 470, 420, 630), PNG / "06-znak-32.png", "32 px"),
        ((1120, 660, 1520, 1020), PNG / "08-altai.png", "8. Алтай — не в знаке"),
        ((1540, 660, 1960, 1020), PNG / "08-mongolia.png", "8. Монголия — не в знаке"),
        ((40, 900, 420, 1280), PNG / "01-znak-inversiya.png", "инверсия"),
        ((450, 920, 1100, 1280), PNG / "02-gorizont-linejka-inversiya.png", ""),
        ((1120, 1060, 1960, 1280), PNG / "02-gorizont-linejka-belyj.png", ""),
    ]
    for box, path, label in cells:
        if not path.exists():
            continue
        im = Image.open(path).convert("RGBA")
        dark = "invers" in path.name or "belyj" in path.name
        d.rectangle(box, fill=DARK if dark else WHITE)
        paste_fit(ov, im, box)
        if label:
            d.text((box[0], box[1] - 26), label, font=f, fill=BAIKAL)
    ov.save(PNG / "00-sistema-obzor.png")


def save_mask(binary: np.ndarray):
    sq = square_pad(binary, 0.10)
    Image.fromarray((sq.astype(np.uint8) * 255), "L").save(SRC / "site-baikal-mask.png")


def _reject_tofu(im: Image.Image, label: str):
    # .notdef Public Sans давал широкую гребенку пустых боксов
    if im.width > 2400:
        raise RuntimeError(f"possible tofu in {label}: width={im.width}")


STALE = [
    "02-gorizont-cvet.png",
    "02-gorizont-chernyj.png",
    "02-gorizont-belyj.png",
    "02-gorizont-inversiya.png",
    "03-vertikal-cvet.png",
    "03-vertikal-chernyj.png",
    "03-vertikal-belyj.png",
    "03-vertikal-inversiya.png",
    "04-slovo-cvet.png",
    "04-slovo-chernyj.png",
    "04-slovo-belyj.png",
    "04-slovo-inversiya.png",
]


def main():
    assert_cyrillic()
    probe = wordmark(80, BLACK)
    _reject_tofu(probe, "wordmark")
    for name in STALE:
        p = PNG / name
        if p.exists():
            p.unlink()
    binary, bbox = extract_site_lake()
    save_mask(binary)
    pts = vectorize(binary)

    write_znak_svg(pts, SVG / "znak.svg", "#124B56")
    write_znak_svg(pts, SVG / "znak-chernyj.svg", "#111111", "#FFFFFF")
    write_znak_svg(pts, SVG / "znak-belyj.svg", "#FFFFFF", "#0C2C30")
    write_znak_svg(pts, SVG / "znak-inversiya.svg", "#FFFFFF", "#124B56")

    raster_from_path(pts, 1024, BAIKAL, WHITE, margin=0.10).save(PNG / "01-znak-cvet-na-belom.png")
    raster_from_path(pts, 1024, BAIKAL, CREAM, margin=0.10).save(PNG / "01-znak-cvet-na-svetlom.png")
    raster_from_path(pts, 1024, WHITE, DARK, margin=0.10).save(PNG / "01-znak-belyj-na-temnom.png")
    raster_from_path(pts, 1024, BAIKAL, DARK, margin=0.10).save(PNG / "01-znak-cvet-na-temnom.png")

    for key, (fg, bg) in WAYS.items():
        raster_from_path(pts, 1024, fg, bg, margin=0.10).save(PNG / f"01-znak-{key}.png")
        horiz(pts, fg, bg, with_line=True).save(PNG / f"02-gorizont-linejka-{key}.png")
        horiz(pts, fg, bg, with_line=False, h=400).save(PNG / f"03-gorizont-mobil-{key}.png")
        vert(pts, fg, bg).save(PNG / f"04-vertikal-{key}.png")
        slovo(fg, bg).save(PNG / f"05-slovo-{key}.png")

    for s in (16, 24, 32, 48):
        inflate = 2 if s <= 24 else 1
        raster_from_path(pts, s, BAIKAL, None, margin=0.04, inflate=inflate).save(PNG / f"06-znak-{s}.png")
        raster_from_path(pts, s, BLACK, WHITE, margin=0.04, inflate=inflate).save(PROOF / f"znak-{s}.png")
        raster_from_path(pts, s, WHITE, BAIKAL, margin=0.10, inflate=2).save(PNG / f"05-avatar-{s}.png")
    raster_from_path(pts, 256, WHITE, BAIKAL, margin=0.12, inflate=2).save(PNG / "07-avatar-telegram.png")
    raster_from_path(pts, 256, WHITE, BAIKAL, margin=0.12, inflate=2).save(PNG / "07-pechat.png")

    pict_altai(640, BAIKAL, CREAM).save(PNG / "08-altai.png")
    pict_mongolia(640, BAIKAL, CREAM).save(PNG / "08-mongolia.png")
    sister = Image.new("RGB", (1400, 720), CREAM)
    a = pict_altai(560, BAIKAL, CREAM)
    m = pict_mongolia(560, BAIKAL, CREAM)
    sister.paste(a, (80, 80))
    sister.paste(m, (760, 80))
    dr = ImageDraw.Draw(sister)
    f = ImageFont.truetype(FONT_UI, 22)
    dr.text((80, 40), "Алтай — страница направления", font=f, fill=BAIKAL)
    dr.text((760, 40), "Монголия — страница направления", font=f, fill=BAIKAL)
    sister.save(PNG / "08-piktogrammy.png")

    proof_overlay(binary, bbox, pts)
    proof_40mm(pts)
    proof_header(pts)
    proof_scales(pts)
    proof_dark_and_risks(pts)
    sistema_obzor(pts)

    # unicode check strip
    strip = Image.new("RGB", (1100, 200), WHITE)
    wm = wordmark(72, BLACK)
    strip.paste(wm, (60, 50), wm)
    ImageDraw.Draw(strip).text(
        (60, 150),
        "U+0422 U+0443 U+043C U+044D U+043D  U+0422 U+0443 U+0440",
        font=ImageFont.truetype(FONT_UI, 16),
        fill=(90, 90, 90),
    )
    strip.save(PROOF / "B-imya-unicode.png")
    print("pts", len(pts) - (1 if pts and pts[0] == pts[-1] else 0), "bbox", bbox, "mask", binary.sum())


if __name__ == "__main__":
    main()
