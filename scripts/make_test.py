#!/usr/bin/env python3
"""Optional joint tolerance test: small and contains the real joint geometry.
 - socket block with three head sockets: radial clearance 0.00 / 0.10 (production) / 0.20 mm (1 / 2 / 3 notches)
 - slotted ball stud identical to the one on the body
 - tail bore block (production bore) + tail peg stub with handle (production peg)
All four pieces are laid out in print orientation in one STL."""
import os, numpy as np, trimesh
from manifold3d import Manifold
import params as P, generate as G
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs(f"{ROOT}/test", exist_ok=True)
cx, cy, cz = P.BALL_C
pitch = 17.5
# --- socket block (printed mouth-down exactly like the head)
block = Manifold.cube((3 * pitch, 17.5, 19.6)).translate((cx - 1.5 * pitch, -8.75, P.HEAD_BOTTOM_Z))
for i, c in enumerate((0.0, 0.10, 0.20)):
    s, _ = G.socket_cutter(c)
    dx = (i - 1) * pitch
    block -= s.translate((dx, 0, 0))
    for k in range(i + 1):  # identification notches on the long side
        block -= Manifold.cube((1.2, 1.2, 30), True).translate((cx + dx - 3 + 3 * k, -8.75, P.HEAD_BOTTOM_Z + 10))
block = block.translate((-cx, 0, -P.HEAD_BOTTOM_Z))
# --- ball stud on a base (identical stud, moat and slot as on the body)
base = Manifold.cylinder(53.8 - 48.0, 9, 9, 96).translate((cx, cy, 48.0))
stud = G.add_stud(base).translate((-cx, 28, -48.0))
# --- tail bore block
ax_x, ax_y = P.TAIL_AXIS
bore, _ = G.tail_bore()
bb = Manifold.cube((17, 17, 24)).translate((ax_x - 8.5, -8.5, P.SEAT_Z - 24)) - bore
bb = bb.translate((-ax_x + 30, 28, -(P.SEAT_Z - 24)))
# --- tail peg stub with handle (printed on its side like the tail)
peg, _ = G.tail_peg()
handle = Manifold.cube((14, 2 * P.TAIL_HALF_W, 16)).translate((ax_x - 7, -P.TAIL_HALF_W, P.TAIL_ROOT_Z))
pg = (peg + handle).translate((-ax_x, 0, -P.TAIL_ROOT_Z)).rotate((90, 0, 0)).translate((-28, 40, P.TAIL_HALF_W))
allp = Manifold.compose([block, stud, bb, pg])
m = allp.to_mesh()
trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False).export(f"{ROOT}/test/joint_tolerance_test.stl")
print("test piece bbox", allp.bounding_box(), "components", len(allp.decompose()))
