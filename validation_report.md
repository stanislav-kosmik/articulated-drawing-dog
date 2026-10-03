# Validation report (final version)

Measured by `source/validate.py` (trimesh + manifold3d) and `source/slice_all.py` (PrusaSlicer CLI) on the delivered files.
Raw data: `build/validation.json`, `build/slicing.json`. Nothing here has been physically printed.

## Architecture

* Printed parts: **3** (rear, middle, front). Articulated interfaces: **2**.
* Joint 1: rear <-> middle, vertical axis at x=48.04. Joint 2: middle <-> front, vertical axis at x=96.38. Both lie in the torso.
* Tail: rear (same shell). Head and neck: front (same shell).
* Middle piece: 28.44 mm long at the flanks (11.34 mm at the centre line), cut from the same torso field as its neighbours.
* Assembled size: **150.75 x 30.11 x 113.38 mm**.

## Meshes

| File | Triangles | Watertight | 2-manifold / manifold3d | Outward normals | Shells | Zero-area | Duplicate | No self-intersection | Bounding box (mm) | Volume (cm³) |
|---|---|---|---|---|---|---|---|---|---|---|
| `stl/rear.stl` | 25748 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 66.35 x 30.01 x 113.38 | 85.3 |
| `stl/middle.stl` | 4730 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 52.6 x 30.01 x 24.92 | 11.97 |
| `stl/front.stl` | 30768 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 72.06 x 30.11 x 97.55 | 52.67 |

One shell per part means legs and tail (rear) and legs, neck, head and ears (front) are structurally one piece with their section.

## Joints

Joint dimensions (identical for both): post Ø11.0, clip bore Ø10.8, clip arm 1.8 mm, wrap 216°,
mouth 10.27 mm, tongue 7.0 mm, neck 6.0 mm, slot height 7.55 mm, seam radius 18.0 mm.

### Joint 1 — rear / middle

| Check | Result |
|---|---|
| Interference over ±30° (31 angles, 2° steps) | **0.0 mm³** |
| Hard stops (last collision-free angle, 0.5° steps) | **-32.0° … +32.0°** |
| Seam gap measured at -30° / 0° / +30° | 0.485 / 0.485 / 0.492 mm |
| Vertical play of the tongue (down / up) | 0.2 / 0.35 mm |
| Clip preload (overlap of as-printed clip with post) | 13.046 mm³ (= 0.1 mm radial, intentional) |
| Assembly path, rigid | 3.45 mm³ overlap (the snap) |
| Assembly path with clip arms opened | collision-free at **0.3 mm per arm** (room: 0.7 mm); est. peak strain 1.06 % in-layer |
| Retention: pulled apart 1.5 mm rigidly | 2.96 mm³ overlap -> the clip must open again to release |
| Sustained strain from preload (estimate) | 0.53 % |
| Slot floor under the clip (min / mean thickness, coverage) | 1.12 / 9.93 mm, 100.0 % |
| Material above the slot | 18.12 mm |
| Slot side walls at r = 17.4 / 15 / 12 mm (both sides) | [2.4, 2.45, 4.6, 4.6, 6.2, 6.2] mm |

### Joint 2 — middle / front

| Check | Result |
|---|---|
| Interference over ±30° (31 angles, 2° steps) | **0.0 mm³** |
| Hard stops (last collision-free angle, 0.5° steps) | **-32.0° … +32.0°** |
| Seam gap measured at -30° / 0° / +30° | 0.486 / 0.485 / 0.487 mm |
| Vertical play of the tongue (down / up) | 0.2 / 0.35 mm |
| Clip preload (overlap of as-printed clip with post) | 13.046 mm³ (= 0.1 mm radial, intentional) |
| Assembly path, rigid | 3.45 mm³ overlap (the snap) |
| Assembly path with clip arms opened | collision-free at **0.3 mm per arm** (room: 0.7 mm); est. peak strain 1.06 % in-layer |
| Retention: pulled apart 1.5 mm rigidly | 2.96 mm³ overlap -> the clip must open again to release |
| Sustained strain from preload (estimate) | 0.53 % |
| Slot floor under the clip (min / mean thickness, coverage) | 1.48 / 13.08 mm, 100.0 % |
| Material above the slot | 15.57 mm |
| Slot side walls at r = 17.4 / 15 / 12 mm (both sides) | [2.0, 2.0, 4.6, 4.6, 6.2, 6.2] mm |

### Whole dog

25 combinations of joint 1 and joint 2 in {-30, -15, 0, 15, 30}° (rear–middle, middle–front and rear–front checked):
maximum interference **0.0 mm³**.

## Structure

| Feature | Section: min x max mm, area mm² |
|---|---|
| Rear legs at 15 mm height | [[11.14, 11.5, 117.6], [11.5, 24.64, 270.7]] |
| Front legs at 15 mm height | [[10.43, 11.5, 109.4], [10.11, 11.5, 105.7]] |
| Tail at z = 95 mm | [[9.97, 10.88, 90.4]] |
| Tail root at z = 82 mm | [[10.0, 13.82, 118.4]] |
| Ears at z = 91.3 mm | [[5.44, 5.52, 23.7], [4.48, 4.49, 15.9]] |
| Tongue neck | 42.0 mm² |

## Standing

| Pose | Feet on ground | Centre of mass (mm) | Margin to tipping edge (mm) | Tilt to tip over |
|---|---|---|---|---|
| straight | 4 | [59.9, -0.5, 54.4] | 14.3 | 14.7° |
| both joints +30 (C-curve) | 4 | [55.0, 13.0, 54.4] | 10.6 | 11.0° |
| S-curve +30/-30 | 4 | [57.3, 8.9, 54.4] | 12.5 | 12.9° |
| joint 1 +30 | 4 | [56.7, 11.3, 54.4] | 12.7 | 13.2° |

## Slicing

Slicer: **[2026-10-03 09:16:15.373618] [0x00007b485160bd00] [trace]   Initializing StaticPrintConfigs**. Settings: `--nozzle-diameter 0.4 --layer-height 0.2 --first-layer-height 0.2 --perimeters 3 --top-solid-layers 5 --bottom-solid-layers 4 --fill-density 15% --fill-pattern gyroid --filament-diameter 1.75 --filament-density 1.24 --filament-type PLA --temperature 210 --first-layer-temperature 215 --bed-temperature 60 --first-layer-bed-temperature 60`.

| File | Sliced | Warnings | Layers | Time | Filament | Supports | Support material | Bed contact (mm²) |
|---|---|---|---|---|---|---|---|---|
| `stl/rear.stl` | yes | 0 | 567 | 3h 15m 12s | 37.70 g | none | 0.0 g (0.0 %) | 409.5 |
| `stl/middle.stl` | yes | 0 | 125 | 38m 1s | 7.50 g | none | 0.0 g (0.0 %) | 359.0 |
| `stl/front.stl` | yes | 0 | 663 | 3h 24m 27s | 35.20 g | build plate only | 6.75 g (19.2 %) | 241.0 |
| `dog_print.3mf` | yes | 0 | 567 | 7h 2m 52s | 73.87 g | none | 0.0 g (0.0 %) | - |

* Production total (rear + middle + front): **7 h 17 min, 80 g**.
* Rear: no supports. The only flat ceilings are the two short bridges around the pivot post ({'58.9': 116.3} mm² by height).
* Front: supports only at model x = [108.6, 154.5] mm (chin / throat column); support moves inside the joint slot: **0**.
* A self-support pass in the generator removed 3.2 cm³ (rear) and 1.8 cm³ (front) of material that would have needed support; this only affects undersides hidden in the side view.
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
