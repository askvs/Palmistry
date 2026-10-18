import math, os
from PIL import Image, ImageDraw

VIOLET_A, VIOLET_B = (124, 58, 237), (109, 40, 217)
GOLD, INK_A, INK_B = (252, 211, 77), (30, 24, 54), (15, 12, 41)
OUT = os.path.join(os.path.dirname(__file__), "..", "public")

def rounded_tile(size, radius_ratio=0.22):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(size - 1, 1)
        color = tuple(int(VIOLET_A[i] + (VIOLET_B[i] - VIOLET_A[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (size, y)], fill=color)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=size * radius_ratio, fill=255)
    img.putalpha(mask)
    return img

def star4(d, cx, cy, r_out, r_in, fill):
    pts = []
    for i in range(8):
        ang = math.pi / 2 * (i / 2) + (0 if i % 2 == 0 else math.pi / 4)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang) + r * 0))  # screen y down
    d.polygon(pts, fill=fill)

def icon(size):
    img = rounded_tile(size)
    d = ImageDraw.Draw(img)
    star4(d, size / 2, size / 2, size * 0.28, size * 0.085, GOLD + (255,))
    return img

icon(512).save(os.path.join(OUT, "icon-512.png"))
icon(192).save(os.path.join(OUT, "icon-192.png"))
icon(180).save(os.path.join(OUT, "icon-180.png"))
icon(64).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

og = Image.new("RGB", (1200, 630), INK_A)
d = ImageDraw.Draw(og)
for y in range(630):
    t = y / 629
    d.line([(0, y), (1200, y)], fill=tuple(int(INK_A[i] + (INK_B[i] - INK_A[i]) * t) for i in range(3)))
d.line([(120, 315), (1080, 315)], fill=(233, 180, 76))
star4(d, 600, 200, 46, 14, GOLD)
try:
    from PIL import ImageFont
    font = ImageFont.truetype(r"C:\Windows\Fonts\georgia.ttf", 44)
    d.text((600, 380), "Self-insight, beautifully decoded.", font=font, fill=(237, 233, 254), anchor="mm")
except Exception:
    pass  # text optional; mark + hairline carry the OG
og.save(os.path.join(OUT, "og-default.png"))
print("Brand assets written to", os.path.abspath(OUT))
