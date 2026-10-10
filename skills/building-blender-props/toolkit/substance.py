"""Lado Blender del texturizado en Substance 3D Painter.

Painter hace las capas; Blender le da lo que Painter no puede sacar solo de una low poly de un
objeto y un material:

    exportar_hp(nombre)            FBX del high poly con los mismos ejes y escala que el de la low
    clases(nombre, lp, ...)        mapa de clases de material (ID) horneado desde los materiales del HP
    normal_hp(nombre, lp, ...)     normal con el relieve de MATERIAL del high poly (Painter solo hornea geometria)
    campos(nombre, lp, eje, ...)   mapas en espacio de objeto: laminas, rayado a lo largo y a lo ancho,
                                   manchas grandes. No dependen de las UV: no dejan costura.
    eje_principal(nombres)         direccion larga de unas piezas (para orientar laminas y rayado)

Nada de esto guarda el .blend ni deja objetos, materiales o imagenes en la escena.
Las mascaras se parten fuera de Blender, con `sp_mascaras.py` (necesita OpenCV).
"""
import json
import os

import bpy
import numpy as np
from mathutils import Vector

import prop

HP, LP = "Model Collection", "LP Collection"

# 26 colores con cada canal en 0, 0.5 o 1 (sin el negro, que es "sin dato")
PALETA = [(r / 2, g / 2, b / 2) for r in (2, 0, 1) for g in (0, 2, 1) for b in (0, 2, 1) if (r, g, b) != (0, 0, 0)]


def _hp(con_rotulos=True):
    c = bpy.data.collections[HP]
    return [o for o in (c.all_objects if con_rotulos else c.objects) if o.type == "MESH"]


def exportar_hp(nombre):
    """FBX del high poly (sin rotulos) junto al de la low, con los ajustes de `exportar.fbx_glb`."""
    R = prop.rutas(nombre)
    objs = _hp(con_rotulos=False)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_viewport = False
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    ruta = os.path.join(R["exportados"], nombre + "_HP.fbx")
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="EDGE", use_tspace=False,
                             use_mesh_modifiers=True, path_mode="RELATIVE", embed_textures=False,
                             bake_anim=False, axis_forward="-Z", axis_up="Y")
    for o in objs:
        o.select_set(False)
    return {"ruta": ruta, "mb": round(os.path.getsize(ruta) / 1e6, 1), "piezas": len(objs)}


def eje_principal(nombres):
    """Direccion de mayor extension de las piezas (PCA de sus vertices en mundo) y su centro."""
    pts = []
    for n in nombres:
        o = bpy.data.objects[n]
        v = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get("co", v)
        v = v.reshape(-1, 3)[:: max(1, len(o.data.vertices) // 20000)]
        m = np.array(o.matrix_world)
        pts.append(v @ m[:3, :3].T + m[:3, 3])
    p = np.concatenate(pts)
    c = p.mean(0)
    _, _, vt = np.linalg.svd(p - c, full_matrices=False)
    return {"eje": [float(x) for x in vt[0]], "centro": [float(x) for x in c]}


class _Horno:
    """Prepara un horneado EMIT a una imagen nueva sobre la low poly y lo deshace todo al salir."""

    def __init__(self, lp, res, propio, flotante=False):
        self.lp, self.res, self.propio, self.flotante = bpy.data.objects[lp], res, propio, flotante

    def __enter__(self):
        sc = bpy.context.scene
        self.sc = sc
        self.prev = (sc.render.engine, sc.cycles.samples)
        bk = sc.render.bake
        self.bk = (bk.use_selected_to_active, bk.cage_extrusion, bk.max_ray_distance, bk.margin, bk.use_clear)
        self.vis = [(o, o.hide_render) for o in sc.objects]
        self.mats = list(self.lp.data.materials)
        self.img = bpy.data.images.new("_sp_horno", self.res, self.res, alpha=False, float_buffer=self.flotante)
        self.img.colorspace_settings.name = "Non-Color"
        self.tmp = bpy.data.materials.new("_sp_destino")
        self.tmp.use_nodes = True
        nt = self.tmp.node_tree
        nd = nt.nodes.new("ShaderNodeTexImage")
        nd.image = self.img
        nt.nodes.active = nd
        self.nt = nt
        for i in range(len(self.lp.data.materials)):
            self.lp.data.materials[i] = self.tmp
        sc.render.engine = "CYCLES"
        return self

    def hornear(self, fuente=None, extrusion=0.002, muestras=1, margen=24, tipo="EMIT"):
        sc, bk = self.sc, self.sc.render.bake
        for o, _ in self.vis:
            o.hide_render = True
        self.lp.hide_render = False
        self.lp.hide_viewport = False
        self.lp.hide_set(False)
        bpy.ops.object.select_all(action="DESELECT")
        if fuente is not None:
            fuente.hide_render = False
            fuente.select_set(True)
        self.lp.select_set(True)
        bpy.context.view_layer.objects.active = self.lp
        sc.cycles.samples = muestras
        bk.use_selected_to_active = fuente is not None
        bk.cage_extrusion, bk.max_ray_distance, bk.margin, bk.use_clear = extrusion, 0.0, margen, True
        if tipo == "NORMAL":
            bk.normal_space, bk.normal_r, bk.normal_g, bk.normal_b = "TANGENT", "POS_X", "POS_Y", "POS_Z"
        return list(bpy.ops.object.bake(type=tipo))

    def guardar(self, ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        if self.flotante:                       # PNG de 16 bits: save_render respeta la profundidad de la escena
            s = self.sc.render.image_settings
            prev = (s.file_format, s.color_mode, s.color_depth, self.sc.view_settings.view_transform)
            s.file_format, s.color_mode, s.color_depth = "PNG", "RGB", "16"
            self.sc.view_settings.view_transform = "Raw"
            try:
                self.img.save_render(ruta, scene=self.sc)
            finally:
                s.file_format, s.color_mode, s.color_depth, self.sc.view_settings.view_transform = prev
            return ruta
        self.img.filepath_raw, self.img.file_format = ruta, "PNG"
        self.img.save()
        return ruta

    def __exit__(self, *a):
        sc, bk = self.sc, self.sc.render.bake
        for i, m in enumerate(self.mats):
            self.lp.data.materials[i] = m
        bpy.data.materials.remove(self.tmp)
        bpy.data.images.remove(self.img)
        for o, h in self.vis:
            try:
                o.hide_render = h
            except ReferenceError:
                pass
        sc.render.engine, sc.cycles.samples = self.prev
        bk.use_selected_to_active, bk.cage_extrusion, bk.max_ray_distance, bk.margin, bk.use_clear = self.bk


def _emision(nombre, rgb):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*rgb, 1)
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m


def clases(nombre, lp, extrusion=0.002, res=4096, por_objeto=None):
    """Mapa de clases: cada material del high poly (rotulos incluidos) es una clase; `por_objeto`
    = {objeto: clase} saca una pieza entera a una clase propia aunque comparta material (letras
    en relieve del mismo cuero que el panel). Escribe Texturas/Bakes/ID_clases.png y su .json."""
    R = prop.rutas(nombre)
    por_objeto = por_objeto or {}
    sc = bpy.context.scene
    nombres, cop = [], []
    for o in _hp():
        c = o.copy()
        c.data = o.data.copy()
        sc.collection.objects.link(c)
        c.hide_viewport = False
        c.hide_set(False)
        cop.append(c)
        for i, m in enumerate(c.data.materials):
            cl = por_objeto.get(o.name) or (m.name[2:] if m and m.name.startswith("M_") else (m.name if m else "Sin_Material"))
            if cl not in nombres:
                nombres.append(cl)
            c.data.materials[i] = bpy.data.materials.get("_ID_" + cl) or _emision("_ID_" + cl, PALETA[nombres.index(cl)])
    if len(nombres) > len(PALETA):
        raise ValueError("mas clases que colores: %d" % len(nombres))
    bpy.ops.object.select_all(action="DESELECT")
    for c in cop:
        c.select_set(True)
    bpy.context.view_layer.objects.active = cop[0]
    bpy.ops.object.join()
    hp = bpy.context.view_layer.objects.active
    ruta = os.path.join(R["texturas_bakes"], "ID_clases.png")
    try:
        with _Horno(lp, res, False) as h:
            r = h.hornear(hp, extrusion)
            h.guardar(ruta)
    finally:
        me = hp.data
        bpy.data.objects.remove(hp, do_unlink=True)
        bpy.data.meshes.remove(me)
        for n in nombres:
            m = bpy.data.materials.get("_ID_" + n)
            if m:
                bpy.data.materials.remove(m)
    pal = {n: PALETA[i] for i, n in enumerate(nombres)}
    with open(ruta[:-4] + ".json", "w", encoding="utf8") as fh:
        json.dump(pal, fh, indent=1)
    return {"bake": r, "ruta": ruta, "clases": nombres}


def normal_hp(nombre, lp, extrusion=0.002, res=4096, sin_grano=()):
    """Normal tangente (OpenGL, 16 bits) horneada en Blender desde el high poly CON sus materiales, a
    Texturas/Bakes/NORMAL_blender.png. Hace falta cuando el relieve fino del high poly no es geometria sino
    relieve de material (`M.relieve`: surcos, moleteado, tejido, dibujo de una cantonera): el horneado de Painter
    solo ve geometria y lo pierde entero. Se le da despues a Painter como mesh map `Normal` (`sp.py normal`).
    `sin_grano` = materiales cuyo mapa de normales de TEXTURA se apaga durante el horneado (queda su relieve labrado):
    la veta escaneada del high poly iba en diagonal por la culata y, horneada, peleaba con la veta de Painter."""
    R = prop.rutas(nombre)
    sc = bpy.context.scene
    apagados = []
    for mn in sin_grano:
        for nd in bpy.data.materials[mn].node_tree.nodes:
            if nd.type == "NORMAL_MAP":
                apagados.append((nd, nd.inputs["Strength"].default_value))
                nd.inputs["Strength"].default_value = 0.0
    cop = []
    for o in _hp(con_rotulos=False):
        c = o.copy()
        c.data = o.data.copy()
        sc.collection.objects.link(c)
        c.hide_viewport = False
        c.hide_set(False)
        cop.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in cop:
        c.select_set(True)
    bpy.context.view_layer.objects.active = cop[0]
    bpy.ops.object.join()
    hp = bpy.context.view_layer.objects.active
    ruta = os.path.join(R["texturas_bakes"], "NORMAL_blender.png")
    try:
        with _Horno(lp, res, False, flotante=True) as h:
            r = h.hornear(hp, extrusion, muestras=8, margen=16, tipo="NORMAL")
            h.guardar(ruta)
    finally:
        for nd, v in apagados:
            nd.inputs["Strength"].default_value = v
        me = hp.data
        bpy.data.objects.remove(hp, do_unlink=True)
        bpy.data.meshes.remove(me)
    return {"bake": r, "ruta": ruta, "kb": os.path.getsize(ruta) // 1024}


def _nodos_campos(nt, eje, centro, paso, largo, ancho):
    """R = rayado a lo largo del eje, G = rayado a lo ancho, B = manchas grandes; y en una segunda
    salida, laminas: R = linea de junta, G = tono aleatorio por lamina."""
    N, L = nt.nodes, nt.links
    e = Vector(eje).normalized()
    u = e.cross(Vector((0, 0, 1)))
    u = (u if u.length > 1e-4 else e.cross(Vector((0, 1, 0)))).normalized()
    v = e.cross(u).normalized()
    geo = N.new("ShaderNodeNewGeometry")
    rel = N.new("ShaderNodeVectorMath")
    rel.operation = "SUBTRACT"
    L.new(geo.outputs["Position"], rel.inputs[0])
    rel.inputs[1].default_value = centro
    comp = N.new("ShaderNodeCombineXYZ")
    for i, ax in enumerate((e, u, v)):
        d = N.new("ShaderNodeVectorMath")
        d.operation = "DOT_PRODUCT"
        L.new(rel.outputs[0], d.inputs[0])
        d.inputs[1].default_value = ax
        L.new(d.outputs["Value"], comp.inputs[i])

    def ruido(escala, detalle=6.0, rug=0.6):
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = escala
        L.new(comp.outputs[0], mp.inputs["Vector"])
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 1.0
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rug
        L.new(mp.outputs[0], n.inputs["Vector"])
        return n.outputs["Fac"] if "Fac" in n.outputs else n.outputs[0]

    a_lo_largo = ruido((1.0 / largo, 1.0 / ancho, 1.0 / ancho))
    a_lo_ancho = ruido((1.0 / ancho, 1.0 / largo, 1.0 / ancho))
    manchas = ruido((1.0 / (largo * 0.6),) * 3, 3.0, 0.5)
    rgb = N.new("ShaderNodeCombineColor")
    for i, s in enumerate((a_lo_largo, a_lo_ancho, manchas)):
        L.new(s, rgb.inputs[i])
    # laminas
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(comp.outputs[0], sep.inputs[0])
    t = N.new("ShaderNodeMath")
    t.operation = "DIVIDE"
    L.new(sep.outputs[0], t.inputs[0])
    t.inputs[1].default_value = paso
    fr = N.new("ShaderNodeMath")
    fr.operation = "FRACT"
    L.new(t.outputs[0], fr.inputs[0])
    tri = N.new("ShaderNodeMath")          # 0 en la junta, 1 en el centro de la lamina
    tri.operation = "PINGPONG"
    L.new(fr.outputs[0], tri.inputs[0])
    tri.inputs[1].default_value = 0.5
    junta = N.new("ShaderNodeMapRange")
    junta.inputs["From Min"].default_value, junta.inputs["From Max"].default_value = 0.0, 0.09
    junta.inputs["To Min"].default_value, junta.inputs["To Max"].default_value = 1.0, 0.0
    L.new(tri.outputs[0], junta.inputs["Value"])
    fl = N.new("ShaderNodeMath")
    fl.operation = "FLOOR"
    L.new(t.outputs[0], fl.inputs[0])
    wn = N.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "1D"
    L.new(fl.outputs[0], wn.inputs["W"])
    lam = N.new("ShaderNodeCombineColor")
    L.new(junta.outputs[0], lam.inputs[0])
    L.new(wn.outputs["Value"], lam.inputs[1])
    return rgb.outputs[0], lam.outputs[0]


def campos(nombre, lp, eje, centro, paso=0.0016, largo=0.05, ancho=0.0006, res=4096, sufijo=""):
    """Mapas en espacio de objeto, horneados desde la propia low poly (no hacen falta rayos al HP).
    `paso` = grueso de lamina; `largo`/`ancho` = tamano del grano del rayado a lo largo y a traves.
    Escribe Texturas/Bakes/CAMPO_rayado.png (R largo, G ancho, B manchas) y CAMPO_laminas.png.
    `sufijo` permite un segundo juego a otra escala (veta ancha de madera ademas del rayado fino):
    CAMPO_rayado<sufijo>.png, que `sp_mascaras.py` parte como CP_*<sufijo>.png."""
    R = prop.rutas(nombre)
    out = {}
    with _Horno(lp, res, True) as h:
        nt = h.nt
        em = nt.nodes.new("ShaderNodeEmission")
        sal = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(em.outputs[0], sal.inputs[0])
        rayado, laminas = _nodos_campos(nt, eje, centro, paso, largo, ancho)
        dest = nt.nodes.active
        for clave, s in (("rayado", rayado), ("laminas", laminas)):
            nt.links.new(s, em.inputs[0])
            nt.nodes.active = dest
            out[clave] = {"bake": h.hornear(None, muestras=8, margen=24),
                          "ruta": h.guardar(os.path.join(R["texturas_bakes"], "CAMPO_%s%s.png" % (clave, sufijo)))}
    return out


def zonas(nombre, lp, zonas, res=4096):
    """Mascaras de ZONA DE USO, horneadas desde la propia low poly: `zonas` = {clave: [((x, y, z), radio_m), ...]}.
    Cada zona vale 1 en el centro de sus esferas y cae suave a 0 en su radio. Es lo que ningun generador de Painter
    sabe: donde agarra la mano, donde apoya la mejilla, donde sale el fogonazo, donde roza el arma al dejarla.
    Escribe Texturas/Bakes/ZONA_<clave>.png; `sp_mascaras.py` las deja como Mascaras/ZN_<clave>.png."""
    R = prop.rutas(nombre)
    out = {}
    with _Horno(lp, res, True) as h:
        nt = h.nt
        N, L = nt.nodes, nt.links
        dest = N.active
        em = N.new("ShaderNodeEmission")
        sal = next(n for n in N if n.type == "OUTPUT_MATERIAL")
        L.new(em.outputs[0], sal.inputs[0])
        geo = N.new("ShaderNodeNewGeometry")
        for clave, esferas in zonas.items():
            acum = None
            for c, r in esferas:
                d = N.new("ShaderNodeVectorMath")
                d.operation = "DISTANCE"
                L.new(geo.outputs["Position"], d.inputs[0])
                d.inputs[1].default_value = c
                mr = N.new("ShaderNodeMapRange")
                mr.interpolation_type = "SMOOTHSTEP"
                mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, r
                mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
                L.new(d.outputs["Value"], mr.inputs["Value"])
                if acum is None:
                    acum = mr.outputs[0]
                else:
                    mx = N.new("ShaderNodeMath")
                    mx.operation = "MAXIMUM"
                    L.new(acum, mx.inputs[0])
                    L.new(mr.outputs[0], mx.inputs[1])
                    acum = mx.outputs[0]
            L.new(acum, em.inputs[0])
            N.active = dest
            out[clave] = {"bake": h.hornear(None, muestras=1, margen=24),
                          "ruta": h.guardar(os.path.join(R["texturas_bakes"], "ZONA_%s.png" % clave))}
    return out


def posicion(nombre, lp, res=4096):
    """Posicion de cada texel en espacio de objeto, horneada desde la propia low poly: R, G, B = x, y, z normalizados
    a la caja de la malla. Escribe Texturas/Bakes/POSICION.png (16 bits) y POSICION.json con la caja en metros. Con
    ella un script fuera de Blender puede sacar mascaras EXACTAS de cualquier forma definida en coordenadas del
    modelo (un panel de picado dibujado como curva), con distancias en milimetros reales y no en pixeles de UV."""
    R = prop.rutas(nombre)
    ob = bpy.data.objects[lp]
    co = np.empty(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lo, hi = co.min(0) - 1e-4, co.max(0) + 1e-4
    ruta = os.path.join(R["texturas_bakes"], "POSICION.png")
    with _Horno(lp, res, True, flotante=True) as h:
        nt = h.nt
        N, L = nt.nodes, nt.links
        dest = N.active
        em = N.new("ShaderNodeEmission")
        sal = next(n for n in N if n.type == "OUTPUT_MATERIAL")
        L.new(em.outputs[0], sal.inputs[0])
        geo = N.new("ShaderNodeNewGeometry")
        mp = N.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        mp.inputs["Location"].default_value = tuple(float(-lo[i] / (hi[i] - lo[i])) for i in range(3))
        mp.inputs["Scale"].default_value = tuple(float(1.0 / (hi[i] - lo[i])) for i in range(3))
        L.new(geo.outputs["Position"], mp.inputs["Vector"])
        L.new(mp.outputs[0], em.inputs[0])
        N.active = dest
        r = h.hornear(None, muestras=1, margen=24)
        h.guardar(ruta)
    with open(ruta[:-4] + ".json", "w", encoding="utf8") as fh:
        json.dump({"min": [float(x) for x in lo], "max": [float(x) for x in hi]}, fh)
    return {"bake": r, "ruta": ruta}
