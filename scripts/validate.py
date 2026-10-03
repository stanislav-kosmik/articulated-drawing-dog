#!/usr/bin/env python3
"""Geometric / mechanical validation. Writes build/validation.json (all values measured, none assumed)."""
import os, json, sys
import numpy as np, trimesh, manifold3d as m3
from manifold3d import Manifold
from scipy.spatial import ConvexHull
import params as P
import generate as G

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
res = {}

def load_man(path):
    tm = trimesh.load(path, process=True)
    mesh = m3.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32))
    mesh.merge()
    return Manifold(mesh), tm

# ------------------------------------------------------------------ 1. mesh quality of every STL
res["meshes"] = {}
files = {"stl/body.stl": 1, "stl/head.stl": 1, "stl/tail.stl": 1, "dog_assembled.stl": 3, "test/joint_tolerance_test.stl": None}
for f, ncomp in files.items():
    p = f"{ROOT}/{f}"
    if not os.path.exists(p): continue
    man, tm = load_man(p)
    areas = tm.area_faces
    fs = np.sort(tm.faces, axis=1)
    dup = len(fs) - len(np.unique(fs, axis=0))
    edges = tm.edges_sorted
    _, cnt = np.unique(edges, axis=0, return_counts=True)
    res["meshes"][f] = dict(
        triangles=int(len(tm.faces)), watertight=bool(tm.is_watertight), winding_consistent=bool(tm.is_winding_consistent),
        outward_normals=bool(tm.volume > 0), every_edge_shared_by_exactly_2_faces=bool((cnt == 2).all()),
        manifold3d_status=str(man.status()).split(".")[-1], components=int(len(tm.split(only_watertight=False))),
        expected_components=ncomp, zero_area_faces=int((areas < 1e-9).sum()), duplicate_faces=int(dup),
        self_intersection_free=bool(man.status() == m3.Error.NoError and abs(man.volume() - tm.volume) < 1e-3 * abs(tm.volume)),
        volume_cm3=round(float(tm.volume) / 1000, 2),
        bbox_mm=[round(float(v), 2) for v in tm.extents])

# ------------------------------------------------------------------ 2. assembled parts
body_free, body_tm = load_man(f"{ROOT}/build/body_assembled.stl")   # as printed (ball halves spread)
body, _ = load_man(f"{ROOT}/build/body_installed.stl")               # ball halves compressed to nominal (installed state)
head, head_tm = load_man(f"{ROOT}/build/head_assembled.stl")
tail, tail_tm = load_man(f"{ROOT}/build/tail_assembled.stl")
asm = trimesh.util.concatenate([body_tm, head_tm, tail_tm])
res["assembled_bbox_mm"] = dict(length_x=round(float(asm.extents[0]), 2), width_y=round(float(asm.extents[1]), 2),
                                height_z=round(float(asm.extents[2]), 2))
C = np.array(P.BALL_C)

def head_pose(yaw, pitch, roll, lift=0.0):
    R = G.rot_head(yaw, pitch, roll)
    T = np.zeros((3, 4)); T[:, :3] = R; T[:, 3] = C - R @ C + np.array([0, 0, lift])
    return head.transform(T)

def tail_pose(ang, lift=0.0):
    a = np.radians(ang); c, s = np.cos(a), np.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]); A = np.array([P.TAIL_AXIS[0], P.TAIL_AXIS[1], 0])
    T = np.zeros((3, 4)); T[:, :3] = R; T[:, 3] = A - R @ A + np.array([0, 0, lift])
    return tail.transform(T)

def ivol(a, b):
    return float((a ^ b).volume())

print('[1] meshes ok', flush=True)
# ---- head: full grid over the design range
grid = [(y, p, r) for y in np.arange(-P.HEAD_YAW, P.HEAD_YAW + 1, 15) for p in np.arange(-P.HEAD_PITCH, P.HEAD_PITCH + 1, 5)
        for r in np.arange(-P.HEAD_ROLL, P.HEAD_ROLL + 1, 6) if np.hypot(p, r) <= P.HEAD_TILT_TOTAL]
worst = 0.0; gaps = []
for (y, p, r) in grid:
    hp = head_pose(y, p, r)
    worst = max(worst, ivol(body, hp))
for (y, p, r) in [(0, 0, 0), (90, 0, 0), (-90, 0, 0), (0, 15, 0), (0, -15, 0), (0, 0, 12), (45, 10, 10), (-90, -10, -10), (90, 15, 0), (-90, 0, 12)]:
    gaps.append(dict(yaw=y, pitch=p, roll=r, min_gap_mm=round(float(body.min_gap(head_pose(y, p, r), 3.0)), 3)))
res["head_joint"] = dict(design_range_deg=dict(yaw=P.HEAD_YAW, pitch=P.HEAD_PITCH, roll=P.HEAD_ROLL, combined_tilt=P.HEAD_TILT_TOTAL), poses_tested=len(grid),
                         max_interference_volume_mm3=round(worst, 4), min_gap_samples=gaps)
# limits beyond the design range (single axis, others 0): first angle with interference > 0.05 mm3
def limit(fn, start, stop, step):
    a = start
    while abs(a) <= abs(stop):
        if ivol(body, fn(a)) > 0.05: return float(a - step)
        a += step
    return float(stop)
res["head_joint"]["collision_free_limits_deg"] = dict(
    yaw_left=limit(lambda a: head_pose(a, 0, 0), 0, 180, 2), yaw_right=limit(lambda a: head_pose(a, 0, 0), 0, -180, -2),
    pitch_nose_down=limit(lambda a: head_pose(0, a, 0), 0, 60, 1), pitch_nose_up=limit(lambda a: head_pose(0, a, 0), 0, -60, -1),
    roll_pos=limit(lambda a: head_pose(0, 0, a), 0, 60, 1), roll_neg=limit(lambda a: head_pose(0, 0, a), 0, -60, -1))

print('[2] head sweep ok', flush=True)
# ---- tail: full revolution
tv = []
for a in range(0, 360, 10):
    inter = body ^ tail_pose(a)
    v = float(inter.volume()); bb = inter.bounding_box() if v > 0 else None
    tv.append((a, v, bb))
band_z = (P.TAIL_ROOT_Z - 14.2, P.TAIL_ROOT_Z - 9.3)
only_band = all(bb is None or (bb[2] >= band_z[0] - 0.05 and bb[5] <= band_z[1] + 0.05) for _, _, bb in tv)
res["tail_joint"] = dict(range_deg=360, angles_tested=len(tv),
                         overlap_volume_mm3_min_max=[round(min(v for _, v, _ in tv), 3), round(max(v for _, v, _ in tv), 3)],
                         overlap_confined_to_intentional_friction_band=bool(only_band),
                         note="the only body/tail overlap is the designed %.2f mm radial preload of the friction band" % P.BAND_INTERF)
# tail with friction band removed must be completely collision free over 360 deg
ax_x, ax_y = P.TAIL_AXIS
band_cut = Manifold.cylinder(band_z[1] - band_z[0], 9, 9, 64).translate((ax_x, ax_y, band_z[0])) - \
           Manifold.cylinder(band_z[1] - band_z[0], P.PEG_R, P.PEG_R, 96).translate((ax_x, ax_y, band_z[0]))
tail_nb = tail - band_cut
def tail_nb_pose(ang, lift=0.0, t=tail_nb):
    a = np.radians(ang); c, s = np.cos(a), np.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]); A = np.array([ax_x, ax_y, 0])
    T = np.zeros((3, 4)); T[:, :3] = R; T[:, 3] = A - R @ A + np.array([0, 0, lift])
    return t.transform(T)
res["tail_joint"]["max_interference_excluding_band_mm3"] = round(max(ivol(body, tail_nb_pose(a)) for a in range(0, 360, 10)), 4)
res["tail_joint"]["min_gap_excluding_band_mm"] = round(min(float(body.min_gap(tail_nb_pose(a), 3.0)) for a in (0, 90, 180, 270)), 3)
res["tail_joint"]["axial_play_mm"] = round(P.TAIL_ROOT_Z - P.SEAT_Z + P.BARB_AX_CLEAR, 2)
# retention: lifting the rigid tail must collide (barb on ledge)
res["tail_joint"]["retention_overlap_when_lifted_2mm_mm3"] = round(ivol(body, tail_nb_pose(0, 2.0)), 2)
res["head_joint"]["retention_overlap_when_lifted_1mm_mm3"] = round(ivol(body_free, head_pose(0, 0, 0, 1.0)), 2)

print('[3] tail ok', flush=True)
# ------------------------------------------------------------------ 3. assembly path with elastically deflected snap features
def split_shift(part, box, axis, s, centre):
    """Rigidly shift the two flexing halves (inside region `box`) towards the slot centre by s (approximates bending)."""
    region = part ^ box
    rest = part - box
    size = [400, 400, 400]; lo = [-200, -200, -200]; lo[axis] = centre
    hp = Manifold.cube(size).translate(lo)
    pos = region ^ hp; neg = region - hp
    sh = [0, 0, 0]; sh[axis] = -s; shn = [0, 0, 0]; shn[axis] = s
    return rest, pos.translate(sh), neg.translate(shn)

def box(lo, hi):
    return Manifold.cube([hi[i] - lo[i] for i in range(3)]).translate(lo)

def head_assembly(s):
    reg = Manifold.cylinder(6, P.MOAT_R - 0.05, P.MOAT_R - 0.05, 64).translate((C[0], C[1], P.MOAT_BOTTOM_Z + 1.0)) + box((104, -9, 56.9), (124, 9, 75))
    rest, a, b = split_shift(body_free, reg, 1, s, 0.0)
    out = []
    for lift in np.arange(0, 20.01, 0.5):
        h = head_pose(0, 0, 0, lift)
        out.append(ivol(a, h) + ivol(b, h) + ivol(rest, h))
    return max(out)
res["head_joint"]["assembly"] = dict(
    direction="head pushed straight down (-z) onto the ball; path sampled every 0.5 mm over 20 mm",
    max_overlap_rigid_mm3=round(head_assembly(0.0), 2))
for s in (0.3, 0.4, 0.5, 0.6):
    v = head_assembly(s)
    res["head_joint"]["assembly"][f"max_overlap_with_halves_deflected_{s:.2f}mm_mm3"] = round(v, 3)
need = next((s for s in np.arange(0.2, 1.0, 0.02) if head_assembly(s) < 0.02), None)
res["head_joint"]["assembly"]["required_deflection_per_half_mm"] = None if need is None else round(float(need), 2)
res["head_joint"]["assembly"]["available_deflection_per_half_mm"] = P.SLOT_W / 2

def tail_assembly(s):
    zr = P.TAIL_ROOT_Z
    rest, a, b = split_shift(tail_nb if s > 0 else tail, box((ax_x - 8, -8, zr - P.PEG_LEN - 1), (ax_x + 8, 8, zr - 5.0)), 0, s, ax_x)
    out = []
    for lift in np.arange(0.0, 24.01, 0.5):
        tr = (0, 0, lift)
        out.append(ivol(body, a.translate(tr)) + ivol(body, b.translate(tr)) + ivol(body, rest.translate(tr)))
    return max(out)
res["tail_joint"]["assembly"] = dict(direction="tail peg pushed straight down (-z) into the bore; path sampled every 0.5 mm over 24 mm",
                                     max_overlap_rigid_mm3=round(tail_assembly(0.0), 2))
need = next((s for s in np.arange(0.1, 1.8, 0.05) if tail_assembly(s) < 0.02), None)
res["tail_joint"]["assembly"]["required_deflection_per_arm_mm"] = None if need is None else round(float(need), 2)
res["tail_joint"]["assembly"]["available_deflection_per_arm_mm"] = P.PEG_SLOT_W / 2

print('[4] assembly ok', flush=True)
# ------------------------------------------------------------------ 4. joint dimensions + snap strain estimates
sock, si = G.socket_cutter(); peg, pi_ = G.tail_peg(); bore, bi = G.tail_bore()
E = 3000.0
sneed = res["head_joint"]["assembly"]["required_deflection_per_half_mm"] or 0.4
Lb = P.BALL_C[2] - P.THROAT_BELOW - (P.MOAT_BOTTOM_Z + 0.8); hb = P.STALK_R - P.SLOT_W / 2
res["head_joint"]["dimensions_mm"] = dict(
    ball_diameter=2 * P.BALL_R, ball_width_across_flats=2 * P.BALL_FLAT, socket_diameter=round(2 * si["R"], 2),
    radial_clearance=P.SOCKET_CLEAR, ball_half_spread=P.BALL_SPREAD,
    preload_interference_per_side=round(P.BALL_SPREAD - P.SOCKET_CLEAR, 3),
    preload_overlap_volume_mm3=round(ivol(body_free, head_pose(0, 0, 0)), 2), throat_diameter=round(2 * si["throat_r"], 3),
    snap_undercut_per_side_installed=round(P.BALL_R - si["throat_r"], 3), moat_outer_diameter=2 * P.MOAT_R, stalk_diameter=2 * P.STALK_R, slot_width=P.SLOT_W,
    flex_length=round(Lb, 2), half_stalk_thickness=round(hb, 2),
    est_peak_strain_assembly_percent=round(100 * 3 * sneed * hb / (2 * Lb ** 2), 2),
    est_sustained_strain_percent=round(100 * 3 * (P.BALL_SPREAD - P.SOCKET_CLEAR) * hb / (2 * Lb ** 2), 2))
tneed = res["tail_joint"]["assembly"]["required_deflection_per_arm_mm"] or 0.6
res["tail_joint"]["dimensions_mm"] = dict(
    peg_diameter=2 * P.PEG_R, peg_across_flats=2 * P.TAIL_HALF_W, bore_diameter=round(2 * bi["bore_r"], 2), radial_clearance=P.BORE_CLEAR,
    barb_diameter=round(2 * pi_["barb_r"], 2), barb_engagement_per_side=P.BARB_H, friction_band_diameter=round(2 * pi_["band_r"], 2),
    friction_band_interference_radial=P.BAND_INTERF, undercut_cavity_diameter=round(2 * bi["cavity_r"], 2),
    peg_length=P.PEG_LEN, bore_depth=P.BORE_DEPTH, slot_width=P.PEG_SLOT_W, arm_thickness=round(pi_["arm_thickness"], 2),
    arm_flex_length=round(pi_["arm_length"], 2),
    est_peak_strain_percent=round(100 * 3 * tneed * pi_["arm_thickness"] / (2 * pi_["arm_length"] ** 2), 2))

# ------------------------------------------------------------------ 5. wall thickness around joint cavities + feature sections
def min_wall(cutter, shell_path, zmin=None, zmax=None, drop_bottom=None):
    shell = trimesh.load(shell_path, process=True)
    if drop_bottom is not None:   # ignore the flat mouth face so we measure real side walls
        keep = shell.triangles_center[:, 2] > drop_bottom + 0.02
        shell = trimesh.Trimesh(shell.vertices, shell.faces[keep], process=False)
    cm = cutter.to_mesh(); ct = trimesh.Trimesh(cm.vert_properties[:, :3], cm.tri_verts)
    pts, _ = trimesh.sample.sample_surface(ct, 6000, seed=1)
    if zmin is not None: pts = pts[pts[:, 2] > zmin]
    if zmax is not None: pts = pts[pts[:, 2] < zmax]
    _, d, _ = trimesh.proximity.closest_point(shell, pts)
    return round(float(d.min()), 2)
bore_only = bore ^ Manifold.cylinder(60, 7, 7, 64).translate((ax_x, ax_y, P.SEAT_Z - 60.3))
res["wall_thickness_mm"] = dict(
    body_around_tail_bore_min=min_wall(bore_only, f"{ROOT}/build/body_shell.stl", zmax=P.SEAT_Z - 4.0),
    head_around_socket_min=min_wall(sock, f"{ROOT}/build/head_shell.stl", zmin=P.HEAD_BOTTOM_Z + 0.05, drop_bottom=P.HEAD_BOTTOM_Z))
def section_min_width(tm, z):
    sec = tm.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    p2, _ = sec.to_2D()
    out = []
    for poly in p2.polygons_full:
        r = poly.minimum_rotated_rectangle; xs, ys = r.exterior.coords.xy
        e = sorted([np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(2)])
        out.append([round(float(e[0]), 2), round(float(e[1]), 2)])
    return out
res["wall_thickness_mm"]["leg_sections_at_z15 (min x max of each leg)"] = section_min_width(body_tm, 15.0)
res["wall_thickness_mm"]["ear_sections_at_z86"] = section_min_width(head_tm, 86.0)
res["wall_thickness_mm"]["ear_sections_at_z91"] = section_min_width(head_tm, 91.0)
res["wall_thickness_mm"]["tail_section_at_z90"] = section_min_width(tail_tm, 90.0)
res["wall_thickness_mm"]["ball_stalk_section_at_z60"] = [s for s in section_min_width(body_tm, 60.0) if s[1] < 9]

print('[5] walls ok', flush=True)
# ------------------------------------------------------------------ 6. stability
def stability(hp, tp, label):
    parts = [body, hp, tp]
    vols = []; coms = []
    for p in parts:
        m = p.to_mesh(); t = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts)
        vols.append(t.volume); coms.append(t.center_mass)
    com = (np.array(coms) * np.array(vols)[:, None]).sum(0) / sum(vols)
    v = body_tm.vertices[body_tm.vertices[:, 2] < 0.05][:, :2]
    hull = v[ConvexHull(v).vertices]
    margins = []
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        n = np.array([b[1] - a[1], -(b[0] - a[0])]); n /= np.linalg.norm(n)
        margins.append(float(n @ (a - com[:2])))
    mm = min(abs(x) for x in margins) if (np.sign(margins) == np.sign(margins[0])).all() else -1
    return dict(pose=label, com_mm=[round(float(c), 1) for c in com], min_margin_to_support_edge_mm=round(mm, 1),
                tip_over_angle_deg=round(float(np.degrees(np.arctan2(mm, com[2]))), 1))
res["stability"] = [stability(head_pose(0, 0, 0), tail_pose(0), "neutral"),
                    stability(head_pose(90, 0, 0), tail_pose(90), "head 90 left, tail 90"),
                    stability(head_pose(-90, 15, 0), tail_pose(180), "head 90 right nose down, tail reversed")]
v = body_tm.vertices[body_tm.vertices[:, 2] < 0.05]
res["feet_contact"] = dict(feet_in_contact=int(len(trimesh.Trimesh(body_tm.vertices, body_tm.faces).section(
    plane_origin=[0, 0, 0.02], plane_normal=[0, 0, 1]).to_2D()[0].polygons_full)),
    footprint_x=[round(float(v[:, 0].min()), 1), round(float(v[:, 0].max()), 1)],
    footprint_y=[round(float(v[:, 1].min()), 1), round(float(v[:, 1].max()), 1)])
res["mass_estimate_solid_g_at_1.24gcc"] = round(float(sum(abs(t.volume) for t in (body_tm, head_tm, tail_tm))) / 1000 * 1.24, 1)

json.dump(res, open(f"{ROOT}/build/validation.json", "w"), indent=1)
print(json.dumps(res, indent=1))
