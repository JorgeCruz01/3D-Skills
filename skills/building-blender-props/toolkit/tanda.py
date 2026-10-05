"""Tramo comun del cierre de un prop: del low poly ya desplegado al FBX verificado.
Lo que cambia de un prop a otro (costuras, replicas, juntas) queda fuera."""
import json
import os

import bpy
from mathutils import Vector

import bake
import entrega
import estudio
import lowpoly as L
import prop
import puertas
import verifications as V

HP, LP = "Model Collection", "LP Collection"


def medir_uv(nombres):
    """Puertas UV de cada objeto: solapes a 1024 y 2048, ocupacion, densidad y caras sin area UV."""
    out, ok = {}, True
    for n in nombres:
        o = {g: V.uv_overlap([n], grid=g) for g in (1024, 2048)}
        dens = V.uv_density([n], texture_res=4096)
        nv = V.uv_null_faces([n])
        out[n] = {"overlap": [v["overlapping_cells"] for v in o.values()], "cov": o[1024]["coverage_pct"],
                  "px_mm": dens["mean"], "null": nv["null"]}
        ok = ok and nv["ok"] and not any(v["overlapping_cells"] for v in o.values())
    out["ok"] = ok
    return out


def malla(nombre):
    m = V.manifold(nombre)
    d = V.degenerate_faces(nombre)
    return {"boundary": m["boundary"], "nonmanifold": m["nonmanifold"], "ngons": m["ngons"], "max": round(d["max"]),
            "over_100": d["over_100"], "ok": not (m["boundary"] or m["nonmanifold"] or m["ngons"] or d["over_100"])}


def hornear_y_exportar(nombre, lp_nombre, solidos_hp, sets, hero, extrusion, vistas=None, scratch=None, ao=0.0,
                       solo_medir=False):
    """`sets`: nombres de set (material LP_<set>, texturas TX_<set>_*). Hornea,
    monta los materiales finales, mide silueta en tres vistas y fidelidad desde
    `hero`, exporta y comprueba la ida y vuelta. Guarda el resumen en _ultimo.json."""
    R = prop.rutas(nombre)
    T = R["texturas"]
    res = {}
    lp = bpy.data.objects[lp_nombre]
    lp.hide_render = False
    for ob in list(bpy.data.collections[HP].all_objects):
        ob.hide_render = False
    if not solo_medir:
        px = L.proxy_bake(lp_nombre)
        # la LP original se oculta mientras se hornea contra su copia: una LP diezmada entra y sale
        # de la piel del high poly y, visible, la ocluye a manchas (mapa de oclusion casi negro)
        lp.hide_render = True
        hp = list(solidos_hp) + [x.name for x in bpy.data.collections["Rotulos"].objects]
        r = bake.hornear(hp, px, {"LP_" + s: s for s in sets}, T, res=4096, extrusion=extrusion, margen=6, samples=8, samples_ao=24)
        L.quitar_proxy(lp_nombre)
        lp.hide_render = False
        res["bake_s"] = round(sum(r["tiempos_s"].values()), 1)
        for img in list(bpy.data.images):
            if img.name.startswith("BK_"):
                bpy.data.images.remove(img)
        tex = puertas.texturas_en_disco(T, {f"TX_{s}_{m}.png": (4096, 4096) for s in sets for m in ("BaseColor", "Normal", "ORM")})
        for s in sets:
            bake.material_final("LP_" + s, {m: os.path.join(T, f"TX_{s}_{m}.png") for m in ("BaseColor", "Normal", "ORM")})
    else:
        tex = puertas.texturas_en_disco(T, {f"TX_{s}_{m}.png": (4096, 4096) for s in sets for m in ("BaseColor", "Normal", "ORM")})

    def _materiales(fuerza):
        for s in sets:
            bake.material_final("LP_" + s, {m: os.path.join(T, f"TX_{s}_{m}.png") for m in ("BaseColor", "Normal", "ORM")}, ao=fuerza)

    _materiales(ao)
    res["tex"] = tex["ok"]
    lp = bpy.data.objects[lp_nombre]
    lp.hide_render = False
    estudio.guardar_base()
    sil = {}
    for etiqueta, dvec in (vistas or (("hero", hero), ("frente", (0.02, -1.0, 0.02)), ("lado", (1.0, 0.03, 0.05)))):
        cam = bpy.data.objects["CAM_Detalle"]
        cam["base_dir"] = list(Vector(dvec).normalized())
        estudio.encuadrar("CAM_Detalle", HP, 0.05, (1400, 1400))
        s_ = V.silhouette_hp_vs_lp(HP, LP, "CAM_Detalle", res=(1400, 1400), samples=8, hide=("Backdrop_360",))
        sil[etiqueta] = (s_["differing_px_pct"], s_["area_delta_pct"])
    res["silueta"] = sil
    estudio.escalar_luces(HP)
    cam = bpy.data.objects["CAM_Beauty"]
    cam["base_dir"] = list(Vector(hero).normalized())
    estudio.encuadrar("CAM_Beauty", HP, 0.05, (1024, 1024))
    f = V.bake_fidelity(HP, LP, "CAM_Beauty", scratch or R["texturas_bakes"], samples=64, hide=("Backdrop_360",))
    _materiales(0.0)                 # el glTF sale con el material limpio: la oclusion viaja en el ORM
    ex = entrega.exportar_y_verificar(nombre, [lp_nombre], ["LP_" + s for s in sets])
    _materiales(ao)
    res.update({"fidelidad": (f["ok"], f["mean_diff_255"], f["mean_smooth_255"]),
                "export": {"tris": ex["tris"], "dims": ex["dims_mm"], "ida_y_vuelta": ex["ida_y_vuelta"]["ok"],
                           "diffs": ex["ida_y_vuelta"]["diffs"]}})
    bpy.ops.wm.save_mainfile()
    json.dump(res, open(os.path.join(R["raiz"], "_ultimo.json"), "w"), default=str, indent=1)
    return res


def cerrar(nombre, lp_nombre, sets, hero, esperados, grosor=0.0008):
    """Laminas tecnicas con la camara del hero, paquete de portafolio y cierre."""
    T = prop.rutas(nombre)["texturas"]
    previo = estudio.DIRECCIONES["CAM_Topo"]
    estudio.DIRECCIONES["CAM_Topo"] = tuple(hero)
    try:
        l = entrega.laminas_tecnicas(nombre, [lp_nombre], [os.path.join(T, "TX_%s_%s.png" % (st, m)) for st in sets
                                                           for m in ("BaseColor", "Normal", "ORM")], grosor=grosor)
    finally:
        estudio.DIRECCIONES["CAM_Topo"] = previo
    p = entrega.paquete_portafolio(nombre)
    c = entrega.cerrar(nombre, [lp_nombre] + list(esperados))
    return {"split": l["split"]["misma_camara"], "paquete": {k: v["ok"] for k, v in p.items()}, "cerrar": c["en_disco"]["ok"],
            "faltan": c["rutas_externas_faltantes"]}
