#!/usr/bin/env python3
"""Procedural generator, version 2: REAR | MIDDLE | FRONT with two vertical-axis snap pivots.

1. The side silhouette traced from the drawing (params.py, image pixels) is extruded and softly rounded as a
   signed-distance field -> one continuous dog.
2. The dog is cut by two vertical cylindrical seams (concentric with the pivot axes) into rear / middle / front.
3. A 45-degree self-support pass removes anything that could not be printed upright without support.
4. Joint geometry (post, C-clip tongue, pocket) is added with exact CSG (manifold3d).

Usage: python3 generate.py
"""
import os, json, sys
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, distance_transform_edt
from skimage import measure
import manifold3d as m3
from manifold3d import Manifold, CrossSection
import trimesh
import params as Q

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEG = 128
H = Q.VOXEL
ZB = Q.fz(Q.BELLY_PY)                       # underside of the tongues / belly of the rear and front stubs
ZM = Q.fz(Q.MID_BELLY_PY)                   # belly of the (deeper) middle piece
XSA, XSB = Q.fx(Q.SEAM_A_PX), Q.fx(Q.SEAM_B_PX)
SETBACK = Q.SEAM_R - np.sqrt(Q.SEAM_R ** 2 - Q.BODY_HALF_W ** 2)
XA = XSA + SETBACK - Q.SEAM_R               # pivot A (rear <-> middle), inside the rear section
XB = XSB - SETBACK + Q.SEAM_R               # pivot B (middle <-> front), inside the front section
Z_FLOOR = ZB - Q.FLOOR_CLEAR
Z_CEIL = ZB + Q.TONGUE_T + Q.CEIL_CLEAR
CLIP_RI = Q.POST_R - Q.CLIP_PRELOAD
CLIP_RO = CLIP_RI + Q.CLIP_T


# ----------------------------------------------------------------------------- SDF helpers
def sd_poly(X, Z, pts):
    pts = np.asarray(pts, np.float32)
    d = np.full(X.shape, 1e9, np.float32); s = np.ones(X.shape, np.float32)
    for i in range(len(pts)):
        a = pts[i]; b = pts[i - 1]
        ex, ez = b[0] - a[0], b[1] - a[1]
        wx, wz = X - a[0], Z - a[1]
        t = np.clip((wx * ex + wz * ez) / (ex * ex + ez * ez), 0, 1)
        bx, bz = wx - ex * t, wz - ez * t
        d = np.minimum(d, bx * bx + bz * bz)
        c1 = Z >= a[1]; c2 = Z < b[1]; c3 = ex * wz > ez * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
    return s * np.sqrt(d)

def extrude(d2, ydist, half, r):
    w0 = d2 + r; w1 = ydist - (half - r)
    return np.minimum(np.maximum(w0, w1), 0) + np.hypot(np.maximum(w0, 0), np.maximum(w1, 0)) - r

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)

def sd_cone_capsule(x, y, z, a, b, ra, rb):
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32); e = b - a
    t = np.clip(((x - a[0]) * e[0] + (y - a[1]) * e[1] + (z - a[2]) * e[2]) / (e @ e), 0, 1)
    return np.sqrt((x - a[0] - e[0] * t) ** 2 + (y - a[1] - e[1] * t) ** 2 + (z - a[2] - e[2] * t) ** 2) - (ra + (rb - ra) * t)

def to_manifold(F, ax, name):
    v, f, _, _ = measure.marching_cubes(F, level=0.0, spacing=(H, H, H))
    v = v + np.array([ax[0][0], ax[1][0], ax[2][0]], np.float32)
    tm = trimesh.Trimesh(v, f, process=True)
    if tm.volume < 0: tm.invert()
    mesh = m3.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32))
    mesh.merge()
    man = Manifold(mesh)
    assert man.status() == m3.Error.NoError, (name, man.status())
    parts = man.decompose()
    if len(parts) > 1:
        parts.sort(key=lambda p: -p.volume())
        print(f"  [{name}] dropped {len(parts) - 1} islands, volumes", [round(p.volume(), 3) for p in parts[1:]])
        man = parts[0]
    n0 = man.num_tri(); man = man.simplify(Q.SIMPLIFY_TOL)
    print(f"  [{name}] tris {n0} -> {man.num_tri()}  vol {man.volume() / 1000:.1f} cm3")
    return man


# ----------------------------------------------------------------------------- the continuous dog
def dog_field():
    ax = [np.arange(lo, hi + H / 2, H, dtype=np.float32) for lo, hi in ((-4, 155), (-17.2, 17.2), (-2.4, 117.2))]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    x2, z2 = X[:, 0, :], Z[:, 0, :]
    aY = np.abs(Y)
    def ex(px, half, r, yd=aY): return extrude(sd_poly(x2, z2, Q.P(px))[:, None, :], yd, half, r)
    F = ex(Q.TORSO_PX, Q.BODY_HALF_W, Q.BODY_EDGE_R)
    F = smin(F, ex(Q.NECK_HEAD_PX, Q.HEAD_HALF_W, Q.HEAD_EDGE_R), 4.0)
    F = smin(F, ex(Q.MUZZLE_PX, Q.MUZZLE_HALF_W, Q.MUZZLE_EDGE_R), 3.0)
    F = smin(F, ex(Q.TAIL_PX, Q.TAIL_HALF_W, Q.TAIL_EDGE_R), 3.0)
    for px, side in Q.LEGS_PX:
        F = smin(F, ex(px, Q.LEG_HALF_W, Q.LEG_EDGE_R, np.abs(Y - side * Q.LEG_Y)), 2.0)
    for b, t, y in Q.EARS_PX:
        (bx, bz), (tx, tz) = Q.P([b, t])
        F = smin(F, sd_cone_capsule(X, Y, Z, (bx, y, bz), (tx, y * 1.15, tz), *Q.EAR_R), 2.0)
    F = gaussian_filter(F, Q.BLUR / H)
    # eyes: dot dimples on both sides
    exx, ezz = Q.P([Q.EYE_PX])[0]
    i = int(round((exx - ax[0][0]) / H)); k = int(round((ezz - ax[2][0]) / H))
    col = F[i, :, k]; ys = ax[1][np.where(col < 0)[0]]
    ysurf = float(ys.max())
    for s in (-1, 1):
        F = np.maximum(F, Q.EYE_R - np.sqrt((X - exx) ** 2 + (Y - s * (ysurf + 0.8)) ** 2 + (Z - ezz) ** 2))
    F = np.maximum(F, -Z)
    return F, ax, (X, Y, Z)


def self_support(F, ax, X, z_max, exempt=None):
    """Remove everything below z_max that is not carried by material underneath within 45 degrees.
    Guarantees the part can be printed upright with no support in that zone."""
    solid = F < 0
    allowed = solid.copy()
    k0 = int(np.searchsorted(ax[2], 0.3)); k1 = int(np.searchsorted(ax[2], z_max))
    st = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)   # 4-neighbour growth: never flatter than 45 deg
    for k in range(k0 + 1, k1):
        sup = binary_dilation(allowed[:, :, k - 1], st)
        if exempt is not None: sup |= exempt[:, :, k]
        allowed[:, :, k] = solid[:, :, k] & sup
    removed = solid & ~allowed
    vol = float(removed.sum()) * H ** 3
    if vol == 0: return F, 0.0
    sd = (distance_transform_edt(~allowed) - distance_transform_edt(allowed)).astype(np.float32) * H
    sd = gaussian_filter(sd, 1.0)
    return np.maximum(F, sd - 0.35), vol


# ----------------------------------------------------------------------------- joint geometry (local frame:
# pivot axis at the origin, the middle piece lies towards +x)
def rot2(pts, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]

def tongue(bore_r=None):
    ri = CLIP_RI if bore_r is None else bore_r
    ro = CLIP_RO
    ring = CrossSection.circle(ro, SEG) - CrossSection.circle(ri, SEG)
    a = Q.MOUTH_HALF_ANGLE
    mouth = CrossSection([[(0, 0)] + [(30 * np.cos(np.radians(t)), 30 * np.sin(np.radians(t)))
                                      for t in np.linspace(180 - a, 180 + a, 9)]])
    neck = CrossSection([[(ri + 0.6, -Q.NECK_W / 2), (Q.SEAM_R + Q.SEAM_GAP + 2.5, -Q.NECK_W / 2),
                          (Q.SEAM_R + Q.SEAM_GAP + 2.5, Q.NECK_W / 2), (ri + 0.6, Q.NECK_W / 2)]])
    cs = (ring - mouth) + neck
    cs = cs.offset(0.8, m3.JoinType.Round, 2.0, 64).offset(-0.8, m3.JoinType.Round, 2.0, 64)   # fillet concave corners
    cs = cs.offset(-0.35, m3.JoinType.Round, 2.0, 64).offset(0.35, m3.JoinType.Round, 2.0, 64) # round the arm tips
    cs = cs - CrossSection.circle(ri, SEG)
    t = Manifold.extrude(cs, Q.TONGUE_T).translate((0, 0, ZB))
    # relief chamfer at the bottom of the bore (first-layer squish must not pinch the post)
    cone = Manifold.revolve(CrossSection([[(0, ZB - 0.01), (ri + 0.6, ZB - 0.01), (ri - 0.01, ZB + 0.6), (0, ZB + 0.6)]]), SEG)
    return t - cone

def sector2d(extra=0.0):
    w = Q.NECK_W / 2 + Q.SIDE_CLEAR
    L = Q.SEAM_R + 4.0
    lim = Q.YAW_RANGE + Q.YAW_STOP_MARGIN + extra
    rects = [CrossSection([rot2([(0, -w), (L, -w), (L, w), (0, w)], t)]) for t in np.arange(-lim, lim + 0.1, 2.0)]
    return CrossSection.batch_boolean(rects, m3.OpType.Add)

def pocket():
    hw = CLIP_RO + Q.CORRIDOR_EXTRA          # straight corridor so the (opened) clip can travel to the post
    corridor = CrossSection([[(0, -hw), (Q.SEAM_R + 4.0, -hw), (Q.SEAM_R + 4.0, hw), (0, hw)]])
    plan = CrossSection.circle(CLIP_RO + Q.POCKET_RADIAL, SEG) + sector2d() + corridor
    p = Manifold.extrude(plan, Z_CEIL - Z_FLOOR).translate((0, 0, Z_FLOOR))
    L = Q.SEAM_R + 4.0; d0 = Q.NOSE_CHAMFER_D
    cone = Manifold.revolve(CrossSection([[(d0, Z_CEIL - 0.05), (L, Z_CEIL - 0.05), (L, Z_CEIL + (L - d0))]]), SEG)
    cone = cone ^ Manifold.extrude(sector2d() + corridor, 40).translate((0, 0, Z_CEIL - 1))
    return p + cone

def post():
    c = Manifold.cylinder(Z_CEIL - Z_FLOOR + 3.0, Q.POST_R, Q.POST_R, SEG).translate((0, 0, Z_FLOOR - 1.5))
    fil = Manifold.cylinder(0.5, Q.POST_R + 0.5, Q.POST_R, SEG).translate((0, 0, Z_FLOOR - 0.01))
    return c + fil

def place(man, joint):
    return man.translate((XA, 0, 0)) if joint == "A" else man.rotate((0, 0, 180)).translate((XB, 0, 0))


# ----------------------------------------------------------------------------- export
def export(man, path):
    from scipy.spatial import cKDTree
    m = man.to_mesh()
    v = np.asarray(m.vert_properties[:, :3], np.float64); f = np.asarray(m.tri_verts, np.int64)
    for _ in range(3):   # weld needle edges so no zero-area triangles are written
        pairs = cKDTree(v).query_pairs(3e-4, output_type="ndarray")
        if not len(pairs): break
        remap = np.arange(len(v))
        for a, b in pairs:
            ra, rb = remap[a], remap[b]
            while remap[ra] != ra: ra = remap[ra]
            while remap[rb] != rb: rb = remap[rb]
            remap[max(ra, rb)] = min(ra, rb)
        for i in range(len(remap)):
            r = i
            while remap[r] != r: r = remap[r]
            remap[i] = r
        f = remap[f]
        f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    tm = trimesh.Trimesh(v, f, process=False); tm.remove_unreferenced_vertices()
    tm.export(path)
    return tm


def main():
    os.makedirs(f"{OUT}/stl", exist_ok=True); os.makedirs(f"{OUT}/build", exist_ok=True)
    print(f"pivot A x={XA:.2f}  pivot B x={XB:.2f}  belly z={ZB:.2f}  slot z={Z_FLOOR:.2f}..{Z_CEIL:.2f}")
    F, ax, (X, Y, Z) = dog_field()
    whole = to_manifold(F, ax, "whole dog (uncut reference)")
    export(whole, f"{OUT}/build/whole_uncut.stl")
    dA = np.hypot(X - XA, Y); dB = np.hypot(X - XB, Y)
    R, g = Q.SEAM_R, Q.SEAM_GAP
    F_rear = np.maximum(F, np.minimum(dA - R, X - XA))
    F_front = np.maximum(F, np.minimum(dB - R, XB - X))
    # the middle piece reaches down to the bottom edge of the drawn box
    x2, z2 = X[:, 0, :], Z[:, 0, :]
    box = Q.P([(400, Q.MID_BOX_TOP_PY), (720, Q.MID_BOX_TOP_PY), (720, Q.MID_BELLY_PY), (400, Q.MID_BELLY_PY)])
    F_box = gaussian_filter(extrude(sd_poly(x2, z2, box)[:, None, :], np.abs(Y), Q.BODY_HALF_W, Q.BODY_EDGE_R), Q.BLUR / H)
    F_mid = np.maximum.reduce([np.minimum(F, F_box), (R + g) - dA, (R + g) - dB, XA - X, X - XB])
    F_mid = np.maximum(F_mid, ((np.abs(Y) - Q.BODY_HALF_W) + (ZM + Q.MID_CHAMFER - Z)) / np.sqrt(2))
    F_mid = np.maximum(F_mid, ZM - Z)
    F_rear, v_r = self_support(F_rear, ax, X, Z_CEIL + 1.0)
    F_front, v_f = self_support(F_front, ax, X, Z_CEIL + 1.0, exempt=(X > Q.fx(815)))
    print(f"self-support pass removed {v_r / 1000:.2f} cm3 from rear, {v_f / 1000:.2f} cm3 from front")
    rear_s = to_manifold(F_rear, ax, "rear"); mid_s = to_manifold(F_mid, ax, "middle"); front_s = to_manifold(F_front, ax, "front")

    rear = (rear_s - place(pocket(), "A")) + (place(post(), "A") ^ rear_s.hull())
    front = (front_s - place(pocket(), "B")) + (place(post(), "B") ^ front_s.hull())
    middle = mid_s + place(tongue(), "A") + place(tongue(), "B")
    middle_inst = mid_s + place(tongue(Q.POST_R + 0.01), "A") + place(tongue(Q.POST_R + 0.01), "B")
    parts = dict(rear=rear, middle=middle, front=front)
    info = dict(pivot_A_x=XA, pivot_B_x=XB, belly_z=ZB, middle_belly_z=ZM, slot_floor_z=Z_FLOOR, slot_ceiling_z=Z_CEIL, clip_ri=CLIP_RI, clip_ro=CLIP_RO,
                self_support_removed_cm3=dict(rear=v_r / 1000, front=v_f / 1000), parts={})
    for n in parts:
        parts[n] = parts[n].simplify(0.004)
        man = parts[n]
        assert man.status() == m3.Error.NoError
        export(man, f"{OUT}/build/{n}_assembled.stl")
        bb = man.bounding_box()
        info["parts"][n] = dict(tris=man.num_tri(), volume_cm3=man.volume() / 1000, shells=len(man.decompose()), bbox=bb)
        print(n, info["parts"][n])
    export(middle_inst.simplify(0.004), f"{OUT}/build/middle_installed.stl")
    for n, s in (("rear", rear_s), ("middle", mid_s), ("front", front_s)):
        export(s, f"{OUT}/build/{n}_shell.stl")
    # print orientation: rear and front stand on their feet, middle lies on its belly
    export(parts["rear"], f"{OUT}/stl/rear.stl")
    export(parts["front"], f"{OUT}/stl/front.stl")
    export(parts["middle"].translate((0, 0, -ZM)), f"{OUT}/stl/middle.stl")
    asm = Manifold.compose([parts["rear"], middle_inst.simplify(0.004), parts["front"]])
    export(asm, f"{OUT}/build/dog_assembled.stl")
    bb = asm.bounding_box()
    info["assembled_size"] = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]
    json.dump(info, open(f"{OUT}/build/geometry_info.json", "w"), indent=1)
    print("assembled size", [round(v, 2) for v in info["assembled_size"]])


if __name__ == "__main__":
    main()
