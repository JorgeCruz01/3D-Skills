"""Del constructor a las mascaras de Painter, en una llamada: high poly, puertas, low poly, UV, exportacion,
clases / campos / zonas por set y la etiqueta impresa horneada al espacio UV de la botella.

    import preparar_sp; preparar_sp.todo()        (escribe _prep.json: la llamada puede pasar a segundo plano)
"""
import json
import math
import os
import time

import bmesh
import bpy
from mathutils import Vector

import construir_extintor as CE
import construir_hp as H
import construir_lp as LPm
import entrega
import estudio
import lowpoly as L
import prop
import puertas
import quads as Q
import substance
import tanda
import uv
import verifications as V

N = "Extintor_Polvo_6kg"
HP, LP = "Model Collection", "LP Collection"
MM = 0.001
EXTRUSION = 0.002
HERO = (0.38, -0.92, 0.27)


def zonas():
    mano = [((x * MM, 0, z * MM), 0.03) for x, z in ((30, 492), (60, 498), (95, 505), (125, 512), (40, 462), (70, 453), (100, 442), (125, 432))]
    return {"B": dict(mat="LP_Botella", eje=(0, 0, 1), centro=(0, 0, 0.2), zonas={"B_Pie": [((0, 0, 0.0), 0.115)], "B_Hombro": [((0, 0, 0.40), 0.10)]}),
            "C": dict(mat="LP_Cabezal", eje=(1, 0, 0), centro=(0, 0, 0.47), zonas={"C_Mano": mano, "C_Boquilla": [((CE.X_M * MM, 0, 0.05), 0.035)]})}


def etiqueta():
    """Hornea el arte de la etiqueta (Texturas/Fuente/Etiqueta_Print.png, mapeado cilindrico con el panel frontal en -Y)
    desde la banda del high poly al espacio UV de la botella: Texturas/Bakes/ETIQUETA.png, en sRGB."""
    R = prop.rutas(N)
    base = bpy.data.objects[LPm.NOMBRE]
    o = base.copy()
    o.data = base.data.copy()
    o.name = o.data.name = "_LP_solo_B"
    bpy.data.collections[LP].objects.link(o)
    k = [m.name for m in o.data.materials].index("LP_Botella")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != k], context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    img = bpy.data.images.load(os.path.join(R["texturas"], "Fuente", "Etiqueta_Print.png"))
    me = bpy.data.materials.new("_ETQ")
    me.use_nodes = True
    nt = me.node_tree
    nt.nodes.clear()
    tc, sx = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sx.inputs[0])
    ny = nt.nodes.new("ShaderNodeMath")
    ny.operation = "MULTIPLY"
    ny.inputs[1].default_value = -1.0
    nt.links.new(sx.outputs["Y"], ny.inputs[0])
    at = nt.nodes.new("ShaderNodeMath")
    at.operation = "ARCTAN2"                       # atan2(x, -y): 0 en el frente (-Y), crece hacia +X
    nt.links.new(sx.outputs["X"], at.inputs[0])
    nt.links.new(ny.outputs[0], at.inputs[1])
    u = nt.nodes.new("ShaderNodeMath")
    u.operation = "MULTIPLY_ADD"
    u.inputs[1].default_value, u.inputs[2].default_value = 1 / (2 * math.pi), 0.5
    nt.links.new(at.outputs[0], u.inputs[0])
    z0, z1 = CE.ETIQUETA
    v = nt.nodes.new("ShaderNodeMapRange")
    v.inputs["From Min"].default_value, v.inputs["From Max"].default_value = z0 * MM, z1 * MM
    nt.links.new(sx.outputs["Z"], v.inputs["Value"])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u.outputs[0], cb.inputs["X"])
    nt.links.new(v.outputs[0], cb.inputs["Y"])
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image, ti.extension = img, "EXTEND"
    nt.links.new(cb.outputs[0], ti.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ti.outputs["Color"], em.inputs[0])
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    negro = substance._emision("_ETQ_negro", (0, 0, 0))
    cop = []
    for nm, mt in (("Etiqueta", me), ("Botella", negro)):
        s = bpy.data.objects[nm]
        c = s.copy()
        c.data = s.data.copy()
        bpy.context.scene.collection.objects.link(c)
        c.hide_viewport = False
        c.hide_set(False)
        c.data.materials.clear()
        c.data.materials.append(mt)
        cop.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in cop:
        c.select_set(True)
    bpy.context.view_layer.objects.active = cop[0]
    bpy.ops.object.join()
    hpj = bpy.context.view_layer.objects.active
    lineal = os.path.join(R["texturas_bakes"], "ETIQUETA_lineal.png")
    try:
        with substance._Horno(o.name, 4096, False) as h:
            h.hornear(hpj, EXTRUSION, muestras=4)
            h.guardar(lineal)
    finally:
        for ob in (hpj, o):
            d = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(d)
        bpy.data.materials.remove(me)
        bpy.data.materials.remove(negro)
        bpy.data.images.remove(img)
    # el horno escribe valores lineales: se pasan a sRGB
    import numpy as np
    im = bpy.data.images.load(lineal)
    w, h_ = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h_, w, 4)
    rgb = a[..., :3]
    a[..., :3] = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(np.maximum(rgb, 1e-6), 1 / 2.4) - 0.055)
    im.pixels.foreach_set(a.ravel())
    im.filepath_raw, im.file_format = os.path.join(R["texturas_bakes"], "ETIQUETA.png"), "PNG"
    im.save()
    bpy.data.images.remove(im)
    os.remove(lineal)
    return True


def silueta():
    for o in [x for x in list(bpy.data.collections[HP].all_objects) if x]:
        o.hide_render = False
    estudio.guardar_base()
    sil = {}
    for et, dv in (("hero", HERO), ("frente", (0.02, -1.0, 0.02)), ("lado", (1.0, 0.03, 0.05))):
        cam = bpy.data.objects["CAM_Detalle"]
        cam["base_dir"] = list(Vector(dv).normalized())
        estudio.encuadrar("CAM_Detalle", HP, 0.05, (1400, 1400))
        s = V.silhouette_hp_vs_lp(HP, LP, "CAM_Detalle", res=(1400, 1400), samples=8, hide=("Backdrop_360",))
        sil[et] = (round(s["differing_px_pct"], 3), round(s["area_delta_pct"], 3))
    return sil


def todo():
    t = time.time()
    R = prop.rutas(N)
    out = {}
    H.materiales_extintor()
    out["hp"] = H.construir()
    noms = H.solidos()
    g, e = puertas.geometria(noms), puertas.ensamblaje(noms)
    out["geometria"] = {"ok": g["ok"], "fallos": str(g.get("fallos"))[:300]}
    out["cruces_no_previstos"] = H.cruces_no_previstos(e["pairs"])
    out["uniones"] = len(e["pairs"])
    out["invertidos"] = V.inverted_solids(HP)["ok"]
    antes = puertas.huella(HP)
    lp = LPm.construir(0.5)
    out["lp_pendientes"] = lp["pendientes"]
    uv.desplegar([LPm.BOTELLA])
    uv.desplegar([LPm.CABEZAL], extra=L.costura_tiras(0.11))
    m = tanda.medir_uv([LPm.BOTELLA, LPm.CABEZAL])
    out["uv"] = {k: v for k, v in m.items()}
    out["densidad"] = puertas.piso_densidad([LPm.BOTELLA, LPm.CABEZAL], 4096, 2.5)["min_px_mm"]
    out["juntar"] = LPm.juntar()
    out["malla"] = tanda.malla(LPm.NOMBRE)
    out["censo"] = {k: v for k, v in Q.censo(bpy.data.objects[LPm.NOMBRE]).items() if k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}
    out["hp_intacto"] = puertas.huella_intacta(HP, antes)["ok"]
    out["silueta"] = silueta()
    ex = entrega.exportar_y_verificar(N, [LPm.NOMBRE], ["LP_Botella", "LP_Cabezal"])
    out["export"] = {"tris": ex["tris"], "dims": ex["dims_mm"], "ok": ex["ida_y_vuelta"]["ok"]}
    out["hp_mb"] = substance.exportar_hp(N)["mb"]
    r = substance.por_set(N, LPm.NOMBRE, zonas(), extrusion=EXTRUSION)
    out["clases"] = r["B"]["clases"]
    out["etiqueta"] = etiqueta()
    prop.guardar(N)
    out["t"] = round(time.time() - t)
    with open(os.path.join(R["raiz"], "_prep.json"), "w", encoding="utf8") as fh:
        json.dump(out, fh, indent=1, default=str)
    return out
