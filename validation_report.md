# Validation report

All numbers below were measured by `scripts/validate.py` (trimesh + manifold3d) and `scripts/slice_all.py`
(PrusaSlicer CLI) on the delivered files; raw data: `build/validation.json`, `build/slicing.json`.

## 1. Dimensions

Assembled, neutral pose: **141.23 x 32.9 x 110.47 mm** (length x width x height).
Solid volume 139.6 cm³.

## 2. Mesh quality

| File | Triangles | Watertight | 2-manifold edges / manifold3d status | Outward normals | Shells | Zero-area faces | Duplicate faces | Free of self-intersection | Bounding box (mm) |
|---|---|---|---|---|---|---|---|---|---|
| `stl/body.stl` | 51204 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 118.49 x 32.9 x 74.0 |
| `stl/head.stl` | 25746 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 39.84 x 26.0 x 40.7 |
| `stl/tail.stl` | 8492 | yes | yes / NoError | yes | 1 | 0 | 0 | yes | 27.26 x 58.22 x 9.8 |
| `dog_assembled.stl` | 85166 | yes | yes / NoError | yes | 3 | 0 | 0 | yes | 141.23 x 32.9 x 110.47 |
| `test/joint_tolerance_test.stl` | 33158 | yes | yes / NoError | yes | 4 | 0 | 0 | yes | 73.5 x 70.25 x 24.0 |

`dog_assembled.stl` intentionally contains 3 shells (body, head, tail in place, shown in their installed state);
the test file contains 4 separate test pieces. Each production STL is a single shell.

## 3. Joint A — head ball joint

| Quantity | Value |
|---|---|
| Ball diameter / width across flats | 12.0 / 7.6 mm |
| Socket diameter | 12.2 mm (radial clearance 0.1 mm) |
| Ball-half spread (as printed) | 0.25 mm per side -> elastic preload interference 0.15 mm per side (overlap volume 12.21 mm³) |
| Throat diameter | 11.773 mm |
| Stalk diameter / slot / moat outer diameter | 7.4 / 2.0 / 9.8 mm |
| Flexing length / half-stalk thickness | 12.6 / 2.7 mm |
| Min. head wall around socket + tunnel | 1.85 mm |
| Ball stalk cross-section (each half, at z = 60) | [[2.7, 7.12], [2.7, 7.12]] mm |

**Range of motion.** 351 poses were tested over yaw ±90° (15° steps) x nod ±15° (5° steps) x
sideways tilt ±12° (6° steps), limited to a combined tilt of 15.7°, with the ball in its installed state:
maximum body/head interference volume = **0.0 mm³**.

Single-axis hard stops (last collision-free angle): yaw -102.0° … +102.0°, nod -19.0° … +19.0°,
sideways tilt -19.0° … +19.0°.

Minimum body-to-head gap at sample poses (the 0.096 mm value is the ball/socket clearance itself, nominal 0.10):

| yaw | nod | tilt | min gap (mm) |
|---|---|---|---|
| 0 | 0 | 0 | 0.096 |
| 90 | 0 | 0 | 0.096 |
| -90 | 0 | 0 | 0.096 |
| 0 | 15 | 0 | 0.096 |
| 0 | -15 | 0 | 0.096 |
| 0 | 0 | 12 | 0.096 |
| 45 | 10 | 10 | 0.096 |
| -90 | -10 | -10 | 0.096 |
| 90 | 15 | 0 | 0.096 |
| -90 | 0 | 12 | 0.096 |

**Assembly path** (head pushed straight down (-z) onto the ball; path sampled every 0.5 mm over 20 mm): pushing the parts together rigidly gives up to 12.21 mm³ overlap
(= the snap). With both ball halves deflected inward the path becomes collision-free at **0.36 mm per half**;
the slot allows 1.0 mm. Estimated peak bending strain while snapping ≈ 0.92 %,
sustained strain from the preload ≈ 0.38 % (beam estimate).
**Retention:** lifting the seated head 1 mm rigidly produces 7.3 mm³ of overlap at the throat, i.e. it cannot come off without re-squeezing the ball.

## 4. Joint B — tail swivel

| Quantity | Value |
|---|---|
| Pin diameter / across flats / length | 10.0 / 9.8 / 21.5 mm |
| Bore diameter / depth | 10.4 / 22.6 mm (radial clearance 0.2 mm) |
| Barb diameter / engagement per side | 11.4 / 0.5 mm |
| Undercut cavity diameter | 12.2 mm |
| Friction band diameter | 10.6 mm (0.1 mm radial preload) |
| Slot / arm thickness / arm flex length | 3.6 / 3.2 / 16.3 mm |
| Axial play | 0.45 mm |
| Min. body wall around bore and undercut | 3.9 mm |

**Range of motion.** Full 360°, tested every 10° (36 positions). The only body/tail overlap is the intended friction band
(4.725–4.726 mm³, constant with angle, confined to the band: yes).
With the band excluded: interference **0.0 mm³**, minimum gap 0.15 mm.

**Assembly path** (tail peg pushed straight down (-z) into the bore; path sampled every 0.5 mm over 24 mm): rigid overlap up to 15.05 mm³ (the snap); collision-free once each arm is deflected
**0.6 mm** (slot allows 1.8 mm). Estimated peak strain ≈ 1.08 %, with layers running along the arms.
**Retention:** lifting the seated tail 2 mm rigidly gives 7.64 mm³ overlap (barbs on the ledge).

## 5. Feature thickness

| Feature | Measured section (mm) |
|---|---|
| Legs at 15 mm above floor (each of 4) | [[11.0, 13.99], [11.0, 13.49], [10.99, 11.49], [10.99, 11.49]] |
| Ears, 9 mm below the higher tip | [[7.25, 7.34], [6.73, 6.88]] |
| Ears, 4 mm below the higher tip | [[3.67, 3.74], [4.62, 4.65]] |
| Tail, mid-height | [[9.8, 10.14]] |

## 6. Standing stability

Feet in contact with the floor: **4** (footprint x [4.4, 104.8], y [-15.6, 15.6] mm). Uniform-density centre of mass:

| Pose | Centre of mass (mm) | Margin to edge of support polygon (mm) | Tilt needed to tip |
|---|---|---|---|
| neutral | [58.8, -0.0, 52.9] | 15.6 | 16.4° |
| head 90 left, tail 90 | [58.1, 0.7, 52.9] | 14.9 | 15.8° |
| head 90 right nose down, tail reversed | [58.1, -0.8, 52.7] | 14.8 | 15.7° |

## 7. Slicing

Slicer: **[2026-10-03 08:05:54.940926] [0x000077e8e7036d00] [trace]   Initializing StaticPrintConfigs**. Settings: `--nozzle-diameter 0.4 --layer-height 0.2 --first-layer-height 0.2 --perimeters 4 --top-solid-layers 5 --bottom-solid-layers 4 --fill-density 15% --fill-pattern gyroid --filament-diameter 1.75 --filament-density 1.24 --filament-type PLA --temperature 210 --first-layer-temperature 215 --bed-temperature 60 --first-layer-bed-temperature 60`.

| File | Sliced | Warnings | Layers | Est. time | Filament | Supports | Support share of filament | Bed contact (mm²) |
|---|---|---|---|---|---|---|---|---|
| `stl/body.stl` | yes | 0 | 466 | 7h 11m 23s | 84.55 g | on (build plate only) | 28.4 % | 597.6 |
| `stl/head.stl` | yes | 0 | 203 | 54m 52s | 11.02 g | off | 0.0 % | 408.2 |
| `stl/tail.stl` | yes | 0 | 49 | 21m 53s | 4.51 g | off | 0.0 % | 228.4 |
| `test/joint_tolerance_test.stl` | yes | 0 | 120 | 2h 50m 31s | 23.66 g | off | 0.0 % | 1139.9 |
| `dog_print.3mf` | yes | 0 | 516 | 8h 34m 40s | 101.14 g | on (build plate only) | 24.9 % | - |

Downward faces steeper than 45° (not on the bed), from the STL: body 1698.5 mm² (supported),
head 129.6 mm² and tail 241.1 mm² (unsupported; these are the rounded bottom edges,
the eye dimples, mouth groove, underside of the nose and the small flat cap of the socket roof — all short spans).
The plate file was sliced with supports on globally only to prove it loads and slices; in practice enable supports for the body only.

## 8. Known compromises

* **The body needs supports** (about a quarter of its filament) under the belly box, torso and between the staggered legs.
  This is the price of keeping the drawing's boxy belly and four separately visible legs in a single strong part.
* **The ball stalk is printed upright**, so its layers lie across the bending direction. The geometry keeps the snap strain
  low (≈ 0.92 %), but it is the most delicate feature: push the head on straight, do not lever it sideways past its stops.
* The chest under the head stands about 6–8 mm further forward than in the drawing, to carry the ball stud.
* Tail and legs are thicker than the pencil lines, for strength.
* The little squiggle drawn between hind leg and belly is not modelled.
* Joint feel depends on the printer; nothing here has been physically printed. Print the tolerance test first.
* PLA slowly relaxes under constant strain, so joint friction will soften somewhat over months.
