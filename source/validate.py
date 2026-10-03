#!/usr/bin/env python3
"""Mechanical / geometric validation of the 3-section dog. Writes build/validation.json (measured values only)."""
import os, json
import numpy as np, trimesh, manifold3d as m3
from manifold3d import Manifold
from scipy.spatial import ConvexHull
import params as Q
import generate as G
ROOT = G.OUT
res = {}
XA, XB = G.XA, G.XB

def load(path):
    tm = trimesh.load(path, process=True)
    mesh = m3.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)); mesh.merge()
    return Manifold(mesh), tm
def ivol(a, b): return float((a ^ b).volume())
def rotz(man, deg, cx):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]]); Cc = np.array([cx, 0, 0.0])
    T = np.zeros((3, 4)); T[:, :3] = R; T[:, 3] = Cc - R @ Cc
    return man.transform(T)

# ------------------------------------------------------------ 1. mesh quality
res["meshes"] = {}
for f in ("stl/rear.stl", "stl/middle.stl", "stl/front.stl"):
    man, tm = load(f"{ROOT}/{f}")
    fs = np.sort(tm.faces, axis=1); _, cnt = np.unique(tm.edges_sorted, axis=0, return_counts=True)
    comps = tm.split(only_watertight=False)
    res["meshes"][f] = dict(triangles=int(len(tm.faces)), watertight=bool(tm.is_watertight), winding_consistent=bool(tm.is_winding_consistent),
        outward_normals=bool(tm.volume > 0), all_edges_shared_by_2_faces=bool((cnt == 2).all()), manifold3d_status=str(man.status()).split(".")[-1],
        shells=int(len(comps)), zero_area_faces=int((tm.area_faces < 1e-9).sum()), duplicate_faces=int(len(fs) - len(np.unique(fs, axis=0))),
        self_intersection_free=bool(man.status() == m3.Error.NoError and abs(man.volume() - tm.volume) < 1e-3 * tm.volume),
        volume_cm3=round(float(tm.volume) / 1000, 2), bbox_mm=[round(float(v), 2) for v in tm.extents])
print("[1] meshes", flush=True)

rear, rear_tm = load(f"{ROOT}/build/rear_assembled.stl")
mid_p, mid_tm = load(f"{ROOT}/build/middle_assembled.stl")       # as printed (clip bore smaller than post)
mid, _ = load(f"{ROOT}/build/middle_installed.stl")              # clip opened onto the post
front, front_tm = load(f"{ROOT}/build/front_assembled.stl")
allv = np.vstack([rear_tm.vertices, mid_tm.vertices, front_tm.vertices])
ext = allv.max(0) - allv.min(0)
res["assembled_bbox_mm"] = dict(length=round(float(ext[0]), 2), width=round(float(ext[1]), 2), height=round(float(ext[2]), 2))
res["architecture"] = dict(printed_parts=3, joints=2, joint_1="rear <-> middle, vertical axis at x=%.2f" % XA,
                           joint_2="middle <-> front, vertical axis at x=%.2f" % XB,
                           middle_length_at_side_mm=round(G.XSB - G.XSA, 2), middle_length_at_centre_mm=round((XB - Q.SEAM_R) - (XA + Q.SEAM_R) - 2 * Q.SEAM_GAP, 2),
                           tail_part_of="rear (same shell)", head_neck_part_of="front (same shell)")

# ------------------------------------------------------------ 2. range of motion, joint by joint
def sweep(fixed, moving, cx, sign=1):
    out = {}
    test = [a for a in np.arange(-Q.YAW_RANGE, Q.YAW_RANGE + 0.1, 2.0)]
    out["angles_tested"] = len(test)
    out["max_interference_mm3_within_design_range"] = round(max(ivol(fixed, rotz(moving, a, cx)) for a in test), 4)
    lim = []
    for sgn in (1, -1):
        a = 0.0
        while a <= 60 and ivol(fixed, rotz(moving, sgn * a, cx)) < 0.05: a += 0.5
        lim.append(round(sgn * (a - 0.5), 1))
    out["hard_stop_deg"] = lim
    return out
res["joint_1"] = sweep(rear, mid, XA)
res["joint_2"] = sweep(mid, front, XB)
mid_shell, _ = load(f"{ROOT}/build/middle_shell.stl")
res["joint_1"]["seam_gap_measured_mm"] = {str(a): round(float(rear.min_gap(rotz(mid_shell, a, XA), 3.0)), 3) for a in (-30, 0, 30)}
res["joint_2"]["seam_gap_measured_mm"] = {str(a): round(float(mid_shell.min_gap(rotz(front, a, XB), 3.0)), 3) for a in (-30, 0, 30)}
print("[2] sweeps", flush=True)

# combined poses of the whole dog (rear fixed)
def dog_pose(a1, a2):
    m = rotz(mid, a1, XA)
    f = rotz(rotz(front, a2, XB), a1, XA)
    return m, f
comb = []
for a1 in (-30, -15, 0, 15, 30):
    for a2 in (-30, -15, 0, 15, 30):
        m, f = dog_pose(a1, a2)
        comb.append(ivol(rear, m) + ivol(m, f) + ivol(rear, f))
res["combined_poses"] = dict(poses_tested=len(comb), max_interference_mm3=round(max(comb), 4), max_total_bend_deg=60)

# ------------------------------------------------------------ 3. clip preload, vertical play, retention, assembly
def clip_region(cx, side):
    """ring half on the mouth side of the pivot (the two flexing arms)"""
    x0 = cx - 12 if side == "A" else cx
    return Manifold.cube((12, 24, Q.TONGUE_T + 2)).translate((x0, -12, G.ZB - 1))
def assembly(fixed, moving_printed, moving_installed, cx, side, direction):
    reg = clip_region(cx, side)
    arms = moving_printed ^ reg; rest = moving_installed - reg
    hp = Manifold.cube((400, 200, 400)).translate((-200, 0, -200))
    ap, an = arms ^ hp, arms - hp
    def path(s):
        worst = 0.0
        for t in np.arange(0, 30.01, 0.5):
            tr = (direction * t, 0, 0)
            worst = max(worst, ivol(fixed, ap.translate((tr[0], s, 0))) + ivol(fixed, an.translate((tr[0], -s, 0))) + ivol(fixed, rest.translate(tr)))
        return worst
    rigid = path(0.0)
    need = next((round(float(s), 2) for s in np.arange(0.05, Q.CORRIDOR_EXTRA + 0.001, 0.05) if path(s) < 0.02), None)
    return rigid, need
arm_L = np.radians(180 - Q.MOUTH_HALF_ANGLE - np.degrees(np.arcsin(Q.NECK_W / 2 / (G.CLIP_RI + Q.CLIP_T / 2)))) * (G.CLIP_RI + Q.CLIP_T / 2)
for name, fixed, moving_p, moving_i, cx, side, d in (("joint_1", rear, mid_p, mid, XA, "A", +1), ("joint_2", front, mid_p, mid, XB, "B", -1)):
    J = res[name]
    J["clip_preload_overlap_mm3_as_printed"] = round(ivol(fixed, moving_p), 3)
    up = next(round(float(t), 2) for t in np.arange(0.05, 2, 0.05) if ivol(fixed, moving_i.translate((0, 0, t))) > 0.02) - 0.05
    dn = next(round(float(t), 2) for t in np.arange(0.05, 2, 0.05) if ivol(fixed, moving_i.translate((0, 0, -t))) > 0.02) - 0.05
    J["vertical_play_mm"] = dict(up=round(up, 2), down=round(dn, 2))
    J["retention_overlap_mm3_when_pulled_apart_1.5mm"] = round(ivol(fixed, moving_p.translate((d * 1.5, 0, 0))), 2)
    rigid, need = assembly(fixed, moving_p, moving_i, cx, side, d)
    J["assembly"] = dict(direction="straight push along the body axis, tongue into the slot; path sampled every 0.5 mm over 30 mm",
                         max_overlap_rigid_mm3=round(rigid, 2), required_arm_opening_mm=need,
                         available_room_per_arm_mm=Q.CORRIDOR_EXTRA, arm_length_mm=round(float(arm_L), 2),
                         est_peak_strain_percent=None if need is None else round(100 * 3 * need * Q.CLIP_T / (2 * arm_L ** 2), 2))
    J["est_sustained_strain_percent"] = round(100 * 3 * Q.CLIP_PRELOAD * 1.5 * Q.CLIP_T / (2 * arm_L ** 2), 2)
    J["dimensions_mm"] = dict(post_diameter=2 * Q.POST_R, clip_bore_diameter=round(2 * G.CLIP_RI, 2), clip_radial_preload=Q.CLIP_PRELOAD,
        clip_arm_thickness=Q.CLIP_T, clip_wrap_deg=360 - 2 * Q.MOUTH_HALF_ANGLE, mouth_width=round(2 * G.CLIP_RI * np.sin(np.radians(Q.MOUTH_HALF_ANGLE)), 2),
        tongue_thickness=Q.TONGUE_T, neck_width=Q.NECK_W, slot_height=round(G.Z_CEIL - G.Z_FLOOR, 2), clearance_below_tongue=Q.FLOOR_CLEAR,
        clearance_above_tongue=Q.CEIL_CLEAR, seam_gap=Q.SEAM_GAP, neck_to_stop_clearance=Q.SIDE_CLEAR, radial_room_around_clip=Q.POCKET_RADIAL, seam_radius=Q.SEAM_R)
print("[3] joints", flush=True)

# ------------------------------------------------------------ 4. material around the joints
def joint_walls(tm, cx, side):
    out = {}
    # floor under the clip ring / ceiling above it (vertical rays)
    th = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    pts = np.array([[cx + r * np.cos(t), r * np.sin(t)] for r in (0.0, 3.0, G.CLIP_RO) for t in th])
    o = np.c_[pts, np.full(len(pts), G.Z_FLOOR - 0.05)]
    loc, ir, _ = tm.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(o), 1)), multiple_hits=False)
    d = np.full(len(o), 0.0); d[ir] = o[ir, 2] - loc[:, 2]
    inside = tm.contains(o)
    d[~inside] = 0.0
    out["floor_thickness_under_clip_min_mean"] = [round(float(d.min()), 2), round(float(d.mean()), 2)]
    out["floor_coverage_under_clip_percent"] = round(100 * float(inside.mean()), 1)
    o2 = np.c_[pts, np.full(len(pts), G.Z_CEIL + 0.05)]
    loc, ir, _ = tm.ray.intersects_location(o2, np.tile([0, 0, 1.0], (len(o2), 1)), multiple_hits=False)
    d2 = np.full(len(o2), np.nan); d2[ir] = loc[:, 2] - o2[ir, 2]
    out["ceiling_thickness_above_clip_min"] = round(float(np.nanmin(d2)), 2)
    # side walls (skirts) of the slot at mid height
    sec = tm.section(plane_origin=[0, 0, (G.Z_FLOOR + G.Z_CEIL) / 2], plane_normal=[0, 0, 1])
    p2, T = sec.to_2D(); Ti = np.linalg.inv(T)
    from shapely.geometry import Point
    polys = list(p2.polygons_full)
    sk = []
    for rr in (Q.SEAM_R - 0.6, Q.SEAM_R - 3.0, Q.SEAM_R - 6.0):
        for sgn in (1, -1):
            ys = []
            for yy in np.arange(0, 16, 0.05):
                xx = cx + (1 if side == "A" else -1) * np.sqrt(max(rr * rr - yy * yy, 0))
                q = Ti @ np.array([xx, sgn * yy, (G.Z_FLOOR + G.Z_CEIL) / 2, 1.0])
                if any(pl.contains(Point(q[0], q[1])) for pl in polys): ys.append(yy)
            sk.append(round(len(ys) * 0.05, 2))
    out["slot_side_wall_thickness_mm_at_r=%.1f/%.1f/%.1f(both sides)" % (Q.SEAM_R - 0.6, Q.SEAM_R - 3.0, Q.SEAM_R - 6.0)] = sk
    return out
res["joint_1"]["material"] = joint_walls(rear_tm, XA, "A")
res["joint_2"]["material"] = joint_walls(front_tm, XB, "B")

def sections(tm, z, normal=(0, 0, 1), origin=None):
    sec = tm.section(plane_origin=origin if origin is not None else [0, 0, z], plane_normal=normal)
    p2, _ = sec.to_2D(); out = []
    for poly in p2.polygons_full:
        r = poly.minimum_rotated_rectangle; xs, ys = r.exterior.coords.xy
        e = sorted([float(np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i])) for i in range(2)])
        out.append([round(e[0], 2), round(e[1], 2), round(float(poly.area), 1)])
    return out
ear_z = Q.fz(470)
res["structure"] = dict(
    rear_legs_section_at_z15=sections(rear_tm, 15.0), front_legs_section_at_z15=sections(front_tm, 15.0),
    tail_section_at_z95=sections(rear_tm, 95.0), tail_root_section_at_z82=sections(rear_tm, 82.0),
    ears_section_at_z=dict(z=round(ear_z, 1), sections=sections(front_tm, ear_z)),
    neck_section_vertical_plane_x110=sections(front_tm, 0, normal=(1, 0, 0), origin=[110, 0, 0]),
    tongue_neck_cross_section_mm2=round(Q.NECK_W * Q.TONGUE_T, 1),
    each_part_is_single_shell={k: v["shells"] == 1 for k, v in res["meshes"].items()})
print("[4] structure", flush=True)

# ------------------------------------------------------------ 5. standing stability (straight and bent)
def stability(a1, a2, label):
    m, f = dog_pose(a1, a2)
    parts = []
    for p in (rear, m, f):
        mm = p.to_mesh(); parts.append(trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts))
    vols = [p.volume for p in parts]; com = sum(p.center_mass * p.volume for p in parts) / sum(vols)
    v = np.vstack([p.vertices[p.vertices[:, 2] < 0.05][:, :2] for p in parts])
    hull = v[ConvexHull(v).vertices]
    mar = []
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        n = np.array([b[1] - a[1], -(b[0] - a[0])]); n /= np.linalg.norm(n); mar.append(float(n @ (a - com[:2])))
    mm_ = min(abs(x) for x in mar) if (np.sign(mar) == np.sign(mar[0])).all() else -1.0
    feet = sum(len(p.section(plane_origin=[0, 0, 0.02], plane_normal=[0, 0, 1]).to_2D()[0].polygons_full) for p in (parts[0], parts[2]))
    return dict(pose=label, feet_on_ground=feet, com_mm=[round(float(c), 1) for c in com], margin_to_tipping_edge_mm=round(mm_, 1),
                tip_angle_deg=round(float(np.degrees(np.arctan2(mm_, com[2]))), 1))
res["stability"] = [stability(0, 0, "straight"), stability(30, 30, "both joints +30 (C-curve)"), stability(30, -30, "S-curve +30/-30"), stability(30, 0, "joint 1 +30")]
res["solid_mass_g_at_1.24"] = round(1.24 * sum(v["volume_cm3"] for v in res["meshes"].values()), 1)
json.dump(res, open(f"{ROOT}/build/validation.json", "w"), indent=1)
print(json.dumps(res, indent=1))
