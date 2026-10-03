#!/usr/bin/env python3
"""Procedural generator for the articulated dog.

Organic shells are built as signed-distance fields (smooth, symmetric, guaranteed closed),
polygonised with marching cubes, then all joint geometry is added with exact CSG booleans
(manifold3d) so every critical dimension is a parameter from params.py.

Usage:  python3 generate.py [out_dir]
"""
import sys, os, json
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import measure
import manifold3d as m3
from manifold3d import Manifold, CrossSection
import trimesh
import params as P

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.abspath(OUT)
SEG = 96  # circular segments for joint features


# ----------------------------------------------------------------------------- SDF helpers
def sd_poly(X, Z, pts):
    pts = np.asarray(pts, np.float32)
    d = np.full(X.shape, 1e9, np.float32)
    s = np.ones(X.shape, np.float32)
    n = len(pts)
    for i in range(n):
        a = pts[i]; b = pts[i - 1]
        ex, ez = b[0] - a[0], b[1] - a[1]
        wx, wz = X - a[0], Z - a[1]
        t = np.clip((wx * ex + wz * ez) / (ex * ex + ez * ez), 0, 1)
        bx, bz = wx - ex * t, wz - ez * t
        d = np.minimum(d, bx * bx + bz * bz)
        c1 = Z >= a[1]; c2 = Z < b[1]; c3 = ex * wz > ez * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def extrude(d2, ydist, half, r):
    """Extrude a 2D sdf (x-z profile) along y with rounded edges of radius r."""
    w0 = d2 + r
    w1 = ydist - (half - r)
    return np.minimum(np.maximum(w0, w1), 0) + np.hypot(np.maximum(w0, 0), np.maximum(w1, 0)) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def sd_round_box(x, y, z, c, half, r):
    qx = np.abs(x - c[0]) - (half[0] - r)
    qy = np.abs(y - c[1]) - (half[1] - r)
    qz = np.abs(z - c[2]) - (half[2] - r)
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r


def sd_cone_capsule(x, y, z, a, b, ra, rb):
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32)
    e = b - a
    t = np.clip(((x - a[0]) * e[0] + (y - a[1]) * e[1] + (z - a[2]) * e[2]) / (e @ e), 0, 1)
    dx = x - (a[0] + e[0] * t); dy = y - (a[1] + e[1] * t); dz = z - (a[2] + e[2] * t)
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * t)


def grid(lo, hi, h=P.VOXEL):
    ax = [np.arange(lo[i], hi[i] + h * 0.5, h, dtype=np.float32) for i in range(3)]
    return ax


def to_manifold(F, ax, name):
    """Marching cubes of field F (negative inside) -> simplified Manifold."""
    h = float(ax[0][1] - ax[0][0])
    v, f, _, _ = measure.marching_cubes(F, level=0.0, spacing=(h, h, h))
    v = v + np.array([ax[0][0], ax[1][0], ax[2][0]], np.float32)
    tm = trimesh.Trimesh(v, f, process=True)
    if tm.volume < 0:
        tm.invert()
    mesh = m3.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                   tri_verts=np.asarray(tm.faces, np.uint32))
    mesh.merge()
    man = Manifold(mesh)
    assert man.status() == m3.Error.NoError, (name, man.status())
    parts = man.decompose()
    if len(parts) > 1:  # drop stray islands, keep largest
        parts.sort(key=lambda p: -p.volume())
        print(f"  [{name}] dropped {len(parts)-1} islands, vols", [round(p.volume(), 3) for p in parts[1:]])
        man = parts[0]
    n0 = man.num_tri()
    man = man.simplify(P.SIMPLIFY_TOL)
    print(f"  [{name}] tris {n0} -> {man.num_tri()}  vol {man.volume():.0f} mm3")
    return man


# ----------------------------------------------------------------------------- HEAD
def head_sdf(x, y, z):
    """Analytic head shell (no joint, no fine details). Works on any point arrays."""
    d = sd_round_box(x, y, z, P.CRANIUM["c"], P.CRANIUM["half"], P.CRANIUM["r"])
    d = smin(d, sd_round_box(x, y, z, P.MUZZLE["c"], P.MUZZLE["half"], P.MUZZLE["r"]), 3.0)
    n = P.NOSE
    d = smin(d, np.sqrt((x - n["c"][0]) ** 2 + y ** 2 + (z - n["c"][2]) ** 2) - n["r"], 1.2)
    for a, b, ra, rb in P.EARS:
        d = smin(d, sd_cone_capsule(x, y, z, a, b, ra, rb), 2.0)
    return np.maximum(d, P.HEAD_BOTTOM_Z - z)


def build_head():
    ax = grid((99, -17, 52), (145, 17, 99))
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    F = head_sdf(X, Y, Z)
    F = gaussian_filter(F, P.HEAD_BLUR / P.VOXEL)
    # eyes: simple dimples on both sides
    e = P.EYE
    for s in (-1, 1):
        F = np.maximum(F, e["r"] - np.sqrt((X - e["x"]) ** 2 + (Y - s * e["y"]) ** 2 + (Z - e["z"]) ** 2))
    # mouth: shallow groove wrapping the muzzle
    mo = P.MOUTH
    G = np.maximum(np.maximum(np.abs(Z - mo["z"]) - mo["half_h"], -(F + mo["depth"])), mo["x_min"] - X)
    F = np.maximum(F, -G)
    F = np.maximum(F, P.HEAD_BOTTOM_Z - Z)
    shell = to_manifold(F, ax, "head")
    sil = (F < 0).any(axis=1)
    return shell, (ax, sil)


def socket_cutter(clear=P.SOCKET_CLEAR):
    """Female cavity: lead-in tunnel + spherical socket + 45deg self-supporting roof."""
    cx, cy, cz = P.BALL_C
    R = P.BALL_R + clear
    tb = P.THROAT_BELOW
    rt = np.sqrt(R * R - tb * tb)
    pts = [(0, P.HEAD_BOTTOM_Z - 0.5), (P.TUNNEL_R_BOTTOM + 0.07, P.HEAD_BOTTOM_Z - 0.5),
           (P.TUNNEL_R_BOTTOM, P.HEAD_BOTTOM_Z)]
    a0 = -np.arcsin(tb / R)
    for a in np.linspace(a0, np.pi / 4, 40):
        pts.append((R * np.cos(a), cz + R * np.sin(a)))
    top = cz + R * np.sqrt(2) - 1.5
    pts += [(1.5, top), (0, top)]
    return Manifold.revolve(CrossSection([pts]), SEG).translate((cx, cy, 0)), dict(R=R, throat_r=rt, roof_top=top)


def ball_stud(base_z=49.0, spread=None):
    """Male slotted ball on stalk (assembled coordinates).
    The two ball halves are modelled `spread` mm further apart than nominal, so that once snapped into the
    socket they are elastically pre-loaded against it (friction that holds the head pose)."""
    spread = P.BALL_SPREAD if spread is None else spread
    cx, cy, cz = P.BALL_C
    ball = Manifold.sphere(P.BALL_R, 128)
    ball = ball ^ Manifold.cube((2 * P.BALL_FLAT, 40, 40), True)
    hp = Manifold.cube((40, 20, 40)).translate((-20, 0, -20))
    ball = (ball ^ hp).translate((0, spread, 0)) + (ball - hp).translate((0, -spread, 0)) + \
        (ball ^ Manifold.cube((40, 2 * spread + 0.02, 40), True))
    ball = ball.translate((cx, cy, cz))
    stalk = Manifold.cylinder(cz - base_z, P.STALK_R, P.STALK_R, SEG).translate((cx, cy, base_z))
    fil = Manifold.cylinder(0.8, P.STALK_FILLET_R, P.STALK_R, SEG).translate((cx, cy, P.MOAT_BOTTOM_Z))
    return ball + stalk + fil


def ball_slot():
    cx, cy, cz = P.BALL_C
    w = P.SLOT_W
    top = cz + P.BALL_R + 1
    L = 2 * (P.MOAT_R + 0.3)
    box = Manifold.cube((L, w, top - P.SLOT_BOTTOM_Z), True).translate((cx, cy, (top + P.SLOT_BOTTOM_Z) / 2))
    rnd = Manifold.cylinder(L, w / 2, w / 2, 48, True).rotate((0, 90, 0)).translate((cx, cy, P.SLOT_BOTTOM_Z))
    return box + rnd


def add_stud(solid, spread=None):
    """Cut the relief moat into `solid` (body pedestal) and add the slotted ball stud."""
    cx, cy, cz = P.BALL_C
    moat = Manifold.cylinder(8.0, P.MOAT_R, P.MOAT_R, SEG).translate((cx, cy, P.MOAT_BOTTOM_Z))
    return (solid - moat) + ball_stud(spread=spread) - ball_slot()


# ----------------------------------------------------------------------------- TAIL
def build_tail():
    ax = grid((-4, -8, 70), (32, 8, 114))
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    x2, z2 = X[:, 0, :], Z[:, 0, :]
    d2 = np.full(x2.shape, 1e9, np.float32)
    tp = P.TAIL_PATH
    for (xa, za, ra), (xb, zb, rb) in zip(tp[:-1], tp[1:]):
        ex, ez = xb - xa, zb - za
        t = np.clip(((x2 - xa) * ex + (z2 - za) * ez) / (ex * ex + ez * ez), 0, 1)
        d2 = np.minimum(d2, np.hypot(x2 - xa - ex * t, z2 - za - ez * t) - (ra + (rb - ra) * t))
    d2 = gaussian_filter(d2, P.TAIL_BLUR / P.VOXEL)
    F = extrude(d2[:, None, :], np.abs(Y), P.TAIL_HALF_W, P.TAIL_EDGE_R)
    F = np.maximum(F, P.TAIL_ROOT_Z - Z)
    shell = to_manifold(F, ax, "tail")
    sil = (F < 0).any(axis=1)
    return shell, (ax, sil)


def tail_peg():
    """Male split snap-pin under the tail root (assembled coordinates)."""
    ax_x, ax_y = P.TAIL_AXIS
    zr = P.TAIL_ROOT_Z
    r = P.PEG_R
    Rb = P.PEG_R + P.BORE_CLEAR
    tip = zr - P.PEG_LEN
    zb = zr - P.BARB_TOP
    rb = Rb + P.BARB_H
    core = [(0, zr + 2.0), (r, zr + 2.0), (r, tip + 1.0), (r - 0.6, tip), (0, tip)]
    core = Manifold.revolve(CrossSection([core[::-1]]), SEG)
    core = core ^ Manifold.cube((40, 2 * P.TAIL_HALF_W, 80), True).translate((0, 0, zr - 10))
    # barb + friction band (only on the central |y| <= BARB_HALF_Y strip of each arm)
    rband = Rb + P.BAND_INTERF
    feat = [(0, zr - 9.4), (r, zr - 9.4), (rband, zr - 10.0), (rband, zr - 13.5), (r, zr - 14.1),
            (r, zb), (rb, zb - (rb - r)), (rb, zb - (rb - r) - 0.7), (r - 0.6, tip), (0, tip)]
    feat = Manifold.revolve(CrossSection([feat[::-1]]), SEG)
    feat = feat ^ Manifold.cube((40, 2 * P.BARB_HALF_Y, 80), True).translate((0, 0, zr - 10))
    peg = core + feat
    w = P.PEG_SLOT_W
    slot_top = zr - 1.0 - w / 2
    slot = Manifold.cube((w, 40, slot_top - (tip - 1)), True).translate((0, 0, (slot_top + tip - 1) / 2))
    slot += Manifold.cylinder(40, w / 2, w / 2, 48, True).rotate((90, 0, 0)).translate((0, 0, slot_top))
    peg = peg - slot
    info = dict(peg_r=r, bore_r=Rb, barb_r=rb, band_r=rband, tip_z=tip, barb_top_z=zb,
                arm_thickness=r - w / 2, arm_length=slot_top + w / 2 - (zb - (rb - r)))
    return peg.translate((ax_x, ax_y, 0)), info


def tail_bore():
    ax_x, ax_y = P.TAIL_AXIS
    Rb = P.PEG_R + P.BORE_CLEAR
    zl = P.TAIL_ROOT_Z - P.BARB_TOP + (Rb - P.PEG_R) + P.BARB_AX_CLEAR  # ledge start (see README)
    Rc = Rb + P.BARB_H + P.CAVITY_CLEAR
    bot = P.SEAT_Z - P.BORE_DEPTH
    pts = [(0, P.SEAT_Z + 10), (Rb + 0.6, P.SEAT_Z + 10), (Rb + 0.6, P.SEAT_Z), (Rb, P.SEAT_Z - 0.6), (Rb, zl),
           (Rc, zl - (Rc - Rb)), (Rc, bot), (0, bot)]
    bore = Manifold.revolve(CrossSection([pts[::-1]]), SEG).translate((ax_x, ax_y, 0))
    seat = Manifold.cylinder(12, P.SEAT_R, P.SEAT_R, SEG).translate((ax_x, ax_y, P.SEAT_Z))
    return bore + seat, dict(bore_r=Rb, ledge_z=zl, cavity_r=Rc, bottom_z=bot)


# ----------------------------------------------------------------------------- BODY
def rot_head(yaw, pitch, roll):
    cy_, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    Rz = np.array([[cy_, -sy, 0], [sy, cy_, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


def build_body():
    ax = grid((-4, -20, -2.4), (126, 20, 80))
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    x2, z2 = X[:, 0, :], Z[:, 0, :]
    aY = np.abs(Y)
    F = extrude(sd_poly(x2, z2, P.TORSO_PROFILE)[:, None, :], aY, P.BODY_HALF_W, P.BODY_EDGE_R)
    b = P.BELLY_BOX
    box = [(b["x0"], b["z0"]), (b["x0"], b["z1"]), (b["x1"], b["z1"]), (b["x1"], b["z0"])]
    F = smin(F, extrude(sd_poly(x2, z2, box)[:, None, :], aY, b["half_w"], b["edge_r"]), 1.5)
    F = smin(F, extrude(sd_poly(x2, z2, P.CHEST_PROFILE)[:, None, :], aY, P.CHEST_HALF_W, P.CHEST_EDGE_R), 3.0)
    for xb, xf, toe, side in P.LEGS:
        leg = [(xb, -3), (xb, P.LEG_TOP_Z), (xf, P.LEG_TOP_Z), (xf, 7.5), (xf + toe, 5.0), (xf + toe, -3)]
        F = smin(F, extrude(sd_poly(x2, z2, leg)[:, None, :], np.abs(Y - side * P.LEG_Y), P.LEG_HALF_W, P.LEG_EDGE_R), 2.5)
    F = gaussian_filter(F, P.BODY_BLUR / P.VOXEL)

    # carve clearance for the swept head (all poses of the design articulation range)
    C = np.array(P.BALL_C)
    ix = ax[0] >= 88; iz = ax[2] >= 40
    sub = np.ix_(ix, np.ones(len(ax[1]), bool), iz)
    xs, ys, zs = X[sub], Y[sub], Z[sub]
    sweep = np.full(xs.shape, 1e9, np.float32)
    pts = np.stack([xs - C[0], ys - C[1], zs - C[2]], -1)
    yaws = np.arange(-P.HEAD_YAW, P.HEAD_YAW + 1, 5)
    for yaw in yaws:
        for pitch in (-P.HEAD_PITCH, -P.HEAD_PITCH / 2, 0, P.HEAD_PITCH / 2, P.HEAD_PITCH):
            for roll in (-P.HEAD_ROLL, 0, P.HEAD_ROLL):
                R = rot_head(yaw, pitch, roll)
                q = pts @ R  # = R^T p
                sweep = np.minimum(sweep, head_sdf(q[..., 0] + C[0], q[..., 1] + C[1], q[..., 2] + C[2]))
    F[sub] = np.maximum(F[sub], P.HEAD_CARVE_CLEAR - sweep)
    F = np.maximum(F, -Z)
    shell = to_manifold(F, ax, "body")
    sil = (F < 0).any(axis=1)
    return shell, (ax, sil)


# ----------------------------------------------------------------------------- assemble
def export(man, path):
    """Write STL after welding needle edges (< 0.3 um) so no zero-area triangles are exported."""
    from scipy.spatial import cKDTree
    m = man.to_mesh()
    v = np.asarray(m.vert_properties[:, :3], np.float64); f = np.asarray(m.tri_verts, np.int64)
    for _ in range(3):
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
    tm = trimesh.Trimesh(v, f, process=False)
    tm.remove_unreferenced_vertices()
    tm.export(path)
    return tm


def main():
    os.makedirs(f"{OUT}/stl", exist_ok=True)
    os.makedirs(f"{OUT}/build", exist_ok=True)
    print("head shell"); head_shell, hs = build_head()
    print("tail shell"); tail_shell, ts = build_tail()
    print("body shell"); body_shell, bs = build_body()

    sock, sock_info = socket_cutter()
    head = head_shell - sock
    peg, peg_info = tail_peg()
    tail = tail_shell + peg
    bore, bore_info = tail_bore()
    body = add_stud(body_shell - bore)
    body_inst = add_stud(body_shell - bore, spread=0.0)   # ball halves as installed (compressed to nominal)

    parts = dict(body=body, head=head, tail=tail)
    info = dict(socket=sock_info, peg=peg_info, bore=bore_info, parts={})
    for n in parts:
        parts[n] = parts[n].simplify(0.004)   # removes boolean slivers / degenerate triangles
    body, head, tail = parts["body"], parts["head"], parts["tail"]
    body_inst = body_inst.simplify(0.004)
    export(body_inst, f"{OUT}/build/body_installed.stl")
    for n, man in parts.items():
        assert man.status() == m3.Error.NoError
        comps = len(man.decompose())
        export(man, f"{OUT}/build/{n}_assembled.stl")
        bb = man.bounding_box()
        info["parts"][n] = dict(tris=man.num_tri(), volume=man.volume(), components=comps, genus=man.genus(), bbox=bb)
        print(n, info["parts"][n])
    # shells without joints (used for wall-thickness checks)
    export(body_shell, f"{OUT}/build/body_shell.stl")
    export(head_shell, f"{OUT}/build/head_shell.stl")

    # print orientations
    export(body, f"{OUT}/stl/body.stl")
    export(head.translate((0, 0, -P.HEAD_BOTTOM_Z)), f"{OUT}/stl/head.stl")
    export(tail.rotate((90, 0, 0)).translate((0, 0, P.TAIL_HALF_W)), f"{OUT}/stl/tail.stl")
    # assembled display file: tail shown as installed (friction band elastically compressed to the bore)
    Rb = P.PEG_R + P.BORE_CLEAR
    zr = P.TAIL_ROOT_Z
    ring = Manifold.cylinder(6.0, 9, 9, SEG) - Manifold.cylinder(6.0, Rb - 0.03, Rb - 0.03, SEG)
    tail_inst = tail - ring.translate((P.TAIL_AXIS[0], P.TAIL_AXIS[1], zr - 14.6))
    asm = Manifold.compose([body_inst.simplify(0.004), head, tail_inst.simplify(0.004)])
    export(asm, f"{OUT}/dog_assembled.stl")
    bb = asm.bounding_box()
    info["assembled_bbox"] = bb
    info["assembled_size"] = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]
    json.dump(info, open(f"{OUT}/build/geometry_info.json", "w"), indent=1)
    np.savez_compressed(f"{OUT}/build/silhouettes.npz",
                        **{f"{n}_{k}": v for n, (a, s) in dict(head=hs, tail=ts, body=bs).items()
                           for k, v in dict(x=a[0], z=a[2], sil=s).items()})
    print("assembled size", info["assembled_size"])


if __name__ == "__main__":
    main()
