#!/usr/bin/env python3
"""renders/source_vs_model.png: LEFT original drawing | CENTER model side render | RIGHT silhouette overlay.
The silhouette is rasterised from the final assembled meshes (not from any intermediate data)."""
import os, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_erosion
import params as Q
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CROP = (60, 290, 1100, 1090)
src = Image.open(f"{ROOT}/source_drawing.jpg").convert("RGB")
W, Hh = src.size
cols = dict(rear=(225, 60, 40), middle=(30, 150, 70), front=(30, 100, 230))
masks = {}
for n in cols:
    f = "middle_installed" if n == "middle" else f"{n}_assembled"
    tm = trimesh.load(f"{ROOT}/build/{f}.stl")
    px = tm.vertices[:, 0] / Q.S + Q.X0; py = Q.Y0 - tm.vertices[:, 2] / Q.S
    im = Image.new("L", (W, Hh), 0); d = ImageDraw.Draw(im)
    for a, b, c in tm.faces:
        d.polygon([(px[a], py[a]), (px[b], py[b]), (px[c], py[c])], fill=255)
    masks[n] = np.asarray(im) > 0
over = np.asarray(src).astype(np.float32).copy()
union = np.zeros((Hh, W), bool)
for n, c in cols.items():
    m = masks[n]; union |= m
    over[m] = over[m] * 0.62 + np.array(c) * 0.38
for n, c in cols.items():
    m = masks[n]; over[m & ~binary_erosion(m, iterations=2)] = c
left = src.crop(CROP); right = Image.fromarray(over.astype(np.uint8)).crop(CROP)
center = Image.open(f"{ROOT}/renders/side.png").convert("RGB").resize(left.size, Image.LANCZOS)
w, h = left.size; gap = 24; top = 78
out = Image.new("RGB", (3 * w + 2 * gap, h + top), (255, 255, 255)); dr = ImageDraw.Draw(out)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
for j, (t, lab) in enumerate(zip((left, center, right), ("original drawing", "3D model, same side view (render)", "model silhouette over the drawing  (rear / middle / front)"))):
    out.paste(t, (j * (w + gap), top)); dr.text((j * (w + gap) + 10, 20), lab, fill=(20, 20, 20), font=f)
out.save(f"{ROOT}/renders/source_vs_model.png")
out.resize((out.width * 2 // 5, out.height * 2 // 5), Image.LANCZOS).save(f"{ROOT}/build/svm_small.png")
# numeric agreement inside the crop: model silhouette vs. a hand-traced reference is not available, so report coverage only
print("silhouette area mm2:", round(float(union.sum()) * Q.S ** 2, 1))
