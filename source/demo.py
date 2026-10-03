#!/usr/bin/env python3
"""renders/articulation_demo.png from the four posed renders (head and tail never move; only the two torso joints do)."""
import os
from PIL import Image, ImageDraw, ImageFont
import params as Q
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = int(Q.YAW_RANGE)
labs = ["1. straight", f"2. joint 1 (rear | middle) bent {R}°", f"3. joint 2 (middle | front) bent {R}°", f"4. both joints bent ({2 * R}° curve)"]
ims = [Image.open(f"{ROOT}/renders/demo_{i}.png").convert("RGB") for i in range(4)]
w, h = ims[0].size; top = int(h * 0.09)
out = Image.new("RGB", (2 * w + 20, 2 * (h + top) + 20), (255, 255, 255)); d = ImageDraw.Draw(out)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(h * 0.045))
for i, (im, lab) in enumerate(zip(ims, labs)):
    x = (i % 2) * (w + 20); y = (i // 2) * (h + top + 20)
    out.paste(im, (x, y + top)); d.text((x + 12, y + int(top * 0.22)), lab, fill=(20, 20, 20), font=f)
out.save(f"{ROOT}/renders/articulation_demo.png")
out.resize((1200, int(1200 * out.height / out.width)), Image.LANCZOS).save(f"{ROOT}/build/demo_small.png")
