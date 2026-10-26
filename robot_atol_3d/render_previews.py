"""Rendus de prévisualisation du robot ATOL (Cycles CPU).

Usage :
    blender -b -noaudio robot_atol.blend --python render_previews.py -- [samples] [taille]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "previews")
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(argv[0]) if argv else 48
SIZE = int(argv[1]) if len(argv) > 1 else 900

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = False  # le Blender d'Ubuntu est compilé sans OIDN
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = -0.35

world = bpy.data.worlds.new("Studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.8, 0.9, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
scene.world = world


def area(name, loc, energy, size, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA")
    l.energy, l.size, l.color = energy, size, color
    o = bpy.data.objects.new(name, l)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-2.5, -3.5, 3.5), 900, 3)
area("Fill", (3.0, -3.0, 1.5), 300, 4, (0.85, 0.9, 1.0))
area("Rim", (1.5, 3.5, 3.5), 700, 2, (0.8, 0.9, 1.0))

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 70
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
rig = bpy.data.objects["ATOL_Rig"]


def shot(name, azimuth, target=(0, 0, 1.06), dist=4.5, elev=8, frame=None, action=None):
    rig.animation_data.action = bpy.data.actions[action] if action else None
    if action is None:
        for pb in rig.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
    scene.frame_set(frame or 1)
    a, e = math.radians(azimuth), math.radians(elev)
    t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


shots = sys.argv[sys.argv.index("--") + 3:] if len(argv) > 2 else ["front", "left", "back", "threequarter", "hello", "face"]
for s in shots:
    if s == "front":
        shot("front", 0)
    elif s == "threequarter":
        shot("threequarter", -35)
    elif s == "left":
        shot("left", 90)
    elif s == "back":
        shot("back", 180)
    elif s == "hello":
        shot("hello", 20, frame=37, action="Hello")
    elif s == "face":
        shot("face", 15, target=(0, 0, 1.55), dist=3.2, elev=5, frame=37, action="Hello")
print("RENDER OK")
