"""Blender (4.x) script: build dog_complete.blend from the generated STLs and render all views.
Run:  blender -b -P render_blender.py -- [quick]
"""
import bpy, sys, os, math
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import params as P
quick = "quick" in sys.argv
only = [a[5:] for a in sys.argv if a.startswith("only=")]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"   # CPU keeps the render reproducible on any machine
sc.cycles.samples = 48 if quick else 160
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.film_transparent = False

def mat(name, rgb, rough=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m
m_dog = mat("PLA_dog", (0.93, 0.50, 0.10))
m_floor = mat("floor", (0.90, 0.89, 0.86), 0.9)

objs = {}
for n in ("body", "head", "tail"):
    bpy.ops.wm.stl_import(filepath=f"{ROOT}/build/{n}_assembled.stl")
    o = bpy.context.selected_objects[0]; o.name = n
    o.data.materials.append(m_dog)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38)) if hasattr(bpy.ops.object, "shade_smooth_by_angle") else bpy.ops.object.shade_smooth()
    objs[n] = o
# joint pivots (rotate these empties to pose the dog)
def pivot(name, loc, child):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 8; e.location = loc
    sc.collection.objects.link(e)
    bpy.context.view_layer.update()
    child.parent = e; child.matrix_parent_inverse = e.matrix_world.inverted()
    return e
piv_head = pivot("JOINT_A_head_ball", P.BALL_C, objs["head"])
piv_tail = pivot("JOINT_B_tail_swivel", (P.TAIL_AXIS[0], P.TAIL_AXIS[1], P.SEAT_Z), objs["tail"])
objs["body"]["note"] = "Fixed part. Head and tail are parented to the JOINT_* empties."

# floor + backdrop
bpy.ops.mesh.primitive_plane_add(size=3000, location=(70, 0, 0)); fl = bpy.context.object; fl.name = "floor"
fl.data.materials.append(m_floor)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.92, 0.92, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.40
def light(name, loc, energy, size):
    l = bpy.data.lights.new(name, "AREA"); l.energy = energy; l.size = size
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    d = Vector((70, 0, 45)) - Vector(loc); o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o
key = light("key", (190, -260, 300), 1.1e6, 180)
fill = light("fill", (-180, -200, 150), 2.5e5, 250)
rim = light("rim", (60, 300, 220), 4.5e5, 200)

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
C = Vector((70, 0, 54))
def shoot(name, direction, ortho=True, scale=175, res=(1600, 1280), lens=85, dist=470, target=C):
    d = Vector(direction).normalized()
    cam.location = target + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam_d.type = "ORTHO" if ortho else "PERSP"
    cam_d.ortho_scale = scale; cam_d.lens = lens; cam_d.clip_end = 5000
    # keep the key light roughly on the camera side
    key.location = target + (d * 300 + Vector((90, 0, 0)).cross(d) * 0 + Vector((0, 0, 260)))
    key.rotation_euler = (target - key.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    if quick: sc.render.resolution_percentage = 50
    sc.render.filepath = f"{ROOT}/renders/{name}.png"
    if only and name not in only: return
    bpy.ops.render.render(write_still=True)

views = [("reference_side", (0, -1, 0.0)), ("opposite_side", (0, 1, 0.0)), ("front", (1, 0, 0.0)),
         ("rear", (-1, 0, 0.0)), ("top", (0.0001, -0.0001, 1))]
for n, d in views:
    shoot(n, d, ortho=True)
shoot("perspective_front", (0.75, -0.8, 0.38), ortho=False)
shoot("perspective_rear", (-0.8, -0.75, 0.42), ortho=False)

# posed hero: head turned and tilted, tail swung
piv_head.rotation_euler = (math.radians(8), math.radians(-6), math.radians(-32))
piv_tail.rotation_euler = (0, 0, math.radians(35))
shoot("hero", (0.62, -0.9, 0.33), ortho=False, res=(2400, 1800), lens=85, dist=560)
piv_head.rotation_euler = (0, 0, 0); piv_tail.rotation_euler = (0, 0, 0)
if not quick:
    bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/dog_complete.blend")
    for o in sc.objects: o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=f"{ROOT}/dog_preview.glb", use_selection=True, export_apply=True)
