"""Reexporta el FBX/GLB de los props ya entregados sin tocar su geometria.

Abrir un .blend y exportar en la misma ejecucion falla (el contexto queda
obsoleto: `Context has no attribute selected_objects`), asi que va por pasos:
cada llamada a `paso()` exporta el archivo abierto y deja abierto el siguiente.

La raiz es la de `prop` (`prop.configurar` o BLENDER_PROPS_ROOT); la cola y los
resultados se guardan en `<raiz>/_reexportacion.json`.
"""
import json
import os

import bpy

import entrega
import prop


def _registro():
    if not prop.RAIZ:
        raise RuntimeError("prop.RAIZ sin definir: llamar a prop.configurar(raiz) o definir BLENDER_PROPS_ROOT")
    return os.path.join(prop.RAIZ, "_reexportacion.json")


def _leer():
    return json.load(open(_registro())) if os.path.exists(_registro()) else {}


def empezar(props):
    json.dump({"cola": list(props), "hecho": {}}, open(_registro(), "w"), indent=1)
    if bpy.data.is_dirty and bpy.data.filepath:
        bpy.ops.wm.save_mainfile()
    bpy.ops.wm.open_mainfile(filepath=os.path.join(prop.RAIZ, props[0], props[0] + ".blend"))
    return {"abierto": props[0]}


def paso():
    r = _leer()
    if not r["cola"]:
        return {"fin": True, "hecho": r["hecho"]}
    n = r["cola"][0]
    abierto = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if abierto != n:
        return {"error": "abierto %s, esperado %s" % (abierto, n)}
    lps = [o for o in bpy.data.collections["LP Collection"].all_objects if o.type == "MESH"]
    planas = sum(1 for o in lps for p in o.data.polygons if not p.use_smooth)
    mats = []
    for o in lps:
        for s in o.material_slots:
            if s.material.name not in mats:
                mats.append(s.material.name)
    ex = entrega.exportar_y_verificar(n, [o.name for o in lps], mats)
    r["hecho"][n] = {"caras_planas": planas, "tris": ex["tris"], "ok": ex["ida_y_vuelta"]["ok"], "diffs": ex["ida_y_vuelta"]["diffs"]}
    r["cola"] = r["cola"][1:]
    json.dump(r, open(_registro(), "w"), indent=1)
    if r["cola"]:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(prop.RAIZ, r["cola"][0], r["cola"][0] + ".blend"))
    return {"exportado": n, **r["hecho"][n], "quedan": len(r["cola"])}
