#!/usr/bin/env python3
"""Slice every production part with PrusaSlicer (0.4 nozzle, 0.20 mm layers, PLA) and analyse the g-code.
Writes build/slicing.json"""
import os, re, json, subprocess, numpy as np, trimesh
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = f"{ROOT}/build/gcode"; os.makedirs(OUT, exist_ok=True)
BASE = ["prusa-slicer", "--export-gcode", "--nozzle-diameter", "0.4", "--layer-height", "0.2", "--first-layer-height", "0.2",
        "--perimeters", "4", "--top-solid-layers", "5", "--bottom-solid-layers", "4", "--fill-density", "15%",
        "--fill-pattern", "gyroid", "--filament-diameter", "1.75", "--filament-density", "1.24", "--filament-type", "PLA",
        "--temperature", "210", "--first-layer-temperature", "215", "--bed-temperature", "60", "--first-layer-bed-temperature", "60",
        "--gcode-comments", "--center", "110,110"]
SUP = ["--support-material", "--support-material-buildplate-only", "--support-material-threshold", "45"]
JOBS = {"body": ("stl/body.stl", SUP), "head": ("stl/head.stl", []), "tail": ("stl/tail.stl", []),
        "joint_tolerance_test": ("test/joint_tolerance_test.stl", []), "plate_3mf": ("dog_print.3mf", SUP)}
ver = subprocess.run(["prusa-slicer", "--help"], capture_output=True, text=True).stdout.splitlines()[0]
res = {"slicer": ver, "settings": " ".join(BASE[2:-3])}

def overhang_stats(path):
    tm = trimesh.load(path)
    n = tm.face_normals; a = tm.area_faces; zc = tm.triangles_center[:, 2]
    down = (n[:, 2] < -np.cos(np.radians(44.0))) & (zc > 0.05)       # steeper than 45 deg overhang, not on the bed
    flat = (n[:, 2] < -0.985) & (zc > 0.05)
    bed = (n[:, 2] < -0.999) & (zc <= 0.05)
    return dict(bed_contact_area_mm2=round(float(a[bed].sum()), 1), overhang_gt45_area_mm2=round(float(a[down].sum()), 1),
                near_horizontal_overhang_area_mm2=round(float(a[flat].sum()), 1))

def analyse(g):
    t = open(g).read()
    out = {}
    for k, pat in dict(print_time=r"estimated printing time \(normal mode\) = (.*)", filament_g=r"filament used \[g\] = ([\d.]+)",
                       filament_mm=r"filament used \[mm\] = ([\d.]+)").items():
        m = re.search(pat, t); out[k] = m.group(1).strip() if m else None
    # extrusion per feature type + layer stats
    typ = "?"; e_by = {}; z = 0.0; zs = set(); first = 0.0; rel = "M83" in t
    last_e = 0.0
    for line in t.splitlines():
        if line.startswith(";TYPE:"): typ = line[6:]; continue
        if line.startswith("G1"):
            mz = re.search(r"Z([\d.]+)", line)
            if mz: z = float(mz.group(1)); zs.add(z)
            me = re.search(r"E(-?[\d.]+)", line)
            if me and ("X" in line or "Y" in line):
                e = float(me.group(1)); de = e if rel else e - last_e
                if de > 0:
                    e_by[typ] = e_by.get(typ, 0) + de
                    if abs(z - 0.2) < 1e-6: first += de
            if me and not rel: last_e = float(me.group(1))
        elif line.startswith("G92") and "E" in line: last_e = 0.0
    out["layers"] = len(zs); out["max_z"] = max(zs) if zs else None
    tot = sum(e_by.values()) or 1
    out["extrusion_share_percent"] = {k: round(100 * v / tot, 1) for k, v in sorted(e_by.items(), key=lambda kv: -kv[1])}
    out["first_layer_filament_mm"] = round(first, 1)
    return out

for name, (rel, extra) in JOBS.items():
    src = f"{ROOT}/{rel}"
    if not os.path.exists(src): continue
    g = f"{OUT}/{name}.gcode"
    r = subprocess.run(BASE + extra + ["-o", g, src], capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.exists(g)
    msgs = [l for l in (r.stdout + r.stderr).splitlines() if re.search(r"warn|error|empty|loose|repair|manifold", l, re.I)]
    res[name] = dict(file=rel, sliced_ok=ok, supports_enabled=bool(extra), slicer_messages=msgs)
    if ok: res[name].update(analyse(g))
    if rel.endswith(".stl"): res[name].update(overhang_stats(src))
    print(name, json.dumps(res[name]))
json.dump(res, open(f"{ROOT}/build/slicing.json", "w"), indent=1)
