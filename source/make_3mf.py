#!/usr/bin/env python3
"""dog_print.3mf: rear, middle and front on one plate in their print orientations."""
import os, trimesh
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sc = trimesh.Scene(); x = 0.0
for n in ("rear", "middle", "front"):
    m = trimesh.load(f"{ROOT}/stl/{n}.stl", process=True)
    lo, hi = m.bounds
    m.apply_translation([x - lo[0], -(lo[1] + hi[1]) / 2, -lo[2]]); x += (hi[0] - lo[0]) + 12
    sc.add_geometry(m, node_name=n, geom_name=n)
sc.export(f"{ROOT}/dog_print.3mf")
chk = trimesh.load(f"{ROOT}/dog_print.3mf")
print("3mf objects:", {k: (len(g.faces), g.is_watertight) for k, g in chk.geometry.items()}, "extent", chk.extents.round(1))
