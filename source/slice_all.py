#!/usr/bin/env python3
"""Slice every production part with PrusaSlicer CLI (PLA, 0.4 nozzle, 0.20 mm) and analyse the g-code -> build/slicing.json"""
import os, re, json, subprocess, numpy as np, trimesh
import generate as G
ROOT = G.OUT
OUT = f"{ROOT}/build/gcode"; os.makedirs(OUT, exist_ok=True)
BASE = ["prusa-slicer", "--export-gcode", "--nozzle-diameter", "0.4", "--layer-height", "0.2", "--first-layer-height", "0.2",
        "--perimeters", "3", "--top-solid-layers", "5", "--bottom-solid-layers", "4", "--fill-density", "15%", "--fill-pattern", "gyroid",
        "--filament-diameter", "1.75", "--filament-density", "1.24", "--filament-type", "PLA", "--temperature", "210",
        "--first-layer-temperature", "215", "--bed-temperature", "60", "--first-layer-bed-temperature", "60", "--gcode-comments"]
BRIM = ["--brim-width", "5"]
SUP = ["--support-material", "--support-material-buildplate-only", "--support-material-threshold", "20"]
JOBS = {"rear": ("stl/rear.stl", BRIM, (110, 110)), "middle": ("stl/middle.stl", [], (110, 110)), "front": ("stl/front.stl", BRIM + SUP, (110, 110)),
        "plate_3mf": ("dog_print.3mf", BRIM, (110, 110))}
ver = subprocess.run(["prusa-slicer", "--help"], capture_output=True, text=True).stdout.splitlines()[0]
res = {"slicer": ver, "settings": " ".join(BASE[2:-1])}

def overhangs(path):
    tm = trimesh.load(path); n = tm.face_normals; a = tm.area_faces; c = tm.triangles_center
    up = c[:, 2] > 0.3
    o60 = (n[:, 2] < -np.sin(np.radians(60))) & up        # steeper than 60 deg from vertical
    flat = (n[:, 2] < -0.985) & up
    out = dict(bed_contact_area_mm2=round(float(a[(n[:, 2] < -0.999) & (c[:, 2] <= 0.05)].sum()), 1),
               overhang_gt60deg_area_mm2=round(float(a[o60].sum()), 1), flat_ceiling_area_mm2=round(float(a[flat].sum()), 1))
    if flat.any():
        zs = np.round(c[flat, 2], 1); u, idx = np.unique(zs, return_inverse=True)
        out["flat_ceilings_by_height_mm2"] = {str(float(z)): round(float(a[flat][idx == i].sum()), 1) for i, z in enumerate(u) if a[flat][idx == i].sum() > 2}
    return out

def analyse(g, centre, part):
    t = open(g).read(); out = {}
    for k, pat in dict(print_time=r"estimated printing time \(normal mode\) = (.*)", filament_g=r"filament used \[g\] = ([\d.]+)").items():
        m = re.search(pat, t); out[k] = m.group(1).strip() if m else None
    typ = "?"; e_by = {}; z = 0.0; zs = set(); x = y = 0.0; last_e = 0.0; rel = "M83" in t
    sup_pts = []
    for line in t.splitlines():
        if line.startswith(";TYPE:"): typ = line[6:]; continue
        if line.startswith("G1"):
            mz = re.search(r"Z([\d.]+)", line)
            if mz: z = float(mz.group(1)); zs.add(z)
            mx = re.search(r"X([\d.]+)", line); my = re.search(r"Y([\d.]+)", line)
            if mx: x = float(mx.group(1))
            if my: y = float(my.group(1))
            me = re.search(r"E(-?[\d.]+)", line)
            if me and (mx or my):
                e = float(me.group(1)); de = e if rel else e - last_e
                if de > 0:
                    e_by[typ] = e_by.get(typ, 0) + de
                    if typ.startswith("Support"): sup_pts.append((x, y, z))
            if me and not rel: last_e = float(me.group(1))
        elif line.startswith("G92") and "E" in line: last_e = 0.0
    tot = sum(e_by.values()) or 1
    out["layers"] = len(zs)
    out["extrusion_share_percent"] = {k: round(100 * v / tot, 1) for k, v in sorted(e_by.items(), key=lambda kv: -kv[1])}
    sup = sum(v for k, v in e_by.items() if k.startswith("Support"))
    out["support_share_percent"] = round(100 * sup / tot, 1)
    out["support_filament_g"] = round(float(out["filament_g"]) * sup / tot, 2) if out["filament_g"] else None
    if sup_pts and part in ("front", "rear"):
        tm = trimesh.load(f"{ROOT}/stl/{part}.stl"); c0 = (tm.bounds[0] + tm.bounds[1]) / 2
        sp = np.array(sup_pts); sp[:, 0] += c0[0] - centre[0]; sp[:, 1] += c0[1] - centre[1]      # back to model coordinates
        cx = G.XB if part == "front" else G.XA
        inpocket = (np.hypot(sp[:, 0] - cx, sp[:, 1]) < Q_R) & (sp[:, 2] > G.Z_FLOOR) & (sp[:, 2] < G.Z_CEIL + 6)
        out["support_moves_inside_joint_pocket"] = int(inpocket.sum())
        out["support_region_model_coords"] = dict(x=[round(float(sp[:, 0].min()), 1), round(float(sp[:, 0].max()), 1)],
                                                  y=[round(float(sp[:, 1].min()), 1), round(float(sp[:, 1].max()), 1)],
                                                  z=[round(float(sp[:, 2].min()), 1), round(float(sp[:, 2].max()), 1)])
    return out
import params as Q
Q_R = Q.SEAM_R
for name, (rel, extra, centre) in JOBS.items():
    src = f"{ROOT}/{rel}"
    if not os.path.exists(src): continue
    g = f"{OUT}/{name}.gcode"
    r = subprocess.run(BASE + extra + ["--center", f"{centre[0]},{centre[1]}", "-o", g, src], capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.exists(g)
    msgs = [l for l in (r.stdout + r.stderr).splitlines() if re.search(r"warn|error|empty|loose|repair|manifold", l, re.I)]
    res[name] = dict(file=rel, sliced_ok=ok, supports="build plate only" if "--support-material" in extra else "none",
                     brim_mm=5 if "--brim-width" in extra else 0, slicer_messages=msgs)
    if ok: res[name].update(analyse(g, centre, name))
    if rel.endswith(".stl"): res[name].update(overhangs(src))
    print(name, json.dumps(res[name]))
json.dump(res, open(f"{ROOT}/build/slicing.json", "w"), indent=1)
