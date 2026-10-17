"""Tramo comun «del constructor a las mascaras de Painter» de un prop de varios sets, parametrizado por un `cfg`.

Sale de los `preparar_sp.py` de la tanda de laboratorio y de la katana: lo que alli era copia de prop en prop.
El `preparar_sp.py` de cada prop queda en su configuracion:

    import prep
    class CFG:
        N = "Mi_Prop"                      # carpeta del prop
        H, LPm = construir_hp, construir_lp
        LETRA = {"Cuerpo": "C", ...}       # set -> prefijo de sus mascaras
        PISO = 2.5                         # px/mm
        EXTRUSION = 0.002                  # jaula de los horneados de Blender (m)
        HERO = (0.4, -1.0, 0.3)
        METODO = {"Cuerpo": "MINIMUM_STRETCH", ...}
        DESPIECE = {"Cuerpo": (0, 0, 0), ...}      # desplazamiento de cada set al exportar para Painter
        TRENZA = ("Cuerpo",)               # sets con cintas trenzadas (opcional)
        @staticmethod
        def zonas(): ...                   # dict para substance.por_set
        @staticmethod
        def arte(): ...                    # [dict(set, piezas, img, u, v, sale, dato)]
        @staticmethod
        def independientes(): ...          # comprobaciones propias del prop (opcional)
    def todo(**k): return prep.todo(CFG, **k)

`todo` escribe <prop>/_prep.json paso a paso: la llamada pasa a segundo plano.
"""
import json
import os
import time
import traceback

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import entrega
import estudio
import prop
import puertas
import quads as Q
import substance
import tanda
import uv
import verifications as V

HP, LP = "Model Collection", "LP Collection"
MM = 0.001


def _solo_set(base, s):
    o = base.copy()
    o.data = base.data.copy()
    o.name = o.data.name = "_LP_solo_" + s
    bpy.data.collections[LP].objects.link(o)
    k = [m.name for m in o.data.materials].index("LP_" + s)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != k], context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    return o


def _material_arte(a, img):
    m = bpy.data.materials.new("_ARTE")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc, sx = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sx.inputs[0])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    for (eje, c0, c1), sal in ((a["u"], "X"), (a["v"], "Y")):
        r = nt.nodes.new("ShaderNodeMapRange")
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = c0 * MM, c1 * MM
        nt.links.new(sx.outputs[eje], r.inputs["Value"])
        nt.links.new(r.outputs[0], cb.inputs[sal])
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image, ti.extension = img, "EXTEND"
    nt.links.new(cb.outputs[0], ti.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    color = ti.outputs["Color"]
    if a.get("mira"):
        # Solo las caras que miran hacia `mira`: una proyeccion plana atraviesa la pieza y deja el rotulo ESPEJADO en
        # su otra cara (el brazo de un visor: la marca se leia del reves por dentro).
        geo, dot = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = tuple(a["mira"])
        nt.links.new(geo.outputs["Normal"], dot.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.3
        nt.links.new(dot.outputs["Value"], gt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMixRGB")
        mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = 1.0
        nt.links.new(color, mx.inputs[1])
        nt.links.new(gt.outputs[0], mx.inputs[2])
        color = mx.outputs[0]
    nt.links.new(color, em.inputs[0])
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m


def arte(cfg):
    """Hornea cada imagen de `cfg.arte()` (dibujada en milimetros del MUNDO, proyeccion plana) desde sus piezas del
    high poly al espacio UV de su set: Texturas/Bakes/<sale>.png. `dato`: mascara, sin gestion de color; si no, sRGB.
    `tapan`: piezas que solo ocultan (hornean en negro): hacen falta, porque el rayo de una pieza LEJANA de la low
    poly tambien acaba dando en la pieza rotulada (la marca del brazo derecho de un visor salio en el izquierdo).
    `mira` = (x, y, z): solo las caras que miran hacia ahi."""
    R = prop.rutas(cfg.N)
    base = bpy.data.objects[cfg.LPm.NOMBRE]
    hechos = {}
    for a in cfg.arte():
        o = _solo_set(base, a["set"])
        img = bpy.data.images.load(os.path.join(R["texturas"], "Fuente", a["img"]))
        if a.get("dato"):
            img.colorspace_settings.name = "Non-Color"
        mt = _material_arte(a, img)
        ng = bpy.data.materials.new("_NEGRO")
        ng.use_nodes = True
        ng.node_tree.nodes.clear()
        em = ng.node_tree.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (0, 0, 0, 1)
        ng.node_tree.links.new(em.outputs[0], ng.node_tree.nodes.new("ShaderNodeOutputMaterial").inputs[0])
        cop = []
        for nombres, mat in ((a["piezas"], mt), (a.get("tapan", ()), ng)):
            for nm in nombres:
                src = bpy.data.objects[nm]
                c = src.copy()
                c.data = src.data.copy()
                bpy.context.scene.collection.objects.link(c)
                c.hide_viewport = False
                c.hide_set(False)
                c.data.materials.clear()
                c.data.materials.append(mat)
                cop.append(c)
        bpy.ops.object.select_all(action="DESELECT")
        for c in cop:
            c.select_set(True)
        bpy.context.view_layer.objects.active = cop[0]
        if len(cop) > 1:
            bpy.ops.object.join()
        hpj = bpy.context.view_layer.objects.active
        final = os.path.join(R["texturas_bakes"], a["sale"] + ".png")
        lineal = final[:-4] + "_lineal.png"
        try:
            with substance._Horno(o.name, 4096, False) as h:
                h.hornear(hpj, a.get("extrusion", cfg.EXTRUSION), muestras=4)
                h.guardar(final if a.get("dato") else lineal)
        finally:
            for ob in (hpj, o):
                d = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.meshes.remove(d)
            bpy.data.materials.remove(mt)
            bpy.data.materials.remove(ng)
            bpy.data.images.remove(img)
        im = bpy.data.images.load(final if a.get("dato") else lineal)
        w, h_ = im.size
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h_, w, 4)
        if not a.get("dato"):                                     # el horno escribe valores lineales: se pasan a sRGB
            rgb = px[..., :3]
            px[..., :3] = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(np.maximum(rgb, 1e-6), 1 / 2.4) - 0.055)
            im.pixels.foreach_set(px.ravel())
            im.filepath_raw, im.file_format = final, "PNG"
            im.save()
        hechos[a["sale"]] = round(float((px[..., :3].max(-1) > 0.02).mean()) * 100, 2)      # % del atlas con arte
        bpy.data.images.remove(im)
        if not a.get("dato"):
            os.remove(lineal)
    return hechos


def trenza(cfg, paso=0.0022):
    """Relieve del trenzado de las cintas, horneado desde la propia low poly con su UV analitica (`analitica.cinta`):
    espigas a lo largo de la cinta, en milimetros reales, vayan como vayan las islas en el atlas.
    Texturas/Bakes/AR_<letra>_Trenza.png (gris; 0 fuera de las cintas)."""
    R = prop.rutas(cfg.N)
    base = bpy.data.objects[cfg.LPm.NOMBRE]
    out = {}
    for s in getattr(cfg, "TRENZA", ()):
        o = _solo_set(base, s)
        try:
            with substance._Horno(o.name, 4096, True) as h:
                nt = h.nt
                Nn, Ln = nt.nodes, nt.links
                dest = Nn.active
                em = Nn.new("ShaderNodeEmission")
                sal = next(n for n in Nn if n.type == "OUTPUT_MATERIAL")
                Ln.new(em.outputs[0], sal.inputs[0])
                at = Nn.new("ShaderNodeAttribute")
                at.attribute_name = "uva"
                sx = Nn.new("ShaderNodeSeparateXYZ")
                Ln.new(at.outputs["Vector"], sx.inputs[0])

                def mat(op, a, b=None):
                    n = Nn.new("ShaderNodeMath")
                    n.operation = op
                    for i, x in enumerate((a, b)):
                        if x is None:
                            continue
                        if isinstance(x, (int, float)):
                            n.inputs[i].default_value = x
                        else:
                            Ln.new(x, n.inputs[i])
                    return n.outputs[0]
                c = mat("ABSOLUTE", sx.outputs["Z"])
                fase = mat("ADD", mat("MULTIPLY", sx.outputs["X"], 1.0 / paso), mat("MULTIPLY", c, 0.9))
                onda = mat("ABSOLUTE", mat("SUBTRACT", mat("FRACT", fase), 0.5))
                esp = mat("ADD", mat("MULTIPLY", onda, 1.3), 0.3)
                surco = mat("MINIMUM", mat("MULTIPLY", c, 9.0), 1.0)
                canto = mat("MINIMUM", mat("MULTIPLY", mat("SUBTRACT", 1.0, c), 5.0), 1.0)
                val = mat("MULTIPLY", mat("MULTIPLY", esp, mat("ADD", mat("MULTIPLY", surco, 0.45), 0.55)), canto)
                Ln.new(mat("MULTIPLY", val, mat("GREATER_THAN", c, 0.0005)), em.inputs[0])
                Nn.active = dest
                h.hornear(None, muestras=1, margen=8)
                out[s] = h.guardar(os.path.join(R["texturas_bakes"], "AR_%s_Trenza.png" % cfg.LETRA[s]))
        finally:
            d = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d)
    return out


def arte_uva(cfg):
    """Arte dibujado en el ESPACIO DE PATRON de cada pieza (su UV analitica en milimetros, `analitica.placa`), horneado
    desde la propia low poly: pespuntes, cenefas repujadas y marcas caen sin deformarse sobre una hoja curvada, cosa
    que una proyeccion plana no consigue. `cfg.arte_uva()` = [dict(set, sale, capas=[dict(ident, img, u=(mm0, mm1),
    v=(mm0, mm1))])]: cada capa pinta solo los texeles cuya pieza es `ident`. Escribe Texturas/Bakes/<sale>.png (RGB
    de datos, sin gestion de color)."""
    R = prop.rutas(cfg.N)
    base = bpy.data.objects[cfg.LPm.NOMBRE]
    out = {}
    for a in cfg.arte_uva():
        o = _solo_set(base, a["set"])
        imgs = []
        try:
            with substance._Horno(o.name, 4096, True) as h:
                nt = h.nt
                Nn, Ln = nt.nodes, nt.links
                dest = Nn.active
                em = Nn.new("ShaderNodeEmission")
                sal = next(n for n in Nn if n.type == "OUTPUT_MATERIAL")
                Ln.new(em.outputs[0], sal.inputs[0])
                at = Nn.new("ShaderNodeAttribute")
                at.attribute_name = "uva"
                sx = Nn.new("ShaderNodeSeparateXYZ")
                Ln.new(at.outputs["Vector"], sx.inputs[0])
                acum = None
                for c in a["capas"]:
                    img = bpy.data.images.load(os.path.join(R["texturas"], "Fuente", c["img"]))
                    img.colorspace_settings.name = "Non-Color"
                    imgs.append(img)
                    cb = Nn.new("ShaderNodeCombineXYZ")
                    for (c0, c1), ent, sal_ in ((c["u"], "X", "X"), (c["v"], "Y", "Y")):
                        r = Nn.new("ShaderNodeMapRange")
                        r.clamp = False
                        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = c0 * MM, c1 * MM
                        Ln.new(sx.outputs[ent], r.inputs["Value"])
                        Ln.new(r.outputs[0], cb.inputs[sal_])
                    ti = Nn.new("ShaderNodeTexImage")
                    ti.image, ti.extension = img, "CLIP"
                    Ln.new(cb.outputs[0], ti.inputs["Vector"])
                    d = Nn.new("ShaderNodeMath")
                    d.operation = "COMPARE"
                    Ln.new(sx.outputs["Z"], d.inputs[0])
                    d.inputs[1].default_value, d.inputs[2].default_value = float(c["ident"]), 0.4
                    mx = Nn.new("ShaderNodeMixRGB")
                    mx.blend_type = "MULTIPLY"
                    mx.inputs[0].default_value = 1.0
                    Ln.new(ti.outputs["Color"], mx.inputs[1])
                    Ln.new(d.outputs[0], mx.inputs[2])
                    if acum is None:
                        acum = mx.outputs[0]
                    else:
                        ad = Nn.new("ShaderNodeMixRGB")
                        ad.blend_type = "ADD"
                        ad.inputs[0].default_value = 1.0
                        Ln.new(acum, ad.inputs[1])
                        Ln.new(mx.outputs[0], ad.inputs[2])
                        acum = ad.outputs[0]
                Ln.new(acum, em.inputs[0])
                Nn.active = dest
                h.hornear(None, muestras=1, margen=8)
                out[a["sale"]] = h.guardar(os.path.join(R["texturas_bakes"], a["sale"] + ".png"))
        finally:
            d_ = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d_)
            for img in imgs:
                bpy.data.images.remove(img)
    return out


def uv_analitica(nombre, margen=0.003):
    """Copia a la capa UV la UV analitica (`uva`) de las caras `cosida` y vuelve a igualar escalas y empaquetar."""
    o = bpy.data.objects[nombre]
    me = o.data
    at, car = me.attributes.get("uva"), me.attributes.get("cosida")
    if not at or not car:
        return 0
    uvl = me.uv_layers.active
    ad = me.attributes.get("uvd")           # desarrollo sobre la malla, para hojas con paredes (`analitica.placa(desarrollo=True)`)
    n = 0
    for pl in me.polygons:
        if car.data[pl.index].value:
            for li in pl.loop_indices:
                d = ad.data[li].vector if ad else None
                uvl.data[li].uv = d[:2] if d is not None and d[2] > 0.5 else at.data[li].vector[:2]
            n += 1
    malas = [i for i, r in enumerate(anisotropia_caras(me)) if r > 1.8]       # tambien las analiticas: el canto de una hoja con paredes sale del patron plano, que lo acorta
    if malas:
        # Un canto es un anillo cerrado entre las costuras de las dos caras de la hoja: sin un corte que lo abra, el
        # despliegue lo aplasta. Se corta a traves cada pocas caras y se vuelve a abrir solo.
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        ms = set(malas)
        for f in bm.faces:
            f.select = f.index in ms
        cand = [e for e in bm.edges if len(e.link_faces) == 2 and all(f.index in ms for f in e.link_faces)]
        padre = {i: i for i in ms}

        def raiz(i):
            while padre[i] != i:
                padre[i] = padre[padre[i]]
                i = padre[i]
            return i
        for e in cand:
            padre[raiz(e.link_faces[0].index)] = raiz(e.link_faces[1].index)
        cortado = set()
        for e in cand:
            if True:                       # cada cara estirada, a su isla: con tramos de varias caras quedaban piezas dobladas sobre el canto que se pisaban
                e.seam = True
                cortado.add(raiz(e.link_faces[0].index))
        for e in cand:                     # ningun anillo se queda sin su corte
            r = raiz(e.link_faces[0].index)
            if r not in cortado:
                e.seam = True
                cortado.add(r)
        bm.select_flush(True)
        bm.to_mesh(me)
        bm.free()
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(area=area, region=region, active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.mode_set(mode="EDIT")
        if malas:                         # los cantos que el despliegue dejo estirados se vuelven a abrir por angulos
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.uv.unwrap(method="ANGLE_BASED", fill_holes=True, correct_aspect=True, margin=margen)
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin=margen, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")
    return n


def anisotropia_caras(me):
    """Por cara, el cociente entre la mayor y la menor densidad de texeles medida a lo largo de sus aristas. 1 = sin
    estirar. Caso real: el canto del casco de una silla media 62 x 12 mm y ocupaba 28 x 208 px (0,44 y 17 px/mm): su
    AREA en el atlas era la correcta, asi que ni la puerta de densidad ni la de ocupacion lo vieron, y el grano del
    cuero salio en ondas. Se vio en un render."""
    uvl = me.uv_layers.active.data
    out = []
    for pl in me.polygons:
        li = list(pl.loop_indices)
        r = []
        for k in range(len(li)):
            a, b = li[k], li[(k + 1) % len(li)]
            d3 = (me.vertices[me.loops[a].vertex_index].co - me.vertices[me.loops[b].vertex_index].co).length
            if d3 > 1e-7:
                r.append((uvl[a].uv - uvl[b].uv).length / d3)
        out.append(max(r) / max(min(r), 1e-12) if r else 1.0)
    return out


def anisotropia(objs, tope=2.5):
    """Puerta: caras con la UV estirada mas de `tope` veces en una direccion respecto de la otra."""
    out = {"ok": True}
    for n in objs:
        me = bpy.data.objects[n].data
        r = np.array(anisotropia_caras(me))
        ar = np.array([p.area for p in me.polygons])
        mal = r > tope
        out[n] = {"caras": int(mal.sum()), "area_pct": round(float(ar[mal].sum() / max(ar.sum(), 1e-12) * 100), 2), "max": round(float(r.max()), 1)}
        out["ok"] = out["ok"] and out[n]["area_pct"] < 1.0
    return out


def lejos(objs, noms, tope_mm=2.0):
    """Caras de la low poly a mas de `tope_mm` del high poly, separadas en ENTERRADAS dentro de un solido del high
    poly (no se ven) y VISTAS, que son desvio real. `Q.desvio` da el maximo, no donde esta."""
    from mathutils.bvhtree import BVHTree
    # arboles en coordenadas de mundo: FromObject las da en las del objeto, y una pieza con el origen en su pivote
    # (puerta, teclas, asa del radiocasete) salia a 38 mm de su low poly sin estarlo
    arboles = {}
    for n in noms:
        ob = bpy.data.objects[n]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        arboles[n] = BVHTree.FromBMesh(bm)
        bm.free()
    dirs = [Vector((0.577, 0.577, 0.577)), Vector((-0.31, 0.82, 0.48)), Vector((0.71, -0.2, -0.67))]

    def dentro(p):
        for t in arboles.values():
            votos = 0
            for d in dirs:
                n, o = 0, p.copy()
                while n < 64:
                    h = t.ray_cast(o, d)
                    if h[0] is None:
                        break
                    n += 1
                    o = h[0] + d * 1e-5
                votos += n % 2
            if votos == 3:
                return True
        return False
    out = {}
    for nombre in objs:
        me = bpy.data.objects[nombre].data
        vistas, enterradas = [], 0
        for f in me.polygons:
            c = f.center
            d = min(x for x in (t.find_nearest(c)[3] for t in arboles.values()) if x is not None)      # ojo: 0.0 es valido
            if d * 1000 > tope_mm:
                if dentro(c):
                    enterradas += 1
                else:
                    vistas.append((round(d * 1000, 1), [round(x * 1000) for x in c]))
        vistas.sort(reverse=True)
        out[nombre] = {"enterradas": enterradas, "vistas": len(vistas), "peores": vistas[:8]}
    return out


def fuera_jaula(objs, noms, jaula_mm=2.6):
    cop = []
    for n in objs:
        o = bpy.data.objects[n].copy()
        o.data = o.data.copy()
        bpy.data.collections[LP].objects.link(o)
        cop.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in cop:
        o.select_set(True)
    bpy.context.view_layer.objects.active = cop[0]
    if len(cop) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = "_LP_unida"
    try:
        return V.hp_outside_cage(noms, j.name, jaula_mm)["over"]
    finally:
        d = j.data
        bpy.data.objects.remove(j, do_unlink=True)
        bpy.data.meshes.remove(d)


def normales_ponderadas(nombre):
    o = bpy.data.objects[nombre]
    antes = V.lp_normal_skew(nombre)
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new("Normales_Ponderadas", "WEIGHTED_NORMAL")
    m.mode, m.weight, m.keep_sharp = "FACE_AREA", 50, True
    bpy.ops.object.modifier_apply(modifier=m.name)
    despues = V.lp_normal_skew(nombre)
    return {"antes": (antes["max_deg"], antes["over"]), "despues": (despues["max_deg"], despues["over"])}


def silueta(cfg):
    for o in [x for x in list(bpy.data.collections[HP].all_objects) if x]:
        o.hide_render = False
    estudio.guardar_base()
    sil = {}
    vistas = getattr(cfg, "SILUETA", (("hero", cfg.HERO), ("frente", (0.02, -1.0, 0.02)), ("lado", (-1.0, -0.25, 0.12))))
    for et, dv in vistas:
        cam = bpy.data.objects["CAM_Detalle"]
        cam["base_dir"] = list(Vector(dv).normalized())
        estudio.encuadrar("CAM_Detalle", HP, 0.05, (1800, 1200))
        s = V.silhouette_hp_vs_lp(HP, LP, "CAM_Detalle", res=(1800, 1200), samples=8, hide=("Backdrop_360",))
        sil[et] = (round(s["differing_px_pct"], 3), round(s["area_delta_pct"], 3))
    return sil


def _mover(cfg, signo):
    lp = bpy.data.objects[cfg.LPm.NOMBRE]
    me = lp.data
    mats = [m.name for m in me.materials]
    de = {}
    for pl in me.polygons:
        for v in pl.vertices:
            de[v] = mats[pl.material_index][3:]
    for v, s in de.items():
        me.vertices[v].co += Vector(cfg.DESPIECE.get(s, (0, 0, 0))) * signo
    me.update()
    for o in bpy.data.collections[HP].objects:
        o.location = Vector(cfg.DESPIECE.get(cfg.LPm.set_de(o.name), (0, 0, 0))) * (1 if signo > 0 else 0)
    bpy.context.view_layer.update()


def exportar(cfg, despiece):
    """FBX de la low poly y del high poly. `despiece=True`: con los sets SEPARADOS segun `cfg.DESPIECE`, para que el
    horneado de Painter no meta en cada pieza la normal y la oclusion de la que tiene apoyada encima; las UV son las
    mismas, asi que las texturas valen para el conjunto montado. `despiece=False` deja los FBX de entrega."""
    hay = despiece and any(any(v) for v in getattr(cfg, "DESPIECE", {}).values())
    if hay:
        _mover(cfg, 1)
    try:
        import exportar as EX
        R = prop.rutas(cfg.N)
        ex = EX.fbx_glb([cfg.LPm.NOMBRE], R["exportados"], cfg.N + "_LP")
        hp = substance.exportar_hp(cfg.N)
    finally:
        if hay:
            _mover(cfg, -1)
    return {"lp": ex["ok"], "hp_mb": hp["mb"], "despiece": bool(hay)}


def hornear(cfg, out=None):
    """Clases, campos, zonas, arte y trenzado."""
    out = {} if out is None else out
    r = substance.por_set(cfg.N, cfg.LPm.NOMBRE, cfg.zonas(), extrusion=cfg.EXTRUSION)
    out["clases"] = {k: r[k]["clases"] for k in r}
    out["arte"] = arte(cfg) if getattr(cfg, "arte", None) else {}
    out["trenza"] = trenza(cfg)
    if getattr(cfg, "arte_uva", None):
        out["arte_uva"] = arte_uva(cfg)
    return out


def todo(cfg, desde_lp=False, hasta_uv=False, despiece=True):
    t = time.time()
    R = prop.rutas(cfg.N)
    H, LPm = cfg.H, cfg.LPm
    out = {}

    def volcar():
        out["t"] = round(time.time() - t)
        with open(os.path.join(R["raiz"], "_prep.json"), "w", encoding="utf8") as fh:
            json.dump(out, fh, indent=1, default=str)
    try:
        if not desde_lp:
            out["hp"] = H.construir()
        noms = H.solidos()
        if not desde_lp:
            g, e = puertas.geometria(noms), puertas.ensamblaje(noms)
            out["geometria"] = {"ok": g["ok"], "fallos": str(g.get("fallos"))[:400]}
            out["cruces_no_previstos"] = H.cruces_no_previstos(e["pairs"])
            out["uniones"] = len(e["pairs"])
            out["ensamblaje"] = {k: str(v)[:200] for k, v in e.items() if k != "pairs"}
            out["invertidos"] = V.inverted_solids(HP)["inverted"]
            if getattr(cfg, "independientes", None):
                out["independientes"] = cfg.independientes()
            volcar()
        antes = puertas.huella(HP)
        lp = LPm.construir()
        out["lp"] = {"tris": lp["tris"], "sets": lp["sets"], "pendientes": lp["pendientes"], "piezas": lp["tris_por_pieza"]}
        objs = [LPm.objeto_set(s) for s in LPm.SETS]
        out["desvio"] = {s: Q.desvio(bpy.data.objects[LPm.objeto_set(s)], noms, tope=cfg.EXTRUSION * 1000) for s in LPm.SETS}
        out["lejos"] = lejos(objs, noms, tope_mm=cfg.EXTRUSION * 1000)
        out["fuera_jaula"] = fuera_jaula(objs, noms, jaula_mm=cfg.EXTRUSION * 1000 + 0.6)
        volcar()
        out["uv_info"] = {}
        for s in LPm.SETS:
            o = LPm.objeto_set(s)
            ex = cfg.costuras(s) if getattr(cfg, "costuras", None) else None
            # margen por set (cfg.MARGEN): con ~800 islas pequenas el margen por defecto se comia el atlas (30 %)
            i = uv.desplegar([o], extra=ex, metodo=cfg.METODO.get(s, "MINIMUM_STRETCH"),
                             margen=getattr(cfg, "MARGEN", {}).get(s, 0.003))
            out["uv_info"][s] = {"islas": i[o]["islas"], "no_disco": i[o]["no_disco"], "refinado": i["refinado"], "analiticas": uv_analitica(o)}
            if getattr(cfg, "tras_uv", None):        # retoque propio del prop (agrandar las islas con rotulos, por ejemplo)
                out["uv_info"][s]["tras_uv"] = cfg.tras_uv(s, o)
        out["afinidad_uv"] = {o: {k: v for k, v in V.uv_quad_affinity(o).items() if k != "evaluated"} for o in objs}
        out["anisotropia_uv"] = anisotropia(objs)
        out["uv"] = tanda.medir_uv(objs)
        out["densidad"] = puertas.piso_densidad(objs, 4096, cfg.PISO)
        volcar()
        if hasta_uv:
            return out
        out["juntar"] = LPm.juntar()
        out["normales"] = normales_ponderadas(LPm.NOMBRE)
        out["malla"] = tanda.malla(LPm.NOMBRE)
        out["censo"] = {k: v for k, v in Q.censo(bpy.data.objects[LPm.NOMBRE]).items() if k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}
        out["hp_intacto"] = puertas.huella_intacta(HP, antes)["ok"]
        out["silueta"] = silueta(cfg)
        volcar()
        ex = entrega.exportar_y_verificar(cfg.N, [LPm.NOMBRE], ["LP_" + s for s in LPm.SETS])
        out["export"] = {"tris": ex["tris"], "dims": ex["dims_mm"], "ok": ex["ida_y_vuelta"]["ok"]}
        hornear(cfg, out)
        prop.guardar(cfg.N)
        if despiece:
            out["despiece"] = exportar(cfg, True)
        out["listo"] = True
    except Exception:
        out["error"] = traceback.format_exc()[-2500:]
    volcar()
    return out
