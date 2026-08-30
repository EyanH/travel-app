"""Generate the PWA app icons (compass mark) with no third-party deps.

Pure-Python PNG writer + supersampled rasteriser. Run from the repo root:
    python tools/make_icons.py
"""
import math
import os
import struct
import zlib

BG = (17, 21, 29)        # --elev
RING = (120, 187, 255)   # --accent
NEEDLE_N = (244, 119, 106)  # --bad (north tip, like a real compass)
NEEDLE_S = (238, 242, 247)  # --text
SS = 3                   # supersampling factor


def _rounded_alpha(x, y, n, radius):
    """Coverage of a rounded square covering the whole canvas."""
    if radius <= 0:
        return 1.0
    cx = min(max(x, radius), n - radius)
    cy = min(max(y, radius), n - radius)
    dx, dy = x - cx, y - cy
    if dx == 0 and dy == 0:
        return 1.0
    return 1.0 if math.hypot(dx, dy) <= radius else 0.0


def _in_triangle(px, py, a, b, c):
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1 = sign((px, py), a, b)
    d2 = sign((px, py), b, c)
    d3 = sign((px, py), c, a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def _rot(px, py, cx, cy, ang):
    s, c = math.sin(ang), math.cos(ang)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)


def render(size, rounded=True, inset=0.0):
    """Return RGBA bytes for one icon."""
    n = size * SS
    radius = (n * 0.22) if rounded else 0.0
    cx = cy = n / 2.0
    scale = 1.0 - inset                      # inset shrinks the mark for maskable safe zone
    r_out = n * 0.335 * scale
    r_in = n * 0.275 * scale
    ang = math.radians(-40)                  # tilt the needle so it reads as a compass
    half = n * 0.085 * scale                 # needle half-width
    tip = n * 0.235 * scale                  # needle half-length

    px_n = _rot(cx, cy - tip, cx, cy, ang)
    px_s = _rot(cx, cy + tip, cx, cy, ang)
    px_e = _rot(cx + half, cy, cx, cy, ang)
    px_w = _rot(cx - half, cy, cx, cy, ang)

    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            ar = ag = ab = aa = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    fx = x * SS + sx + 0.5
                    fy = y * SS + sy + 0.5
                    cov = _rounded_alpha(fx, fy, n, radius)
                    if cov <= 0:
                        continue
                    r, g, b = BG
                    d = math.hypot(fx - cx, fy - cy)
                    if r_in <= d <= r_out:
                        r, g, b = RING
                    elif _in_triangle(fx, fy, px_n, px_e, px_w):
                        r, g, b = NEEDLE_N
                    elif _in_triangle(fx, fy, px_s, px_e, px_w):
                        r, g, b = NEEDLE_S
                    ar += r; ag += g; ab += b; aa += 255.0
            k = SS * SS
            if aa == 0:
                row += bytes((0, 0, 0, 0))
            else:
                cnt = aa / 255.0
                row += bytes((int(ar / cnt), int(ag / cnt), int(ab / cnt), int(aa / k)))
        rows.append(bytes(row))
    return rows


def write_png(path, rows, size):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")
    os.makedirs(out, exist_ok=True)
    targets = [
        ("icon-192.png", 192, True, 0.0),
        ("icon-512.png", 512, True, 0.0),
        ("icon-maskable-512.png", 512, False, 0.18),  # full bleed + safe zone
        ("apple-touch-icon.png", 180, False, 0.0),    # iOS applies its own mask
    ]
    for name, size, rounded, inset in targets:
        write_png(os.path.join(out, name), render(size, rounded, inset), size)
