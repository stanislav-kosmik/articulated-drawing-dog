"""Blender 4.x: build dog_complete.blend (posable: rotate the two JOINT_* empties about Z) and render everything.
Run: blender -b -P render_blender.py -- [quick] [only=name ...]"""
import bpy, sys, os, math, json
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import params as Q
info = json.load(open(f"{ROOT}/build/geometry_info.json"))
XA, XB = info["pivot_A_x"], info["pivot_B_x"]
quick = "quick" in sys.argv
only = [a[5:] for a in sys.argv if a.startswith("only=")]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 40 if quick else 140
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"

def mat(name, rgb, rough=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m
m_dog = mat("PLA", (0.93, 0.50, 0.10)); m_floor = mat("floor", (0.90, 0.89, 0.86), 0.9)
objs = {}
for n, f in (("rear", "rear_assembled"), ("middle", "middle_installed"), ("front", "front_assembled")):
    bpy.ops.wm.stl_import(filepath=f"{ROOT}/build/{f}.stl")
    o = bpy.context.selected_objects[0]; o.name = n; o.data.materials.append(m_dog)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    objs[n] = o
def empty(name, loc):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 10; e.location = loc; sc.collection.objects.link(e); return e
def parent(child, par):
    bpy.context.view_layer.update(); child.parent = par; child.matrix_parent_inverse = par.matrix_world.inverted()
j1 = empty("JOINT_1_rear_middle", (XA, 0, 60)); j2 = empty("JOINT_2_middle_front", (XB, 0, 60))
parent(j1, objs["rear"]); parent(objs["middle"], j1); parent(j2, objs["middle"]); parent(objs["front"], j2)

bpy.ops.mesh.primitive_plane_add(size=4000, location=(75, 0, 0)); fl = bpy.context.object; fl.name = "floor"; fl.data.materials.append(m_floor)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.92, 0.92, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.42
def light(name, loc, energy, size):
    l = bpy.data.lights.new(name, "AREA"); l.energy = energy; l.size = size
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o); return o
key = light("key", (0, 0, 0), 1.1e6, 180); fill = light("fill", (-180, -200, 150), 2.5e5, 250); rim = light("rim", (60, 300, 220), 4.5e5, 200)
C = Vector((75.35, 0, 56.6))
for l in (fill, rim): l.rotation_euler = (C - l.location).to_track_quat("-Z", "Y").to_euler()
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam

def shoot(name, direction, ortho=True, scale=164.3, res=(1300, 1000), lens=85, dist=480, target=C):
    if only and name not in only: return
    d = Vector(direction).normalized()
    cam.location = target + d * dist; cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam_d.type = "ORTHO" if ortho else "PERSP"; cam_d.ortho_scale = scale; cam_d.lens = lens; cam_d.clip_end = 6000
    key.location = target + d * 300 + Vector((0, 0, 260)); key.rotation_euler = (target - key.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if quick else 100
    sc.render.filepath = f"{ROOT}/renders/{name}.png"
    bpy.ops.render.render(write_still=True)

def pose(a1, a2):
    j1.rotation_euler = (0, 0, math.radians(a1)); j2.rotation_euler = (0, 0, math.radians(a2))

pose(0, 0)
shoot("side", (0, -1, 0))                       # frame matches the crop used in source_vs_model.png
shoot("opposite_side", (0, 1, 0))
shoot("front", (1, 0, 0)); shoot("rear", (-1, 0, 0)); shoot("top", (0.0001, -0.0001, 1))
shoot("perspective", (0.72, -0.85, 0.36), ortho=False)
shoot("perspective_rear", (-0.8, -0.75, 0.42), ortho=False)

R = Q.YAW_RANGE
demo = [("demo_0", 0, 0), ("demo_1", R, 0), ("demo_2", 0, R), ("demo_3", R, R), ("demo_4", R, -R)]
T2 = Vector((70, 8, 40))
for n, a1, a2 in demo:
    pose(a1, a2); shoot(n, (0.25, -0.62, 0.74), ortho=False, res=(1200, 1000), lens=80, dist=540, target=T2)
pose(R * 0.8, R * 0.8); shoot("hero", (0.62, -0.9, 0.36), ortho=False, res=(2000, 1500), lens=85, dist=560, target=Vector((72, 6, 52)))
pose(0, 0)
if not quick and not only:
    bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/dog_complete.blend")
    for o in sc.objects: o.select_set(o.name in objs)
    bpy.ops.export_scene.gltf(filepath=f"{ROOT}/dog_preview.glb", use_selection=True, export_apply=True)
