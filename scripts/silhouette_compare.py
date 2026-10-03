#!/usr/bin/env python3
"""Overlay the model's reference-side silhouette on the source drawing (drawing is not modified)."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_erosion, map_coordinates
import params as P
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src = Image.open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source_drawing.jpg")).convert("RGB")
W, H = src.size
d = np.load(f"{ROOT}/build/silhouettes.npz")
py, px = np.mgrid[0:H, 0:W]
xm = (px - 125) * P.PX; zm = (1060 - py) * P.PX
cols = dict(body=(230, 60, 40), head=(30, 110, 230), tail=(20, 160, 70))
over = np.asarray(src).astype(np.float32).copy()
fill = over.copy()
union = np.zeros((H, W), bool)
for n, c in cols.items():
    x, z, s = d[f"{n}_x"], d[f"{n}_z"], d[f"{n}_sil"].astype(np.float32)
    i = (xm - x[0]) / (x[1] - x[0]); k = (zm - z[0]) / (z[1] - z[0])
    m = map_coordinates(s, [i, k], order=1, cval=0) > 0.5
    union |= m
    edge = m & ~binary_erosion(m, iterations=3)
    fill[m] = fill[m] * 0.72 + np.array(c) * 0.28
    fill[edge] = c
a = Image.fromarray(np.asarray(src)); b = Image.fromarray(fill.astype(np.uint8))
sil = Image.fromarray(np.where(union[..., None], np.array([40, 40, 46]), np.array([245, 243, 238])).astype(np.uint8))
crop = (60, 280, 1110, 1120)
tiles = [im.crop(crop) for im in (a, b, sil)]
w, h = tiles[0].size
out = Image.new("RGB", (w * 3 + 40, h + 60), (255, 255, 255))
dr = ImageDraw.Draw(out)
try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
except Exception: f = ImageFont.load_default()
for j, (t, lab) in enumerate(zip(tiles, ["source drawing", "model silhouette overlaid (body / head / tail)", "model silhouette"])):
    out.paste(t, (j * (w + 20), 60)); dr.text((j * (w + 20) + 10, 12), lab, fill=(20, 20, 20), font=f)
out.save(f"{ROOT}/renders/silhouette_comparison.png")
out.resize((out.width // 2, out.height // 2)).save(f"{ROOT}/build/sil_small.png")
