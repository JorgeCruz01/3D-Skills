"""Cierre de un prop: exportacion, renders, laminas y comprobaciones de entrega.

Cada funcion hace una fase y devuelve sus mediciones. Los renders largos van de
uno en uno para no pasar de los 120 s por llamada del MCP.
"""
import os
import shutil

import bpy
from mathutils import Vector

import estudio
import exportar
import laminas
import prop
import puertas
import verifications as V

HP, LP = "Model Collection", "LP Collection"


def _ver(hp=True, lp=False, extra_ocultos=()):
    for o in list(bpy.data.collections[HP].all_objects):
        o.hide_render = not hp
    for o in list(bpy.data.collections[LP].all_objects):
        o.hide_render = not lp
    for n in extra_ocultos:
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = True


def exportar_y_verificar(nombre, objetos_lp, materiales):
    """FBX + GLB de la LP y prueba de ida y vuelta."""
    R = prop.rutas(nombre)
    for o in list(bpy.data.collections[LP].all_objects):
        o.hide_render = False
    ex = exportar.fbx_glb(objetos_lp, R["exportados"], nombre + "_LP")
    tris = 0
    for n in objetos_lp:
        me = bpy.data.objects[n].data
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
    bb = estudio._bbox(LP)
    dims = [round((bb[1][i] - bb[0][i]) * 1000, 2) for i in range(3)]
    rt = puertas.ida_y_vuelta_fbx(ex["fbx"], tris, 1, materiales, dims)
    return {"export": ex, "tris": tris, "dims_mm": dims, "ida_y_vuelta": rt}


def still(nombre, fichero, direccion, res=(3840, 2160), samples=160, margen=0.02, ocultar=(), relleno=None, lp=False):
    """Un still del HIGH POLY desde `direccion` (objeto -> camara). `relleno` =
    (posicion, potencia_W, tamano_m) anade una luz de area temporal mirando al
    centro del prop, para tomas donde las luces del rig no llegan.
    `lp=True` renderiza la LOW POLY con sus texturas: es lo que toca cuando las
    texturas se hicieron en Substance Painter, porque el high poly ya no lleva
    el material que se entrega."""
    R = prop.rutas(nombre)
    sc = bpy.context.scene
    _ver(hp=not lp, lp=lp, extra_ocultos=ocultar)
    estudio.guardar_base()
    estudio.escalar_luces(HP)
    cam = bpy.data.objects["CAM_Beauty"]
    cam["base_dir"] = list(Vector(direccion).normalized())
    e = estudio.encuadrar("CAM_Beauty", HP, margen, res)
    luz = None
    if relleno:
        ld = bpy.data.lights.new("_relleno", "AREA")
        ld.size, ld.energy = relleno[2], relleno[1]
        luz = bpy.data.objects.new("_relleno", ld)
        sc.collection.objects.link(luz)
        luz.location = relleno[0]
        bb = estudio._bbox(HP)
        d = ((bb[0] + bb[1]) / 2 - Vector(relleno[0])).normalized()
        luz.rotation_mode = "QUATERNION"
        luz.rotation_quaternion = (-d).to_track_quat("Z", "Y")
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    s = sc.render.image_settings
    s.file_format, s.color_mode, s.color_depth = "PNG", "RGB", "8"
    ruta = os.path.join(R["renders_stills"], fichero)
    sc.render.filepath = ruta
    import time
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = round(time.time() - t, 1)
    if luz:
        ld = luz.data
        bpy.data.objects.remove(luz)
        bpy.data.lights.remove(ld)
    for n in ocultar:
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = False
    cam["base_dir"] = list(Vector(estudio.DIRECCIONES["CAM_Beauty"]).normalized())
    return {"ruta": ruta, "ok": os.path.exists(ruta), "encuadre": e["all_inside"], "t": dt}


def arcilla(nombre, direccion, fichero="05_arcilla_ao.png", gris=0.62, alcance=0.06, **kw):
    """Still del HIGH POLY en arcilla gris con la oclusion multiplicada, bajo las mismas luces y la misma camara
    que el hero: ensena la forma sin textura. `alcance`: distancia de la oclusion como fraccion de la diagonal del
    prop. El AO solo, sin luces, sale plano y sobre el ciclorama blanco el modelo se pierde: por eso va con luces."""
    m = bpy.data.materials.get("_Arcilla_AO") or bpy.data.materials.new("_Arcilla_AO")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    lo, hi = estudio._bbox(HP)
    ao.inputs["Color"].default_value = (gris, gris, gris, 1)
    ao.inputs["Distance"].default_value = (hi - lo).length * alcance
    ao.samples = 16
    b.inputs["Roughness"].default_value = 0.62
    nt.links.new(ao.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    vl = bpy.context.view_layer
    previo = vl.material_override
    vl.material_override = m
    try:
        return still(nombre, fichero, direccion, **kw)
    finally:
        vl.material_override = previo
        bpy.data.materials.remove(m)


def laminas_tecnicas(nombre, objetos_lp, mapas, solo_alambre=(), tambien=(), grosor=0.0005, lp=False):
    """Split con una sola camara, wireframe, hoja UV y tira de mapas. `lp=True`: la mitad
    renderizada del split es la low poly texturizada (texturas de Substance Painter)."""
    R = prop.rutas(nombre)
    estudio.guardar_base()
    estudio.escalar_luces(HP)
    cam = bpy.data.objects["CAM_Topo"]
    cam["base_dir"] = list(Vector(estudio.DIRECCIONES["CAM_Topo"]).normalized())
    cam.data.lens = bpy.data.objects["CAM_Beauty"].data.lens
    cam.data.shift_x = cam.data.shift_y = 0.0
    estudio.encuadrar("CAM_Topo", HP, 0.03, (3840, 2160))
    _ver(hp=not lp, lp=lp)
    sp = laminas.par_split(objetos_lp, "CAM_Topo", R["renders_topologia"], res=(3840, 2160), samples=160,
                           grosor=grosor, solo_alambre=solo_alambre, tambien=tambien, render_lp=lp)
    _ver(hp=True, lp=False)
    uvh = laminas.hoja_uv_sets(objetos_lp, os.path.join(R["texturas"], "uv.png"), res=2048)["ruta"]   # una celda por set
    tira = laminas.tira_mapas(mapas, os.path.join(R["texturas"], "maps.png"), lado=1024)
    return {"split": sp, "uv": uvh, "maps": tira}


def paquete_portafolio(nombre, hero="01_hero.png"):
    R = prop.rutas(nombre)
    src = {"render": os.path.join(R["renders_stills"], hero),
           "split": os.path.join(R["renders_topologia"], "split.png"),
           "wireframe": os.path.join(R["renders_topologia"], "wireframe.png"),
           "uv": os.path.join(R["texturas"], "uv.png"), "maps": os.path.join(R["texturas"], "maps.png")}
    out = {}
    for k, v in src.items():
        r = laminas.a_webp(v, os.path.join(R["renders_portafolio"], k + ".webp"))
        out[k] = {"ok": r["ok"], "kb": round(os.path.getsize(r["ruta"]) / 1024) if r["ok"] else None}
    return out


def cerrar(nombre, esperados):
    """Guarda, comprueba el .blend EN DISCO (sobre una copia) y las rutas externas."""
    R = prop.rutas(nombre)
    _ver(hp=True, lp=False)
    g = prop.guardar(nombre)
    copia = os.path.join(R["raiz"], "_verificacion.blend")
    shutil.copyfile(R["blend"], copia)
    d = V.datablocks_on_disk(copia, expect_objects=tuple(esperados))
    os.remove(copia)
    ext = [(i.name, i.filepath) for i in bpy.data.images
           if i.source == "FILE" and i.filepath and not os.path.exists(bpy.path.abspath(i.filepath))]
    b1 = R["blend"] + "1"
    if os.path.exists(b1):
        os.remove(b1)
    return {"guardar": g, "en_disco": {"ok": d["ok"], "missing": d["missing"], "counts": d["counts"]},
            "rutas_externas_faltantes": ext}
