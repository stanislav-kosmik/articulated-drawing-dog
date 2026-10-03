#!/usr/bin/env python3
"""renders/presentation.png : SOURCE DRAWING -> FINISHED 3D DOG (the source file itself is never modified)."""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src = Image.open(f"{ROOT}/source_drawing.jpg").convert("RGB").crop((60, 250, 1110, 1130))
ref = Image.open(f"{ROOT}/renders/reference_side.png").convert("RGB")
hero = Image.open(f"{ROOT}/renders/hero.png").convert("RGB")
H = 900
def fit(im): return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
tiles = [fit(src), fit(ref), fit(hero)]
gap = 110
W = sum(t.width for t in tiles) + gap * 2 + 80
out = Image.new("RGB", (W, H + 170), (250, 249, 246))
d = ImageDraw.Draw(out)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
x = 40
for i, (t, lab) in enumerate(zip(tiles, ["the drawing", "same view, 3D model", "posed render: head + tail move"])):
    out.paste(t, (x, 110)); d.text((x + 6, 40), lab, fill=(40, 40, 40), font=f)
    x += t.width
    if i < 2:
        cy = 110 + H // 2
        d.line([(x + 22, cy), (x + gap - 30, cy)], fill=(60, 60, 60), width=10)
        d.polygon([(x + gap - 38, cy - 24), (x + gap - 8, cy), (x + gap - 38, cy + 24)], fill=(60, 60, 60))
        x += gap
out.save(f"{ROOT}/renders/presentation.png")
out.resize((out.width // 3, out.height // 3)).save(f"{ROOT}/build/presentation_small.png")
