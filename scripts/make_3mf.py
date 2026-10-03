#!/usr/bin/env python3
"""dog_print.3mf : the three production parts laid out on one plate in their print orientations."""
import os, trimesh, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sc = trimesh.Scene()
layout = {"body": (0, 0), "head": (8, 32), "tail": (62, 30)}
for n, (dx, dy) in layout.items():
    m = trimesh.load(f"{ROOT}/stl/{n}.stl", process=True)
    lo = m.bounds[0]
    if n != "body": m.apply_translation([-lo[0] + dx, -lo[1] + dy + 16.5, -lo[2]])
    m.metadata["name"] = n
    sc.add_geometry(m, node_name=n, geom_name=n)
sc.export(f"{ROOT}/dog_print.3mf")
chk = trimesh.load(f"{ROOT}/dog_print.3mf")
print("3mf objects:", {k: (len(g.faces), g.is_watertight) for k, g in chk.geometry.items()}, "extent", chk.extents.round(1))
