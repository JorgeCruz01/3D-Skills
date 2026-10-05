"""Tandas de puertas de la skill por fase, para no reescribirlas en cada prop.

Cada funcion devuelve {"ok": bool, ...} con los numeros medidos. `ok` es False
si no se evaluo nada.

Las mediciones que nacieron en este lote (texturas en disco, ida y vuelta del
FBX, fidelidad del bake, distancia a superficie) viven en la skill
(`verifications.py`), con el caso real del casco en su docstring. Aqui solo
quedan las tandas y los nombres en espanol que usan los scripts del lote.
"""
import verifications as V


def geometria(nombres, max_aspecto=100):
    """manifold + degenerate_faces + escala aplicada, pieza a pieza."""
    fallos, caras = {}, 0
    for n in nombres:
        m = V.manifold(n)
        d = V.degenerate_faces(n)
        caras += m["faces"]
        if m["boundary"] or m["nonmanifold"] or d["over_100"] or m["scale"] != [1, 1, 1] or d["max"] > max_aspecto:
            fallos[n] = {"boundary": m["boundary"], "nonmanifold": m["nonmanifold"],
                         "over_100": d["over_100"], "max": d["max"], "scale": m["scale"]}
    return {"ok": bool(nombres) and not fallos, "evaluated": len(nombres), "caras": caras, "fallos": fallos}


def ensamblaje(nombres):
    r = V.pairwise_intersections(list(nombres), margin=0.0)
    ok = r["clean"] and not r["unverified_parts"] and not r["open_meshes"]
    return {"ok": bool(ok), "evaluated": len(nombres), "pairs": r["pairs"], "disagreement": r["disagreement"],
            "unverified_parts": r["unverified_parts"], "open_meshes": r["open_meshes"]}


def distancia_minima(a, b):
    r = V.surface_distance(a, b)
    return {"min_mm": r.get("min_mm"), "vertices_por_dentro": r.get("vertices_behind")}


def texturas_en_disco(directorio, esperado):
    return V.texture_files(directorio, esperado)


def piso_densidad(nombres, texture_res, piso_px_mm):
    r = V.uv_density(list(nombres), texture_res=texture_res)
    bajos = {n: v for n, v in r["px_per_mm"].items() if v < piso_px_mm}
    return {"ok": bool(r["px_per_mm"]) and not bajos, "evaluated": len(r["px_per_mm"]),
            "min_px_mm": min(r["px_per_mm"].values()) if r["px_per_mm"] else None,
            "piso": piso_px_mm, "below_floor": bajos}


def ida_y_vuelta_fbx(ruta, tris, capas_uv=1, materiales=None, dims_mm=None, tol_mm=0.5):
    return V.fbx_roundtrip(ruta, tris, capas_uv, materiales, dims_mm, tol_mm)


def huella(coleccion):
    """Huella de una coleccion: {nombre: (vertices, caras)}. Se toma del high poly
    ANTES de construir la low poly y se compara despues con `huella_intacta`:
    nada de lo que se haga con la LP debe tocar el HP."""
    import bpy
    return {o.name: (len(o.data.vertices), len(o.data.polygons))
            for o in bpy.data.collections[coleccion].all_objects if o.type == "MESH"}


def huella_intacta(coleccion, antes):
    ahora = huella(coleccion)
    faltan = sorted(set(antes) - set(ahora))
    nuevas = sorted(set(ahora) - set(antes))
    cambiadas = sorted(n for n in antes if n in ahora and antes[n] != ahora[n])
    return {"ok": bool(antes) and not (faltan or nuevas or cambiadas), "evaluated": len(antes),
            "faltan": faltan, "nuevas": nuevas, "cambiadas": cambiadas}


def fugas(nombres, punto, permitidas=(), n=4000):
    """Prueba de fugas: lanza `n` rayos desde `punto` (dentro de una cavidad) en
    todas direcciones contra el conjunto `nombres`. Los que no chocan con nada
    escapan por una abertura. `permitidas` = [(direccion, semiangulo_grados)]:
    las aberturas que SI deben existir (las bocas del paso de una valvula).

    Caso que la motivo: la cavidad interior del bonete de una valvula rompio la
    pared de la cupula donde esta se estrecha. La pieza seguia siendo estanca,
    sin caras degeneradas y sin cruces; el agujero se vio en un render."""
    import math
    import bmesh
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for nom in nombres:
        ob = bpy.data.objects[nom]
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        tmp.transform(ob.matrix_world)
        me = bpy.data.meshes.new("_fugas")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    arbol = BVHTree.FromBMesh(bm)
    bm.free()
    p = Vector(punto)
    conos = [(Vector(d).normalized(), math.cos(math.radians(a))) for d, a in permitidas]
    escapes, suma = 0, Vector()
    g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        d = Vector((r * math.cos(g * i), r * math.sin(g * i), z))
        if arbol.ray_cast(p, d)[0] is None and not any(d.dot(c) >= cosa for c, cosa in conos):
            escapes += 1
            suma += d
    return {"ok": bool(nombres) and escapes == 0, "evaluated": n, "escapes": escapes,
            "direccion_media": [round(v, 2) for v in (suma / escapes)] if escapes else None}


def fidelidad_bake(col_hp, col_lp, camara, salida_dir, res=(1024, 1024), samples=48, ocultar=()):
    return V.bake_fidelity(col_hp, col_lp, camara, salida_dir, res=res, samples=samples, hide=ocultar)
