"""Construit le robot ATOL en 3D (modèle + matériaux + rig + animations de démo).

Usage :
    blender -b -noaudio --python build_robot.py

Produit dans le même dossier :
    robot_atol.blend  (scène Blender avec rig et actions "Hello" et "Idle")
    robot_atol.glb    (glTF binaire, mesh skinné + animations)
    robot_atol.fbx    (FBX pour Cinema 4D / Maya / Unity / Unreal)

Conventions : 1 unité = 1 m (robot ~2,1 m), Z vers le haut, le robot regarde vers -Y.
Les pièces sont rigides et chacune est pondérée à 100 % sur un os (style robot).
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
COL = bpy.data.collections.new("ATOL_Robot_parts")
scene.collection.children.link(COL)

PARTS = []  # (objet, os ou fonction de pondération)


# ---------------------------------------------------------------- matériaux
def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(name, color, rough=0.4, metal=0.0, emit=0.0, alpha=1.0, coat=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col = srgb(color)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
        m.shadow_method = "HASHED"
    if alpha < 0.5:
        b.inputs["IOR"].default_value = 1.05  # verres : reflets discrets
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    m.diffuse_color = (*col, alpha)
    return m



def image_material(name, path, rough=0.15, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if emit:
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.03
    return m


M = {
    "white": material("Robot_White", "#F2F4F8", rough=0.25, coat=0.6),
    "panel": material("Robot_NavyPanel", "#1A2440", rough=0.25, coat=0.6),
    "seam": material("Robot_Seam", "#AEB6C2", rough=0.4),
    "joint": material("Robot_Joint", "#1B202B", rough=0.35, metal=0.3),
    "metal": material("Robot_Silver", "#9AA3AF", rough=0.25, metal=0.9),
    "hand": material("Robot_Hand", "#20242C", rough=0.35, metal=0.2),
    "knuckle": material("Robot_Knuckle", "#5C6370", rough=0.3, metal=0.6),
    "frame": material("Glasses_Frame", "#0D0F13", rough=0.15, coat=0.8),
    "glass": material("Glasses_Lens", "#E4F2FF", rough=0.0, alpha=0.03),
    "glow": material("Cyan_Glow", "#2BC4FF", rough=0.2, emit=7.0),
    "accent": material("Blue_Accent", "#1D57D6", rough=0.2, coat=0.8),
    "shirt": material("Tshirt_Blue", "#124BC8", rough=0.75, sheen=0.2),
    "shirt_dark": material("Tshirt_Seam", "#0F3FAE", rough=0.8, sheen=0.4),
    "print": material("Tshirt_Print_ATOL", "#FFFFFF", rough=0.5),
    "eye_rim": material("Eye_Rim", "#08163A", rough=0.1, coat=1.0),
    "iris": image_material("Eye_Iris", os.path.join(HERE, "textures", "iris.png"), emit=0.25),
    "highlight": material("Eye_Highlight", "#FFFFFF", rough=0.1, emit=3.0),
    "brow": material("Eyebrow", "#4A5260", rough=0.4),
    "mouth": material("Mouth", "#5A0E16", rough=0.5),
    "tongue": material("Tongue", "#F0646A", rough=0.45),
    "cheek": material("Cheek_Blush", "#FF8E9C", rough=0.6, alpha=0.4),
    "sole": material("Sole", "#1A1D24", rough=0.7),
}


# ---------------------------------------------------------------- géométrie
def new_object(name, verts, faces, mat, weight, smooth=True, subsurf=0, matrix=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    me.materials.append(mat)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if subsurf:
        mod = ob.modifiers.new("Subdiv", "SUBSURF")
        mod.levels = mod.render_levels = subsurf
    if matrix is not None:
        ob.matrix_world = matrix
    if weight is not None:
        PARTS.append((ob, weight))
    return ob


def frame_matrix(origin, direction, q=None):
    """Matrice qui envoie l'axe local +Z sur `direction`, origine en `origin`."""
    if q is None:
        q = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized())
    return Matrix.Translation(Vector(origin)) @ q.to_matrix().to_4x4()


def loft(name, p0, p1, profile, mat, weight, seg=32, subsurf=1, caps=True):
    """Révolution le long de p0->p1. profile = [(z, rx, ry)] avec z en distance absolue."""
    verts, faces = [], []
    for z, rx, ry in profile:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((rx * math.cos(a), ry * math.sin(a), z))
    n = len(profile)
    for r in range(n - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((r * seg + i, r * seg + j, (r + 1) * seg + j, (r + 1) * seg + i))
    if caps:
        verts.append((0, 0, profile[0][0]))
        c = len(verts) - 1
        faces += [(c, (i + 1) % seg, i) for i in range(seg)]
        verts.append((0, 0, profile[-1][0]))
        c = len(verts) - 1
        base = (n - 1) * seg
        faces += [(c, base + i, base + (i + 1) % seg) for i in range(seg)]
    d = Vector(p1) - Vector(p0)
    return new_object(name, verts, faces, mat, weight, subsurf=subsurf, matrix=frame_matrix(p0, d))


def capsule(name, p0, p1, r0, r1, mat, weight, seg=24):
    L = (Vector(p1) - Vector(p0)).length
    prof = []
    for k in range(1, 5):
        a = math.radians(90 * k / 4)
        prof.append((-r0 * math.cos(a), r0 * math.sin(a), r0 * math.sin(a)))
    for k in range(4, 0, -1):
        a = math.radians(90 * k / 4)
        prof.append((L + r1 * math.cos(a), r1 * math.sin(a), r1 * math.sin(a)))
    return loft(name, p0, p1, prof, mat, weight, seg=seg)


def ellipsoid(name, center, radii, mat, weight, q=None, seg=32, rings=16, subsurf=1):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    me.materials.append(mat)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if subsurf:
        mod = ob.modifiers.new("Subdiv", "SUBSURF")
        mod.levels = mod.render_levels = subsurf
    rot = (q or Quaternion()).to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(Vector(center)) @ rot
    if weight is not None:
        PARTS.append((ob, weight))
    return ob


def torus(name, center, axis, major, minor, mat, weight, major_y=None, seg=48, mseg=12):
    major_y = major_y or major
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        cx, cy = major * math.cos(a), major_y * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            verts.append((cx + minor * math.cos(b) * nx, cy + minor * math.cos(b) * ny, minor * math.sin(b)))
    for i in range(seg):
        for j in range(mseg):
            i2, j2 = (i + 1) % seg, (j + 1) % mseg
            faces.append((i * mseg + j, i * mseg + j2, i2 * mseg + j2, i2 * mseg + j))
    return new_object(name, verts, faces, mat, weight, matrix=frame_matrix(center, axis))


def box(name, center, half, mat, weight, bevel=0.01, q=None, subsurf=1):
    hx, hy, hz = half
    verts = [(x * hx, y * hy, z * hz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = new_object(name, verts, faces, mat, weight, smooth=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 4
    if subsurf:
        s = ob.modifiers.new("Subdiv", "SUBSURF")
        s.levels = s.render_levels = subsurf
    ob.matrix_world = Matrix.Translation(Vector(center)) @ (q or Quaternion()).to_matrix().to_4x4()
    return ob


def tube(name, pts, radius, mat, weight, cyclic=False, nurbs=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS" if nurbs else "POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = cyclic
    if nurbs:
        sp.order_u = 3
        sp.use_endpoint_u = not cyclic
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    COL.objects.link(ob)
    PARTS.append((ob, weight))
    return ob


def decal(name, center, outline, proj, mat, weight, rings=7, thickness=0.0):
    """Surface remplie à partir d'un contour 2D (x, z), plaquée via proj(x, z)."""
    cx, cz = center
    n = len(outline)
    verts = [proj(cx, cz)]
    for k in range(1, rings + 1):
        f = k / rings
        verts += [proj(cx + (x - cx) * f, cz + (z - cz) * f) for x, z in outline]
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for k in range(1, rings):
        b0, b1 = 1 + (k - 1) * n, 1 + k * n
        faces += [(b0 + i, b1 + i, b1 + (i + 1) % n, b0 + (i + 1) % n) for i in range(n)]
    ob = new_object(name, verts, faces, mat, weight)
    if thickness:
        s = ob.modifiers.new("Solidify", "SOLIDIFY")
        s.thickness = thickness
        s.offset = -1
    return ob


def superellipse(cx, cz, a, b, n=4.0, count=64):
    pts = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        pts.append((cx + a * math.copysign(abs(c) ** (2 / n), c), cz + b * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def ellipse(cx, cz, a, b, count=48):
    return superellipse(cx, cz, a, b, 2.0, count)


def frame_quat(zdir, xhint):
    """Quaternion d'un repère dont l'axe Z suit zdir et l'axe X est au plus près de xhint."""
    z = Vector(zdir).normalized()
    x = (Vector(xhint) - z * Vector(xhint).dot(z)).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed().to_quaternion()


def uv_dome(name, center, radii, mat, weight, q):
    """Dôme ellipsoïdal avec UV planaires (face -Y locale) pour une texture d'iris."""
    ob = ellipsoid(name, center, radii, mat, weight, q=q, seg=48, rings=24)
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + co.x / (2 * radii[0]), 0.5 + co.z / (2 * radii[2]))
    return ob


def import_logo_mesh(width, center_z):
    """Logo ATOL vectorisé (SVG potrace) -> mesh plat dense, dans le plan XZ, face -Y."""
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(HERE, "textures", "atol_logo.svg"))
    curves = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in curves:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in curves:
        bpy.data.objects.remove(o)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    k = width / (max(xs) - min(xs))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    for v in bm.verts:
        v.co = Vector(((v.co.x - cx) * k, -0.6, (v.co.y - cy) * k + center_z))
    for _ in range(2):
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > 0.012], cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    me = bpy.data.meshes.new("Tshirt_Print_ATOL")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Tshirt_Print_ATOL", me)
    COL.objects.link(ob)
    return ob


# ---------------------------------------------------------------- tête
HC = Vector((0, 0, 1.68))
RX, RY, RZ = 0.44, 0.42, 0.43


def surf(x, z, off=0.0):
    """Point de la face avant de la tête (x, z relatifs au centre)."""
    a, b, c = RX + off, RY + off, RZ + off
    t = 1 - (x / a) ** 2 - (z / c) ** 2
    return HC + Vector((x, -b * math.sqrt(max(t, 0.0)), z))


def surf_normal(p):
    l = p - HC
    return Vector((l.x / RX ** 2, l.y / RY ** 2, l.z / RZ ** 2)).normalized()


def facing(n):
    """Rotation qui oriente l'axe local -Y le long de la normale n."""
    return Vector((0, -1, 0)).rotation_difference(n)


ellipsoid("Head", HC, (RX, RY, RZ), M["white"], "head", seg=64, rings=32)

# bande bleu marine sur le dessus du crâne (intersection booléenne)
panel = ellipsoid("Head_Panel", HC, (RX * 1.012, RY * 1.012, RZ * 1.012), M["panel"], "head", seg=64, rings=32, subsurf=2)
cutter = box("cutter", HC + Vector((0, 0, 0.47)), (0.20, 0.6, 0.27), M["panel"], None, bevel=0.07, subsurf=1)
boo = panel.modifiers.new("Bool", "BOOLEAN")
boo.operation = "INTERSECT"
boo.solver = "EXACT"
boo.object = cutter

# rainures de panneaux du casque
k = math.sqrt(1 - (0.10 / RY) ** 2)
torus("Head_Seam", HC + Vector((0, 0.10, 0)), (0, 1, 0), RX * k, 0.0045, M["seam"], "head", major_y=RZ * k, seg=96, mseg=8)
k = math.sqrt(1 - (0.22 / RZ) ** 2)
torus("Head_Seam_Low", HC + Vector((0, 0, -0.22)), (0, 0, 1), RX * k, 0.0045, M["seam"], "head", major_y=RY * k, seg=96, mseg=8)
box("Head_BackSlot", HC + Vector((0, 0.305, -0.29)), (0.07, 0.03, 0.022), M["joint"], "head", bevel=0.012)

# casque audio (oreillettes)
EAR_Z = HC.z - 0.02
for s, side in ((1, "L"), (-1, "R")):
    loft(f"EarPod_Base.{side}", (s * 0.33, 0.03, EAR_Z), (s * 0.47, 0.03, EAR_Z),
         [(0, 0.15, 0.15), (0.03, 0.178, 0.178), (0.14, 0.178, 0.178)], M["joint"], "head", seg=48)
    loft(f"EarPod_Face.{side}", (s * 0.46, 0.03, EAR_Z), (s * 0.52, 0.03, EAR_Z),
         [(0, 0.17, 0.17), (0.035, 0.17, 0.17), (0.05, 0.155, 0.155), (0.055, 0.12, 0.12)], M["accent"], "head", seg=48)
    loft(f"EarPod_Disc.{side}", (s * 0.505, 0.03, EAR_Z), (s * 0.528, 0.03, EAR_Z),
         [(0, 0.108, 0.108), (0.023, 0.108, 0.108)], M["joint"], "head", seg=48, subsurf=0)
    torus(f"EarPod_Ring.{side}", (s * 0.524, 0.03, EAR_Z), (s, 0, 0), 0.088, 0.011, M["glow"], "head")
    ellipsoid(f"EarPod_Cap.{side}", (s * 0.528, 0.03, EAR_Z), (0.065, 0.065, 0.016), M["eye_rim"], "head",
              q=Vector((0, 0, 1)).rotation_difference(Vector((s, 0, 0))))

# lunettes : grosses montures rectangulaires + branches "tech" à LEDs
LENS_Z, LENS_X, LA, LB, GOFF = -0.035, 0.215, 0.175, 0.128, 0.075
for s, side in ((1, "L"), (-1, "R")):
    outline = superellipse(s * LENS_X, LENS_Z, LA, LB, 5.0, 72)
    tube(f"Glasses_Frame.{side}", [surf(x, z, GOFF) for x, z in outline], 0.028, M["frame"], "head", cyclic=True)
    top = [surf(s * LENS_X + t * LA * 0.92, LENS_Z + LB + 0.008, GOFF + 0.004) for t in (-1, -0.5, 0, 0.5, 1)]
    tube(f"Glasses_Brow.{side}", top, 0.031, M["frame"], "head", nurbs=True)
    decal(f"Glasses_Lens.{side}", (s * LENS_X, LENS_Z), superellipse(s * LENS_X, LENS_Z, LA - 0.01, LB - 0.01, 5.0),
          lambda x, z: surf(x, z, GOFF), M["glass"], "head")
    p0 = surf(s * (LENS_X + LA - 0.005), LENS_Z + 0.02, GOFF)
    p1 = Vector((s * 0.41, -0.06, EAR_Z + 0.0))
    d = p1 - p0
    q = frame_quat(d, (s, 0, 0))
    mid = (p0 + p1) / 2
    box(f"Glasses_Temple.{side}", mid, (0.02, 0.04, d.length / 2 + 0.02), M["frame"], "head", bevel=0.012, q=q)
    for dz in (-0.045, 0.0):
        box(f"Glasses_LED{dz}.{side}", mid + q @ Vector((0.019, 0.0, dz + 0.02)), (0.004, 0.006, 0.022),
            M["glow"], "head", bevel=0.003, q=q, subsurf=0)
bridge = [surf(x, LENS_Z + 0.06 + 0.012 * (1 - (x / 0.05) ** 2), GOFF + 0.004) for x in (-0.05, -0.025, 0, 0.025, 0.05)]
tube("Glasses_Bridge", bridge, 0.024, M["frame"], "head", nurbs=True)

# sourcils
for s, side in ((1, "L"), (-1, "R")):
    pts = [surf(s * (0.13 + 0.15 * t), 0.165 + 0.025 * math.sin(math.pi * t), 0.006) for t in (0, 0.25, 0.5, 0.75, 1)]
    tube(f"Eyebrow.{side}", pts, 0.009, M["brow"], "head", nurbs=True)

# yeux : contour marine + dôme d'iris texturé + reflets
EYES = {}
for s, side in ((1, "L"), (-1, "R")):
    e = surf(s * LENS_X, LENS_Z, 0.0)
    n = surf_normal(e)
    q = facing(n)
    EYES[side] = (e, n)
    bone = f"eye.{side}"

    def at(lx, lz, off):
        return e + q @ Vector((lx, -off, lz))

    ellipsoid(f"Eye_Rim.{side}", at(0, 0, 0.0), (0.112, 0.03, 0.116), M["eye_rim"], bone, q=q)
    uv_dome(f"Eye_Iris.{side}", at(0, 0, 0.006), (0.1, 0.034, 0.104), M["iris"], bone, q=q)
    ellipsoid(f"Eye_Highlight.{side}", at(-0.036, 0.04, 0.038), (0.028, 0.008, 0.03), M["highlight"], bone, q=q)
    ellipsoid(f"Eye_Highlight2.{side}", at(0.038, -0.04, 0.034), (0.012, 0.006, 0.012), M["highlight"], bone, q=q)

# bouche ouverte + langue, joues
MOUTH_Z, MW = -0.235, 0.07
mouth_pts = []
for i in range(24):  # arc inférieur, de gauche à droite
    x = -MW + 2 * MW * i / 23
    mouth_pts.append((x, 0.01 - 0.08 * max(0.0, 1 - (x / MW) ** 2) ** 0.6))
for i in range(1, 23):  # bord supérieur (sourire), de droite à gauche
    x = MW - 2 * MW * i / 23
    mouth_pts.append((x, 0.016 * (x / MW) ** 2))
mouth_pts = [(x, MOUTH_Z + z) for x, z in mouth_pts]
decal("Mouth", (0, MOUTH_Z - 0.035), mouth_pts, lambda x, z: surf(x, z, 0.003), M["mouth"], "mouth", thickness=0.004)
decal("Tongue", (0, MOUTH_Z - 0.05), ellipse(0, MOUTH_Z - 0.05, 0.04, 0.022),
      lambda x, z: surf(x, z, 0.0055), M["tongue"], "mouth")
for s, side in ((1, "L"), (-1, "R")):
    decal(f"Cheek.{side}", (s * 0.27, -0.205), ellipse(s * 0.27, -0.205, 0.05, 0.028),
          lambda x, z: surf(x, z, 0.0035), M["cheek"], "head")

# ---------------------------------------------------------------- cou
loft("Neck_Core", (0, 0, 1.12), (0, 0, 1.36), [(0, 0.07, 0.07), (0.24, 0.07, 0.07)], M["joint"], "neck", subsurf=0)
for i, (z, mat) in enumerate(((1.218, "metal"), (1.245, "joint"), (1.272, "metal"))):
    torus(f"Neck_Ring{i}", (0, 0, z), (0, 0, 1), 0.08, 0.016, M[mat], "neck")

# ---------------------------------------------------------------- torse : body bleu échancré
Z_HIPS, Z_SPINE, Z_CHEST, Z_NECK, Z_HEAD = 0.62, 0.80, 0.98, 1.16, 1.28


def torso_weight(co):
    z = co.z

    def ramp(a, b):
        return min(1.0, max(0.0, (z - a) / (b - a)))

    w_spine = ramp(0.76, 0.86)
    w_chest = ramp(0.98, 1.06)
    return {"hips": 1 - w_spine, "spine": w_spine - w_chest, "chest": w_chest}


TORSO = [(0.57, 0.22, 0.18), (0.60, 0.26, 0.21), (0.66, 0.28, 0.222), (0.75, 0.28, 0.225), (0.88, 0.29, 0.235), (1.00, 0.295, 0.235),
         (1.08, 0.29, 0.23), (1.14, 0.25, 0.205), (1.19, 0.16, 0.135), (1.215, 0.10, 0.085)]
HEM_RISE = [0.08, 0.07, 0.035, 0.01]  # échancrure aux hanches (anneaux du bas)
seg = 48
verts, faces = [], []
for r, (z, rx, ry) in enumerate(TORSO):
    rise = HEM_RISE[r] if r < len(HEM_RISE) else 0.0
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((rx * math.cos(a), ry * math.sin(a), z + rise * math.cos(a) ** 2))
for r in range(len(TORSO) - 1):
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((r * seg + i, r * seg + j, (r + 1) * seg + j, (r + 1) * seg + i))
verts.append((0, 0, TORSO[0][0] - 0.005))
c = len(verts) - 1
faces += [(c, (i + 1) % seg, i) for i in range(seg)]
verts.append((0, 0, TORSO[-1][0]))
c = len(verts) - 1
base = (len(TORSO) - 1) * seg
faces += [(c, base + i, base + (i + 1) % seg) for i in range(seg)]
shirt = new_object("Tshirt", verts, faces, M["shirt"], torso_weight, subsurf=2)
torus("Tshirt_Collar", (0, 0, 1.2), (0, 0, 1), 0.112, 0.02, M["shirt_dark"], "chest", major_y=0.098)


def torso_radius(z):
    for (z0, rx0, ry0), (z1, rx1, ry1) in zip(TORSO, TORSO[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
    return TORSO[-1][1:]


# couture du panneau de dos
back = []
for x, z in superellipse(0, 0.9, 0.17, 0.17, 4.0, 64):
    rx, ry = torso_radius(z)
    back.append(Vector((x, ry * 0.97 * math.sqrt(max(0.0, 1 - (x / rx) ** 2)) + 0.0, z)))
tube("Tshirt_BackSeam", back, 0.006, M["shirt_dark"], torso_weight, cyclic=True)

# logo ATOL officiel (vectorisé) plaqué sur la poitrine
logo = import_logo_mesh(0.40, 0.975)
logo.data.materials.append(M["print"])
sw = logo.modifiers.new("Wrap", "SHRINKWRAP")
sw.target = shirt
sw.wrap_method = "PROJECT"
sw.use_project_y = True
sw.use_negative_direction = False
sw.use_positive_direction = True
sw.offset = 0.003
sol = logo.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.003
sol.offset = 1
PARTS.append((logo, torso_weight))

# bassin blanc (visible sous l'échancrure)
loft("Pelvis", (0, 0, 0), (0, 0, 1), [(0.55, 0.12, 0.10), (0.58, 0.22, 0.17), (0.64, 0.24, 0.185),
                                      (0.72, 0.23, 0.18)], M["white"], "hips", seg=32)

# ---------------------------------------------------------------- bras
THETA = math.radians(48)  # A-pose : bras à 48° de la verticale
HS, WRIST = 1.75, -0.35  # échelle des mains, position du poignet le long du bras
FINGERS = [  # nom, y (avant < 0), longueurs, rayon
    ("index", -0.034, 0.042, 0.036, 0.0135),
    ("middle", -0.0115, 0.046, 0.038, 0.0135),
    ("ring", 0.0115, 0.043, 0.036, 0.013),
    ("pinky", 0.034, 0.036, 0.030, 0.012),
]
ARM = {}  # repères des os de bras, en espace monde

for s, side in ((1, "L"), (-1, "R")):
    S = Vector((s * 0.27, 0, 1.10))
    st, ct = math.sin(THETA), math.cos(THETA)
    R = Matrix(((ct, 0, -s * st), (0, 1, 0), (s * st, 0, ct)))  # colonnes : X=extérieur, Y=arrière, Z=remontée du bras

    def P(x, y, z):
        return S + R @ Vector((s * x, y, z))

    def Ph(x, y, z):  # main agrandie autour du poignet (mains "cartoon")
        return P(x * HS, y * HS, WRIST + (z - WRIST) * HS)

    Rq = R.to_quaternion()
    L_ = f".{side}"
    loft("Sleeve" + L_, P(0, 0, 0), P(0, 0, -1), [(-0.07, 0.08, 0.08), (-0.05, 0.112, 0.112), (0.0, 0.122, 0.122),
                                                   (0.08, 0.124, 0.124), (0.115, 0.128, 0.128), (0.122, 0.118, 0.118),
                                                   (0.124, 0.06, 0.06)], M["shirt"], "upper_arm" + L_, seg=32)
    capsule("UpperArm" + L_, P(0, 0, -0.03), P(0, 0, -0.14), 0.068, 0.068, M["white"], "upper_arm" + L_)
    loft("Elbow" + L_, P(0, 0, -0.145), P(0, 0, -1), [(0, 0.056, 0.056), (0.005, 0.074, 0.074), (0.055, 0.074, 0.074),
                                                     (0.06, 0.056, 0.056)], M["joint"], "forearm" + L_)
    loft("Forearm" + L_, P(0, 0, -0.195), P(0, 0, -1), [(0, 0.05, 0.05), (0.005, 0.076, 0.076), (0.025, 0.085, 0.085),
                                                       (0.08, 0.09, 0.09), (0.125, 0.082, 0.082), (0.14, 0.072, 0.072),
                                                       (0.145, 0.05, 0.05)], M["white"], "forearm" + L_)
    loft("Wrist" + L_, P(0, 0, -0.33), P(0, 0, -1), [(0, 0.058, 0.058), (0.03, 0.058, 0.058)], M["joint"], "hand" + L_, subsurf=0)
    box("Palm" + L_, Ph(-0.003, 0, -0.402), (0.022 * HS, 0.048 * HS, 0.046 * HS), M["hand"], "hand" + L_, bevel=0.016 * HS, q=Rq)
    box("HandPlate" + L_, Ph(0.017, 0, -0.398), (0.009 * HS, 0.042 * HS, 0.036 * HS), M["white"], "hand" + L_, bevel=0.007 * HS, q=Rq)
    for name, y, l1, l2, r in FINGERS:
        r *= HS
        b1, b2 = f"{name}_01{L_}", f"{name}_02{L_}"
        base = Vector((-0.005, y, -0.445))
        d1 = Vector((-0.15, 0, -1)).normalized()
        d2 = Vector((-0.45, 0, -1)).normalized()
        mid, tip = base + d1 * l1, base + d1 * l1 + d2 * l2
        ellipsoid(f"Knuckle_{name}{L_}", Ph(*base), (r * 1.15,) * 3, M["knuckle"], b1, seg=16, rings=8)
        capsule(f"Finger_{name}_01{L_}", Ph(*base), Ph(*mid), r, r, M["hand"], b1, seg=16)
        ellipsoid(f"FingerJoint_{name}{L_}", Ph(*mid), (r * 1.1,) * 3, M["knuckle"], b2, seg=16, rings=8)
        capsule(f"Finger_{name}_02{L_}", Ph(*mid), Ph(*tip), r * 0.98, r * 0.95, M["white"], b2, seg=16)
        ARM[b1] = (Ph(*base), Ph(*mid), "hand" + L_)
        ARM[b2] = (Ph(*mid), Ph(*tip), b1)
    tb = Vector((-0.015, -0.046, -0.38))
    tm = tb + Vector((-0.35, -0.6, -0.7)).normalized() * 0.036
    tt = tm + Vector((-0.45, -0.35, -0.8)).normalized() * 0.03
    ellipsoid("Knuckle_thumb" + L_, Ph(*tb), (0.017 * HS,) * 3, M["knuckle"], "thumb_01" + L_, seg=16, rings=8)
    capsule("Finger_thumb_01" + L_, Ph(*tb), Ph(*tm), 0.0145 * HS, 0.0145 * HS, M["hand"], "thumb_01" + L_, seg=16)
    ellipsoid("FingerJoint_thumb" + L_, Ph(*tm), (0.016 * HS,) * 3, M["knuckle"], "thumb_02" + L_, seg=16, rings=8)
    capsule("Finger_thumb_02" + L_, Ph(*tm), Ph(*tt), 0.014 * HS, 0.013 * HS, M["white"], "thumb_02" + L_, seg=16)
    ARM["thumb_01" + L_] = (Ph(*tb), Ph(*tm), "hand" + L_)
    ARM["thumb_02" + L_] = (Ph(*tm), Ph(*tt), "thumb_01" + L_)
    ARM["shoulder" + L_] = (Vector((s * 0.08, 0, 1.10)), S, "chest")
    ARM["upper_arm" + L_] = (S, P(0, 0, -0.17), "shoulder" + L_)
    ARM["forearm" + L_] = (P(0, 0, -0.17), P(0, 0, -0.35), "upper_arm" + L_)
    ARM["hand" + L_] = (P(0, 0, -0.35), Ph(0, 0, -0.445), "forearm" + L_)


# ---------------------------------------------------------------- jambes et baskets
SHOE = [  # y (talon -> pointe), demi-largeur, demi-hauteur
    (0.20, 0.07, 0.05), (0.185, 0.11, 0.085), (0.14, 0.128, 0.098), (0.05, 0.132, 0.096), (-0.06, 0.132, 0.09),
    (-0.17, 0.13, 0.08), (-0.25, 0.116, 0.07), (-0.30, 0.09, 0.055), (-0.325, 0.05, 0.035)]


def shoe_shell(name, x, mat, weight, grow=0.0, flat=None, z_bottom=0.045):
    """Basket : sections elliptiques le long de -Y, à plat sur le sol."""
    seg, verts, faces = 32, [], []
    for y, w, h in SHOE:
        w, h = w + grow, (flat if flat else h + grow)
        zc = z_bottom - grow + h
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((x + w * math.cos(a), y, zc + h * math.sin(a)))
    n = len(SHOE)
    for r in range(n - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((r * seg + i, r * seg + j, (r + 1) * seg + j, (r + 1) * seg + i))
    for r, sign in ((0, 1), (n - 1, -1)):
        y, w, h = SHOE[r]
        verts.append((x, y + sign * 0.004, z_bottom - grow + (flat if flat else h + grow)))
        c = len(verts) - 1
        faces += [(c, r * seg + (i + 1) % seg, r * seg + i) for i in range(seg)]
    ob = new_object(name, verts, faces, mat, weight, subsurf=2)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def shoe_cap(name, x, ycut, front, weight):
    """Coque bleue (bout ou talon) : coque légèrement agrandie ∩ demi-espace."""
    cap = shoe_shell(name, x, M["accent"], weight, grow=0.006)
    cy = ycut - 0.5 if front else ycut + 0.5
    cut = box(name + "_cut", (x, cy, 0.30), (0.3, 0.5, 0.3), M["accent"], None, bevel=0.0, subsurf=0)
    b = cap.modifiers.new("Bool", "BOOLEAN")
    b.operation = "INTERSECT"
    b.solver = "EXACT"
    b.object = cut


LEG = {}
for s, side in ((1, "L"), (-1, "R")):
    L_ = f".{side}"
    x = s * 0.155
    H, K, A = Vector((x, 0, 0.64)), Vector((x, 0, 0.42)), Vector((x, 0, 0.19))
    ellipsoid("HipJoint" + L_, H, (0.095,) * 3, M["white"], "thigh" + L_)
    loft("Thigh" + L_, (x, 0, 0), (x, 0, 1), [(0.44, 0.07, 0.07), (0.45, 0.096, 0.096), (0.58, 0.1, 0.1),
                                             (0.62, 0.08, 0.08)], M["white"], "thigh" + L_)
    loft("Knee" + L_, (x, 0, 0), (x, 0, 1), [(0.39, 0.08, 0.08), (0.395, 0.102, 0.102), (0.45, 0.102, 0.102),
                                            (0.455, 0.08, 0.08)], M["joint"], "shin" + L_)
    box("KneePlate" + L_, (x, -0.099, 0.422), (0.045, 0.012, 0.02), M["metal"], "shin" + L_, bevel=0.008)
    loft("Shin" + L_, (x, 0, 0), (x, 0, 1), [(0.40, 0.07, 0.07), (0.395, 0.1, 0.1), (0.32, 0.108, 0.108),
                                            (0.24, 0.122, 0.118), (0.20, 0.12, 0.116), (0.18, 0.08, 0.08)],
         M["white"], "shin" + L_)
    shoe_shell("Shoe" + L_, x, M["white"], "foot" + L_)
    shoe_cap("Shoe_Toe" + L_, x, -0.15, True, "foot" + L_)
    shoe_cap("Shoe_Heel" + L_, x, 0.135, False, "foot" + L_)
    shoe_shell("Sole" + L_, x, M["sole"], "foot" + L_, grow=0.01, flat=0.026, z_bottom=0.01)
    LEG["thigh" + L_] = (H, K, "hips")
    LEG["shin" + L_] = (K, A, "thigh" + L_)
    LEG["foot" + L_] = (A, Vector((x, -0.30, 0.09)), "shin" + L_)


# ---------------------------------------------------------------- cuisson + fusion
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
baked = []
for ob, weight in PARTS:
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(ob.matrix_world)
    nob = bpy.data.objects.new(ob.name + "_baked", me)
    scene.collection.objects.link(nob)
    if callable(weight):
        groups = {}
        for v in me.vertices:
            for bname, wv in weight(v.co).items():
                if wv > 1e-4:
                    if bname not in groups:
                        groups[bname] = nob.vertex_groups.new(name=bname)
                    groups[bname].add([v.index], wv, "REPLACE")
    else:
        vg = nob.vertex_groups.new(name=weight)
        vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    baked.append(nob)

for ob in list(COL.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.collections.remove(COL)
for c in list(bpy.data.curves):
    bpy.data.curves.remove(c)

bpy.ops.object.select_all(action="DESELECT")
for ob in baked:
    ob.select_set(True)
bpy.context.view_layer.objects.active = baked[0]
bpy.ops.object.join()
robot = bpy.context.active_object
robot.name = robot.data.name = "ATOL_Robot"

# ---------------------------------------------------------------- rig
arm_data = bpy.data.armatures.new("ATOL_Rig")
arm_data.display_type = "OCTAHEDRAL"
rig = bpy.data.objects.new("ATOL_Rig", arm_data)
scene.collection.objects.link(rig)
rig.show_in_front = True
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")

BACK, UP = Vector((0, 1, 0)), Vector((0, 0, 1))
BONES = {
    "root": ((0, 0, 0), (0, 0.35, 0), None, UP),
    "hips": ((0, 0, Z_HIPS), (0, 0, Z_SPINE), "root", BACK),
    "spine": ((0, 0, Z_SPINE), (0, 0, Z_CHEST), "hips", BACK),
    "chest": ((0, 0, Z_CHEST), (0, 0, Z_NECK), "spine", BACK),
    "neck": ((0, 0, Z_NECK), (0, 0, Z_HEAD), "chest", BACK),
    "head": ((0, 0, Z_HEAD), (0, 0, 2.2), "neck", BACK),
}
for side, (e, n) in EYES.items():
    BONES[f"eye.{side}"] = (e, e + n * 0.12, "head", UP)
m0 = surf(0, MOUTH_Z, 0.003)
BONES["mouth"] = (m0, m0 + surf_normal(m0) * 0.1, "head", UP)
for name, (h, t, parent) in {**ARM, **LEG}.items():
    BONES[name] = (h, t, parent, UP if name.startswith("foot") else BACK)

for name, (h, t, parent, roll_axis) in BONES.items():
    eb = arm_data.edit_bones.new(name)
    eb.head, eb.tail = Vector(h), Vector(t)
    eb.align_roll(roll_axis)
for name, (h, t, parent, _) in BONES.items():
    if parent:
        eb = arm_data.edit_bones[name]
        eb.parent = arm_data.edit_bones[parent]
        eb.use_connect = (eb.head - eb.parent.tail).length < 1e-4
for name in ("root", "mouth", "eye.L", "eye.R"):
    arm_data.edit_bones[name].use_deform = name != "root"
bpy.ops.object.mode_set(mode="OBJECT")

robot.parent = rig
mod = robot.modifiers.new("Armature", "ARMATURE")
mod.object = rig

# ---------------------------------------------------------------- animations de démo
ORDER = [b.name for b in rig.data.bones]  # parents avant enfants (ordre de création)
REST = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}


def aim(d0, n0, d1, n1):
    """Rotation monde envoyant la direction d0 sur d1, en tournant n0 au plus près de n1."""
    d0, d1 = d0.normalized(), d1.normalized()
    q1 = d0.rotation_difference(d1)
    n = q1 @ n0
    t = (n1 - d1 * n1.dot(d1)).normalized()
    ang = math.atan2(d1.dot(n.cross(t)), n.dot(t))
    return Quaternion(d1, ang) @ q1


def key_pose(frame, rots, loc=None, scales=None, prev={}):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    for name in ORDER:
        pb = rig.pose.bones[name]
        if name in rots or (name == "hips" and loc):
            q = rots.get(name)
            if q is None:
                q = pb.matrix.to_quaternion() @ REST[name].to_quaternion().inverted()
            head = pb.head.copy() + (loc if name == "hips" and loc else Vector())
            pb.matrix = Matrix.Translation(head) @ (q.to_matrix() @ REST[name]).to_4x4()
            bpy.context.view_layer.update()
    for name, sc in (scales or {}).items():
        rig.pose.bones[name].scale = sc
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion.copy()
        if pb.name in prev and prev[pb.name].dot(q) < 0:
            q.negate()
            pb.rotation_quaternion = q
        prev[pb.name] = q
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("location", frame=frame)
        pb.keyframe_insert("scale", frame=frame)


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


rig.animation_data_create()
I = Quaternion()
FWD = Vector((0, -1, 0))
d_rest = Vector((math.sin(THETA), 0, -math.cos(THETA)))
n_rest = Vector((-math.cos(THETA), 0, -math.sin(THETA)))  # paume vers le corps (bras gauche)

# "Hello" : lève le bras gauche et fait coucou, comme sur l'image de référence
hello = bpy.data.actions.new("Hello")
hello.use_fake_user = True
rig.animation_data.action = hello
q_up = aim(d_rest, n_rest, Vector((0.95, -0.2, 0.05)), FWD)
q_fore = aim(d_rest, n_rest, Vector((0.35, -0.25, 1.0)), FWD)
for f in range(1, 73, 2):
    w = smooth((f - 1) / 12) * (1 - smooth((f - 60) / 12))
    ph = math.sin((f - 13) / 48 * 2 * math.pi * 3) * w
    hand_q = Quaternion(FWD, 0.38 * ph) @ q_fore
    rots = {
        "upper_arm.L": I.slerp(q_up, w),
        "forearm.L": I.slerp(Quaternion(FWD, 0.12 * ph) @ q_fore, w),
        "hand.L": I.slerp(hand_q, w),
        "head": Quaternion(FWD, -0.10 * w + 0.03 * ph) @ Quaternion(Vector((1, 0, 0)), 0.05 * w),
        "chest": Quaternion(FWD, -0.04 * w),
    }
    key_pose(f, rots, scales={"mouth": Vector((1 + 0.08 * w, 1, 1 + 0.15 * w))})

# "Idle" : respiration, léger balancement, clignement des yeux
idle = bpy.data.actions.new("Idle")
idle.use_fake_user = True
rig.animation_data.action = idle
for f in range(1, 50, 2):
    t = (f - 1) / 48 * 2 * math.pi
    blink = 1.0 if not 30 <= f <= 36 else max(0.08, abs(f - 33) / 3)
    rots = {
        "chest": Quaternion(Vector((1, 0, 0)), 0.02 * math.sin(t)),
        "head": Quaternion(FWD, 0.05 * math.sin(t)) @ Quaternion(Vector((1, 0, 0)), 0.03 * math.cos(t)),
        "upper_arm.L": Quaternion(Vector((0, 1, 0)), -0.04 * math.sin(t)),
        "upper_arm.R": Quaternion(Vector((0, 1, 0)), 0.04 * math.sin(t)),
    }
    key_pose(f, rots, loc=Vector((0, 0, 0.008 * math.sin(2 * t))),
             scales={"eye.L": Vector((1, 1, blink)), "eye.R": Vector((1, 1, blink))})

for act in (hello, idle):
    tr = rig.animation_data.nla_tracks.new()
    tr.name = act.name
    tr.strips.new(act.name, 1, act)
    tr.mute = True
rig.animation_data.action = hello
scene.frame_start, scene.frame_end = 1, 72
scene.render.fps = 24

# ---------------------------------------------------------------- export
bpy.ops.object.select_all(action="DESELECT")
blend = os.path.join(HERE, "robot_atol.blend")
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "robot_atol.glb"), export_format="GLB",
                          export_animations=True, export_animation_mode="ACTIONS", export_yup=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(HERE, "robot_atol.fbx"), add_leaf_bones=False, bake_anim=True,
                         bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, path_mode="COPY",
                         embed_textures=True)
bpy.ops.wm.open_mainfile(filepath=blend)
print("TRIS", sum(len(p.vertices) - 2 for p in bpy.data.objects["ATOL_Robot"].data.polygons))
print("BUILD OK")
