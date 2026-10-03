#!/usr/bin/env python3
"""README.md and validation_report.md generated from measured data (build/validation.json, build/slicing.json)."""
import os, json
import params as Q
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V = json.load(open(f"{ROOT}/build/validation.json")); S = json.load(open(f"{ROOT}/build/slicing.json"))
bb = V["assembled_bbox_mm"]; J1, J2 = V["joint_1"], V["joint_2"]; D = J1["dimensions_mm"]; A = V["architecture"]
URL = "https://drive.google.com/file/d/13HVwXR2jKd8h_SItTTXizeP983Ik6S_V/view?usp=drivesdk"
tot_g = sum(float(S[n]["filament_g"]) for n in ("rear", "middle", "front"))
def hm(t):
    h = int(t.split("h")[0]) if "h" in t else 0; m = int(t.split("h")[-1].split("m")[0]); return h * 60 + m
tot_min = sum(hm(S[n]["print_time"]) for n in ("rear", "middle", "front"))
tot_t = f"{tot_min // 60} h {tot_min % 60} min"
def yn(b): return "yes" if b else "**NO**"
M = V["meshes"]

readme = f"""# Articulated drawing-dog (final version)

![drawing vs model](renders/source_vs_model.png)

A child's pencil drawing of a dog, given thickness and turned into a small FDM-printable toy.
The side silhouette is traced from the drawing; the body bends at **two joints in the torso**. Head, neck and tail are fixed.

```
[ REAR: tail + rump + rear legs ] <joint 1> [ MIDDLE: short torso slice ] <joint 2> [ FRONT: chest + front legs + neck + head ]
```

![articulation](renders/articulation_demo.png)

| | |
|---|---|
| Size (straight) | **{bb['length']} x {bb['width']} x {bb['height']} mm** (length x width x height) |
| Printed pieces | **3** — `stl/rear.stl`, `stl/middle.stl`, `stl/front.stl` (no pins, no glue, no hardware) |
| Joints | exactly 2, both vertical-axis snap pivots hidden inside the torso |
| Movement | joint 1: {J1['hard_stop_deg'][1]}° … +{J1['hard_stop_deg'][0]}°, joint 2: {J2['hard_stop_deg'][1]}° … +{J2['hard_stop_deg'][0]}° left/right (hard stops); up to {V['combined_poses']['max_total_bend_deg']}° combined curve |
| Middle piece | {A['middle_length_at_side_mm']} mm long at the flanks, same cross-section as the torso |
| Source drawing | {URL} (copy: `source_drawing.jpg`) |

More views: [side](renders/side.png) · [opposite side](renders/opposite_side.png) · [front](renders/front.png) · [rear](renders/rear.png) · [top](renders/top.png) · [perspective](renders/perspective.png)

![perspective](renders/perspective.png)

## How the joints work

Each joint is a **vertical pivot post with a snap-on C-clip**:

* The rear and the front section each contain a Ø{D['post_diameter']} mm vertical **post** standing in a {D['slot_height']} mm high slot at belly level.
* The middle piece has a flat **tongue** at each end ({D['tongue_thickness']} mm thick, {D['neck_width']} mm neck) ending in a **C-shaped clip** that wraps {D['clip_wrap_deg']:.0f}° of the post.
  It is printed flat, so the clip arms flex within the layers — the strong direction.
* Push the tongue into the slot and the clip snaps over the post. It then turns only about the vertical axis (yaw);
  slot floor and ceiling keep it from tilting.
* The seam between sections is a cylinder concentric with the pivot (radius {D['seam_radius']} mm), so the gap stays a constant
  {D['seam_gap']} mm line at every angle and the three pieces read as one dog when straight.

Clearances (all parameters in `source/params.py`):

| Fit | Value |
|---|---|
| Seam gap between sections | **{D['seam_gap']} mm** |
| Neck to yaw-stop faces | **{D['neck_to_stop_clearance']} mm** |
| Under / over the tongue | {D['clearance_below_tongue']} / {D['clearance_above_tongue']} mm (measured play {J1['vertical_play_mm']['down']} / {J1['vertical_play_mm']['up']} mm) |
| Room around the clip (for snapping) | {D['radial_room_around_clip']} mm radial, {Q.CORRIDOR_EXTRA} mm per side in the insertion corridor |
| Clip on post | not a clearance fit: the clip bore is Ø{D['clip_bore_diameter']} on a Ø{D['post_diameter']} post, i.e. **{D['clip_radial_preload']} mm radial elastic preload**. The spring grip is what holds a pose; it tolerates printer variation because the arms flex. |

If your printer makes the joints too stiff or too loose, change `CLIP_PRELOAD` (0.00 = looser, 0.20 = tighter) and re-run `generate.py`; only `middle.stl` changes (38 min print).

## Printing (PLA, 0.4 mm nozzle, 0.20 mm layers, 3 perimeters, 15 % infill)

| Part | Orientation (as in the STL) | Supports | Brim | Time | Filament |
|---|---|---|---|---|---|
| `rear.stl` | standing on its two feet | **none** | 5 mm recommended | {S['rear']['print_time']} | {S['rear']['filament_g']} g |
| `middle.stl` | lying on its belly, tongues on the bed | **none** | no | {S['middle']['print_time']} | {S['middle']['filament_g']} g |
| `front.stl` | standing on its two feet | **build plate only**, overhang threshold 20° — a single column under chin and throat ({S['front']['support_filament_g']} g) | 5 mm recommended | {S['front']['print_time']} | {S['front']['filament_g']} g |

Total about **{tot_t}** and **{tot_g:.0f} g** (PrusaSlicer estimate). `dog_print.3mf` has all three parts on one plate.

Important: use *build-plate-only* supports. "Supports everywhere" would fill the joint slots. With build-plate-only supports nothing can get
into the slots (checked in the g-code: {S['front']['support_moves_inside_joint_pocket']} support moves inside the joint).
All undersides of the rear and front sections are shaped at 45° or steeper so they print without support.

## Assembly

1. Remove brim and the support column under the chin.
2. Hold the middle piece with its flat belly down. Push one tongue straight into the slot at the cut face of the rear section until it clicks onto the post.
3. Push the front section onto the other tongue the same way.
4. To take it apart, pull the sections straight apart.

The clip arms open {J1['assembly']['required_arm_opening_mm']} mm each while snapping (room available: {J1['assembly']['available_room_per_arm_mm']} mm).

## Files

```
dog_complete.blend   posable scene (rotate the two JOINT_* empties about Z)
dog_preview.glb      assembled preview
dog_print.3mf        all parts on one plate
stl/                 rear.stl, middle.stl, front.stl (print orientation)
renders/             source_vs_model.png, articulation_demo.png, side/opposite_side/front/rear/top/perspective
source/              params.py, generate.py, validate.py, slice_all.py, render_blender.py, compare.py, demo.py, make_3mf.py, build_docs.py
validation_report.md measured results
```
Rebuild: `cd source && python3 generate.py && python3 make_3mf.py && python3 validate.py && python3 slice_all.py && blender -b -P render_blender.py && python3 compare.py && python3 demo.py && python3 build_docs.py`

Version 1 (movable head and tail) is superseded; it remains available under release v1.0.
"""
open(f"{ROOT}/README.md", "w").write(readme)

rows = "".join(f"| `{f}` | {m['triangles']} | {yn(m['watertight'])} | {yn(m['all_edges_shared_by_2_faces'])} / {m['manifold3d_status']} | {yn(m['outward_normals'])} | {m['shells']} | {m['zero_area_faces']} | {m['duplicate_faces']} | {yn(m['self_intersection_free'])} | {' x '.join(map(str, m['bbox_mm']))} | {m['volume_cm3']} |\n" for f, m in M.items())
srows = "".join(f"| `{S[n]['file']}` | {yn(S[n]['sliced_ok'])} | {len(S[n]['slicer_messages'])} | {S[n]['layers']} | {S[n]['print_time']} | {S[n]['filament_g']} g | {S[n]['supports']} | {S[n]['support_filament_g']} g ({S[n]['support_share_percent']} %) | {S[n].get('bed_contact_area_mm2', '-')} |\n" for n in ("rear", "middle", "front", "plate_3mf"))
def jrow(J, name):
    a = J["assembly"]; m = J["material"]; k = [x for x in m if x.startswith("slot_side")][0]
    return f"""### {name}

| Check | Result |
|---|---|
| Interference over ±{int(Q.YAW_RANGE)}° ({J['angles_tested']} angles, 2° steps) | **{J['max_interference_mm3_within_design_range']} mm³** |
| Hard stops (last collision-free angle, 0.5° steps) | **{J['hard_stop_deg'][1]}° … +{J['hard_stop_deg'][0]}°** |
| Seam gap measured at -30° / 0° / +30° | {J['seam_gap_measured_mm']['-30']} / {J['seam_gap_measured_mm']['0']} / {J['seam_gap_measured_mm']['30']} mm |
| Vertical play of the tongue (down / up) | {J['vertical_play_mm']['down']} / {J['vertical_play_mm']['up']} mm |
| Clip preload (overlap of as-printed clip with post) | {J['clip_preload_overlap_mm3_as_printed']} mm³ (= {Q.CLIP_PRELOAD} mm radial, intentional) |
| Assembly path, rigid | {a['max_overlap_rigid_mm3']} mm³ overlap (the snap) |
| Assembly path with clip arms opened | collision-free at **{a['required_arm_opening_mm']} mm per arm** (room: {a['available_room_per_arm_mm']} mm); est. peak strain {a['est_peak_strain_percent']} % in-layer |
| Retention: pulled apart 1.5 mm rigidly | {J['retention_overlap_mm3_when_pulled_apart_1.5mm']} mm³ overlap -> the clip must open again to release |
| Sustained strain from preload (estimate) | {J['est_sustained_strain_percent']} % |
| Slot floor under the clip (min / mean thickness, coverage) | {m['floor_thickness_under_clip_min_mean'][0]} / {m['floor_thickness_under_clip_min_mean'][1]} mm, {m['floor_coverage_under_clip_percent']} % |
| Material above the slot | {m['ceiling_thickness_above_clip_min']} mm |
| Slot side walls at r = 17.4 / 15 / 12 mm (both sides) | {m[k]} mm |
"""
st = "\n".join(f"| {s['pose']} | {s['feet_on_ground']} | {s['com_mm']} | {s['margin_to_tipping_edge_mm']} | {s['tip_angle_deg']}° |" for s in V["stability"])
T = V["structure"]
rep = f"""# Validation report (final version)

Measured by `source/validate.py` (trimesh + manifold3d) and `source/slice_all.py` (PrusaSlicer CLI) on the delivered files.
Raw data: `build/validation.json`, `build/slicing.json`. Nothing here has been physically printed.

## Architecture

* Printed parts: **{A['printed_parts']}** (rear, middle, front). Articulated interfaces: **{A['joints']}**.
* Joint 1: {A['joint_1']}. Joint 2: {A['joint_2']}. Both lie in the torso.
* Tail: {A['tail_part_of']}. Head and neck: {A['head_neck_part_of']}.
* Middle piece: {A['middle_length_at_side_mm']} mm long at the flanks ({A['middle_length_at_centre_mm']} mm at the centre line), cut from the same torso field as its neighbours.
* Assembled size: **{bb['length']} x {bb['width']} x {bb['height']} mm**.

## Meshes

| File | Triangles | Watertight | 2-manifold / manifold3d | Outward normals | Shells | Zero-area | Duplicate | No self-intersection | Bounding box (mm) | Volume (cm³) |
|---|---|---|---|---|---|---|---|---|---|---|
{rows}
One shell per part means legs and tail (rear) and legs, neck, head and ears (front) are structurally one piece with their section.

## Joints

Joint dimensions (identical for both): post Ø{D['post_diameter']}, clip bore Ø{D['clip_bore_diameter']}, clip arm {D['clip_arm_thickness']} mm, wrap {D['clip_wrap_deg']:.0f}°,
mouth {D['mouth_width']} mm, tongue {D['tongue_thickness']} mm, neck {D['neck_width']} mm, slot height {D['slot_height']} mm, seam radius {D['seam_radius']} mm.

{jrow(J1, 'Joint 1 — rear / middle')}
{jrow(J2, 'Joint 2 — middle / front')}
### Whole dog

{V['combined_poses']['poses_tested']} combinations of joint 1 and joint 2 in {{-30, -15, 0, 15, 30}}° (rear–middle, middle–front and rear–front checked):
maximum interference **{V['combined_poses']['max_interference_mm3']} mm³**.

## Structure

| Feature | Section: min x max mm, area mm² |
|---|---|
| Rear legs at 15 mm height | {T['rear_legs_section_at_z15']} |
| Front legs at 15 mm height | {T['front_legs_section_at_z15']} |
| Tail at z = 95 mm | {T['tail_section_at_z95']} |
| Tail root at z = 82 mm | {T['tail_root_section_at_z82']} |
| Ears at z = {T['ears_section_at_z']['z']} mm | {T['ears_section_at_z']['sections']} |
| Tongue neck | {T['tongue_neck_cross_section_mm2']} mm² |

## Standing

| Pose | Feet on ground | Centre of mass (mm) | Margin to tipping edge (mm) | Tilt to tip over |
|---|---|---|---|---|
{st}

## Slicing

Slicer: **{S['slicer']}**. Settings: `{S['settings']}`.

| File | Sliced | Warnings | Layers | Time | Filament | Supports | Support material | Bed contact (mm²) |
|---|---|---|---|---|---|---|---|---|
{srows}
* Production total (rear + middle + front): **{tot_t}, {tot_g:.0f} g**.
* Rear: no supports. The only flat ceilings are the two short bridges around the pivot post ({S['rear'].get('flat_ceilings_by_height_mm2', {})} mm² by height).
* Front: supports only at model x = {S['front']['support_region_model_coords']['x']} mm (chin / throat column); support moves inside the joint slot: **{S['front']['support_moves_inside_joint_pocket']}**.
* A self-support pass in the generator removed {json.load(open(f"{ROOT}/build/geometry_info.json"))['self_support_removed_cm3']['rear']:.1f} cm³ (rear) and {json.load(open(f"{ROOT}/build/geometry_info.json"))['self_support_removed_cm3']['front']:.1f} cm³ (front) of material that would have needed support; this only affects undersides hidden in the side view.
* The plate file was sliced without supports only to confirm it loads; for a real print enable build-plate-only supports for the front part.

## Known compromises

* Not physically printed; the snap force and joint friction depend on the printer. `CLIP_PRELOAD` is the single tuning parameter.
* Legs are staggered (one forward, one back on each end) to reproduce the four legs visible in the drawing. To print without support, the undersides
  between them are 45° facets rather than soft curves, and the slit between the rear legs is shorter than drawn.
* A 45° wedge under each joint (behind the front legs, in front of the rear thigh) carries the slot floor; it sits slightly outside the drawn outline.
* The inside of the tail hook is filled to a 35° chord so the tail prints without support; the outer curve follows the drawing.
* The rear and front sections stand on two small feet while printing, so a brim is recommended.
* The dark scribble between rear body and middle box in the drawing is not modelled.
* PLA relaxes under constant strain, so joint friction will soften somewhat over time.
"""
open(f"{ROOT}/validation_report.md", "w").write(rep)
print("docs written")
