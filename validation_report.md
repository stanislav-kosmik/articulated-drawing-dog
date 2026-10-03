# Validation report (final version)

Measured by `source/validate.py` (trimesh + manifold3d) and `source/slice_all.py` (PrusaSlicer CLI) on the delivered files.
Raw data: `build/validation.json`, `build/slicing.json`. Nothing here has been physically printed.

## Architecture

* Printed parts: **3** (rear, middle, front). Articulated interfaces: **2**.
* Joint 1: rear <-> middle, vertical axis at x=50.41. Joint 2: middle <-> front, vertical axis at x=96.38. Both lie in the torso.
* Tail: rear (same shell). Head and neck: front (same shell).
* Middle piece: 26.07 mm long at the flanks (8.97 mm at the centre line), cut from the same torso field as its neighbours.
* Assembled size: **150.75 x 30.11 x 113.38 mm**.

## Meshes

| File | Triangles | Watertight | 2-manifold / manifold3d | Outward normals | Shells | Zero-area | Duplicate | No self-intersection | Bounding box (mm) | Volume (cm³) |
|---|---|---|---|---|---|---|---|---|---|---|
| `stl/rear.stl` | 25580 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 68.72 x 30.01 x 113.38 | 84.61 |
| `stl/middle.stl` | 4908 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 50.23 x 30.01 x 35.5 | 14.69 |
| `stl/front.stl` | 30714 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 72.06 x 30.11 x 97.55 | 52.65 |

One shell per part means legs and tail (rear) and legs, neck, head and ears (front) are structurally one piece with their section.

## Joints

Joint dimensions (identical for both): post Ø11.0, clip bore Ø10.8, clip arm 1.8 mm, wrap 216°,
mouth 10.27 mm, tongue 7.0 mm, neck 6.0 mm, slot height 7.65 mm, seam radius 18.0 mm.

### Joint 1 — rear / middle

| Check | Result |
|---|---|
| Interference over ±30° (31 angles, 2° steps) | **0.0 mm³** |
| Hard stops (last collision-free angle, 0.5° steps) | **-32.0° … +32.0°** |
| Seam gap measured at -30° / 0° / +30° | 0.485 / 0.487 / 0.488 mm |
| Vertical play of the tongue (down / up) | 0.3 / 0.35 mm |
| Clip preload (overlap of as-printed clip with post) | 13.046 mm³ (= 0.1 mm radial, intentional) |
| Assembly path, rigid | 3.45 mm³ overlap (the snap) |
| Assembly path with clip arms opened | collision-free at **0.3 mm per arm** (room: 0.7 mm); est. peak strain 1.06 % in-layer |
| Retention: pulled apart 1.5 mm rigidly | 2.96 mm³ overlap -> the clip must open again to release |
| Sustained strain from preload (estimate) | 0.53 % |
| Slot floor under the clip (min / mean thickness, coverage) | 5.25 / 12.04 mm, 100.0 % |
| Material above the slot | 17.98 mm |
| Slot side walls at r = 17.4 / 15 / 12 mm (both sides) | [2.4, 2.4, 4.6, 4.6, 6.2, 6.2] mm |

### Joint 2 — middle / front

| Check | Result |
|---|---|
| Interference over ±30° (31 angles, 2° steps) | **0.0 mm³** |
| Hard stops (last collision-free angle, 0.5° steps) | **-32.0° … +32.0°** |
| Seam gap measured at -30° / 0° / +30° | 0.486 / 0.485 / 0.489 mm |
| Vertical play of the tongue (down / up) | 0.3 / 0.35 mm |
| Clip preload (overlap of as-printed clip with post) | 13.047 mm³ (= 0.1 mm radial, intentional) |
| Assembly path, rigid | 3.45 mm³ overlap (the snap) |
| Assembly path with clip arms opened | collision-free at **0.3 mm per arm** (room: 0.7 mm); est. peak strain 1.06 % in-layer |
| Retention: pulled apart 1.5 mm rigidly | 2.96 mm³ overlap -> the clip must open again to release |
| Sustained strain from preload (estimate) | 0.53 % |
| Slot floor under the clip (min / mean thickness, coverage) | 1.38 / 12.98 mm, 100.0 % |
| Material above the slot | 15.57 mm |
| Slot side walls at r = 17.4 / 15 / 12 mm (both sides) | [1.95, 1.95, 4.6, 4.6, 6.2, 6.2] mm |

### Whole dog

25 combinations of joint 1 and joint 2 in {-30, -15, 0, 15, 30}° (rear–middle, middle–front and rear–front checked):
maximum interference **0.0 mm³**.

## Structure

| Feature | Section: min x max mm, area mm² |
|---|---|
| Rear legs at 15 mm height | [[11.14, 11.5, 117.6], [11.5, 14.54, 156.6]] |
| Front legs at 15 mm height | [[10.43, 11.5, 109.4], [10.11, 11.5, 105.7]] |
| Tail at z = 95 mm | [[9.97, 10.88, 90.4]] |
| Tail root at z = 82 mm | [[10.0, 13.82, 118.4]] |
| Ears at z = 91.3 mm | [[5.44, 5.52, 23.7], [4.48, 4.49, 15.9]] |
| Tongue neck | 42.0 mm² |

## Standing

| Pose | Feet on ground | Centre of mass (mm) | Margin to tipping edge (mm) | Tilt to tip over |
|---|---|---|---|---|
| straight | 4 | [60.8, -0.0, 55.1] | 14.8 | 15.0° |
| both joints +30 (C-curve) | 4 | [56.1, 13.1, 55.1] | 10.2 | 10.5° |
| S-curve +30/-30 | 4 | [58.4, 9.0, 55.1] | 12.2 | 12.5° |
| joint 1 +30 | 4 | [57.8, 11.4, 55.1] | 12.2 | 12.5° |

## Slicing

Slicer: **[2026-10-03 15:23:22.472381] [0x00007b1251d96d00] [trace]   Initializing StaticPrintConfigs**. Settings: `--nozzle-diameter 0.4 --layer-height 0.2 --first-layer-height 0.2 --perimeters 3 --top-solid-layers 5 --bottom-solid-layers 4 --fill-density 15% --fill-pattern gyroid --filament-diameter 1.75 --filament-density 1.24 --filament-type PLA --temperature 210 --first-layer-temperature 215 --bed-temperature 60 --first-layer-bed-temperature 60`.

| File | Sliced | Warnings | Layers | Time | Filament | Supports | Support material | Bed contact (mm²) |
|---|---|---|---|---|---|---|---|---|
| `stl/rear.stl` | yes | 0 | 623 | 3h 39m 34s | 43.61 g | build plate only | 6.6 g (15.1 %) | 352.2 |
| `stl/middle.stl` | yes | 0 | 203 | 56m 38s | 12.00 g | build plate only | 2.53 g (21.1 %) | 128.7 |
| `stl/front.stl` | yes | 0 | 663 | 3h 24m 28s | 35.20 g | build plate only | 6.75 g (19.2 %) | 241.0 |
| `dog_print.3mf` | yes | 0 | 567 | 7h 11m 49s | 74.99 g | none | 0.0 g (0.0 %) | - |

* Production total (rear + middle + front): **7 h 59 min, 91 g**.
* Middle: supports only under the two tongues (2.53 g).
* Rear: supports only under the haunch, model x = [-3.2, 48.5] mm, up to z = 34.8 mm; support moves inside the joint slot: **0**.
* Front: supports only at model x = [108.6, 154.5] mm (chin / throat column); support moves inside the joint slot: **0**.
* A self-support pass in the generator removed 0.0 cm³ (rear) and 1.8 cm³ (front) of material that would have needed support (the pass is switched off for the rear so its legs follow the drawing).
* The plate file was sliced without supports only to confirm it loads; for a real print enable build-plate-only supports for the front part.

## Known compromises

* Not physically printed; the snap force and joint friction depend on the printer. `CLIP_PRELOAD` is the single tuning parameter.
* Legs are staggered (one forward, one back on each end) to reproduce the four legs and the gap between the rear legs visible in the drawing.
  The rear haunch therefore has a flat underside around the legs and needs build-plate supports there; under the front chest the undersides are 45° facets instead.
* The middle piece reaches down to the bottom of the drawn box, so its tongues sit 10.7 mm above the bed and need two small support pads; their undersides will be slightly rough (the slot has 0.3 mm clearance below the tongue for that).
* A 45° wedge under each joint (behind the front legs, in front of the rear thigh) carries the slot floor; it sits slightly outside the drawn outline.
* The inside of the tail hook is filled to a 35° chord so the tail prints without support; the outer curve follows the drawing.
* The rear and front sections stand on two small feet while printing, so a brim is recommended. All three parts use build-plate-only supports.
* The dark scribble between rear body and middle box in the drawing is not modelled.
* PLA relaxes under constant strain, so joint friction will soften somewhat over time.
