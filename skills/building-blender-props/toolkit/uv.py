"""Despliegue UV con costuras propias, sin proyeccion automatica por angulo.

Regla: toda arista viva es costura, y cada isla que queda entre costuras debe
ser topologicamente un disco (un solo borde, sin asas) para poder desplegarse
plana. `costuras` lo consigue en dos pasos:

1. Marca como costura las aristas con angulo diedro mayor que el umbral.
2. Para cada isla que no es un disco, anade el corte minimo: un camino de
   aristas que une dos de sus bordes (un cilindro pasa a ser un rectangulo), o
   un tajo entre dos puntos alejados si la isla es cerrada.

Los cortes anadidos se esconden: el coste de cada arista crece cuanto mas mira
hacia `vista`, la direccion desde el objeto hacia la camara del hero.
"""
import heapq
import math

import bmesh
import bpy
from mathutils import Vector

VISTA = Vector((0.8, -1.0, 0.42)).normalized()


def _islas(bm):
    """Grupos de caras conectadas por aristas que no son costura."""
    vistas, islas = set(), []
    for f in bm.faces:
        if f.index in vistas:
            continue
        pila, isla = [f], []
        vistas.add(f.index)
        while pila:
            g = pila.pop()
            isla.append(g)
            for e in g.edges:
                if e.seam:
                    continue
                for h in e.link_faces:
                    if h.index not in vistas:
                        vistas.add(h.index)
                        pila.append(h)
        islas.append(isla)
    return islas


def _bordes(isla):
    """Aristas de borde de la isla agrupadas en lazos (por vertices compartidos)."""
    dentro = {f.index for f in isla}
    borde = set()
    for f in isla:
        for e in f.edges:
            n = sum(1 for g in e.link_faces if g.index in dentro)
            if n == 1 or e.seam:
                borde.add(e)
    padre = {}

    def raiz(a):
        while padre.setdefault(a, a) != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    for e in borde:
        padre[raiz(e.verts[0].index)] = raiz(e.verts[1].index)
    lazos = {}
    for e in borde:
        lazos.setdefault(raiz(e.verts[0].index), set()).update(v for v in e.verts)
    return list(lazos.values())


def _largo(lazo):
    """Perimetro aproximado de un lazo: suma de sus aristas de costura."""
    vs = {v.index for v in lazo}
    vistas, total = set(), 0.0
    for v in lazo:
        for e in v.link_edges:
            if e.index not in vistas and e.seam and e.other_vert(v).index in vs:
                vistas.add(e.index)
                total += e.calc_length()
    return total


def _planitud(isla):
    """|media ponderada de normales|: 1 = isla plana, ~0 = envuelve un volumen."""
    s, a = Vector(), 0.0
    for f in isla:
        ar = f.calc_area()
        s += f.normal * ar
        a += ar
    return s.length / a if a > 0 else 0.0


def _euler(isla):
    """Caracteristica de Euler de la isla CORTADA por sus costuras: un vertice
    sobre una costura cuenta una vez por cada abanico de caras que toca."""
    dentro = {f.index for f in isla}
    aristas = set()
    for f in isla:
        aristas.update(f.edges)
    # aristas: una costura interior a la isla separa, cuenta doble
    E = sum(2 if (e.seam and sum(1 for g in e.link_faces if g.index in dentro) == 2) else 1 for e in aristas)
    # vertices: numero de abanicos de caras de la isla alrededor de cada vertice
    V = 0
    verts = {v for f in isla for v in f.verts}
    for v in verts:
        caras = [g for g in v.link_faces if g.index in dentro]
        resto, abanicos = set(g.index for g in caras), 0
        while resto:
            abanicos += 1
            pila = [resto.pop()]
            while pila:
                gi = pila.pop()
                g = next(c for c in caras if c.index == gi)
                for e in g.edges:
                    if v not in e.verts or e.seam:
                        continue
                    for h in e.link_faces:
                        if h.index in resto:
                            resto.discard(h.index)
                            pila.append(h.index)
        V += abanicos
    return V - E + len(isla)


def _camino(isla, origen, destino, vista):
    """Dijkstra por aristas interiores de la isla, de un conjunto de vertices a otro."""
    dentro = {f.index for f in isla}
    dist = {v.index: 0.0 for v in origen}
    previo = {}
    cola = [(0.0, v.index, v) for v in origen]
    heapq.heapify(cola)
    meta = {v.index for v in destino}
    while cola:
        d, _, v = heapq.heappop(cola)
        if d > dist.get(v.index, 1e18):
            continue
        if v.index in meta and d > 0:
            camino = []
            while v.index in previo:
                e, v = previo[v.index]
                camino.append(e)
            return camino
        for e in v.link_edges:
            if e.seam or not any(g.index in dentro for g in e.link_faces):
                continue
            w = e.other_vert(v)
            n = sum((g.normal for g in e.link_faces), Vector()).normalized()
            coste = e.calc_length() * (1.0 + 3.0 * max(0.0, n.dot(vista)))
            nd = d + coste
            if nd < dist.get(w.index, 1e18):
                dist[w.index] = nd
                previo[w.index] = (e, v)
                heapq.heappush(cola, (nd, w.index, w))
    return []


def costuras(nombre, angulo_grados=50, vista=VISTA, max_pasadas=6, extra=None, plana=0.9):
    """Marca las costuras de `nombre`. Devuelve cuantas islas quedan y cuantas
    no son discos ni casi planas (deberia ser 0).

    `extra`: funcion arista -> bool con costuras propias del prop (el ecuador de
    un aro, una linea de particion). `plana`: una isla con varios bordes pero
    planitud mayor que este valor se deja como esta: una cara de brida con sus
    taladros se despliega sin cortes."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    lim = math.radians(angulo_grados)
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.seam = True
        else:
            e.seam = e.calc_face_angle(0.0) > lim or bool(extra and extra(e))
    anadidas = 0
    for _ in range(max_pasadas):
        cambio = False
        for isla in _islas(bm):
            lazos = _bordes(isla)
            if len(lazos) >= 2:
                if _planitud(isla) > plana:
                    continue
                # une el lazo mas largo con el mas cercano
                lazos.sort(key=len, reverse=True)
                mejor, pareja = None, None
                for otro in lazos[1:]:
                    c = _camino(isla, lazos[0], otro, vista)
                    if c and (mejor is None or sum(e.calc_length() for e in c) < sum(e.calc_length() for e in mejor)):
                        mejor, pareja = c, otro
                if mejor:
                    # isla conica (los dos bordes miden distinto): un solo corte la
                    # despliega como un abanico que se pisa. Segundo corte, opuesto.
                    la, lb = _largo(lazos[0]), _largo(pareja)
                    conica = len(lazos) == 2 and min(la, lb) > 0 and max(la, lb) / min(la, lb) > 1.25
                    for e in mejor:
                        e.seam = True
                    anadidas += len(mejor)
                    if conica:
                        c2 = _camino(isla, lazos[0], pareja, -vista)
                        for e in c2:
                            e.seam = True
                        anadidas += len(c2)
                    cambio = True
            elif len(lazos) == 0:
                # isla cerrada: tajo entre los dos vertices mas alejados a lo largo de la direccion oculta
                verts = list({v for f in isla for v in f.verts})
                a = min(verts, key=lambda v: v.co.dot(vista))
                b = max(verts, key=lambda v: (v.co - a.co).length)
                c = _camino(isla, [a], [b], vista)
                for e in c:
                    e.seam = True
                anadidas += len(c)
                cambio = bool(c)
            elif _euler(isla) < 1:
                # un borde pero con asas: corta entre dos puntos alejados del propio borde
                verts = list(lazos[0])
                a = min(verts, key=lambda v: v.co.dot(vista))
                lejos = sorted({v for f in isla for v in f.verts} - lazos[0], key=lambda v: -(v.co - a.co).length)
                if lejos:
                    c = _camino(isla, [a], [lejos[0]], vista)
                    for e in c:
                        e.seam = True
                    anadidas += len(c)
                    cambio = bool(c)
        if not cambio:
            break
    islas = _islas(bm)
    no_disco = sum(1 for i in islas if (len(_bordes(i)) != 1 or _euler(i) != 1) and _planitud(i) <= plana)
    n_costuras = sum(1 for e in bm.edges if e.seam)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return {"islas": len(islas), "no_disco": no_disco, "costuras": n_costuras, "anadidas": anadidas}


def caras_solapadas(nombre, rejilla=2048):
    """Indices de las caras cuyo UV comparte celda con otra cara. Rasteriza cada
    triangulo UV con prueba estricta (el borde no cuenta)."""
    import numpy as np
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    luv = bm.loops.layers.uv.active
    celdas = {}
    for f in bm.faces:
        ls = [l[luv].uv for l in f.loops]
        for i in range(1, len(ls) - 1):
            tri = np.array([[ls[0].x, ls[0].y], [ls[i].x, ls[i].y], [ls[i + 1].x, ls[i + 1].y]]) * rejilla
            x0, x1 = max(int(np.floor(tri[:, 0].min())), 0), min(int(np.ceil(tri[:, 0].max())) + 1, rejilla)
            y0, y1 = max(int(np.floor(tri[:, 1].min())), 0), min(int(np.ceil(tri[:, 1].max())) + 1, rejilla)
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
            a, b, c = tri
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
            yy, xx = np.nonzero((w0 > 1e-6) & (w1 > 1e-6) & ((1 - w0 - w1) > 1e-6))
            for k in zip((yy + y0).tolist(), (xx + x0).tolist()):
                celdas.setdefault(k, set()).add(f.index)
    bm.free()
    malas = set()
    for fs in celdas.values():
        if len(fs) >= 2:
            malas |= fs
    return malas


def _refinar(nombre, caras, angulo_grados):
    """Anade costuras, SOLO en las islas que contienen `caras`, en toda arista con
    angulo diedro mayor que `angulo_grados` (0 = todas)."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    lim = math.radians(angulo_grados)
    n = 0
    for isla in _islas(bm):
        if not any(f.index in caras for f in isla):
            continue
        dentro = {f.index for f in isla}
        for f in isla:
            for e in f.edges:
                if not e.seam and len(e.link_faces) == 2 and all(g.index in dentro for g in e.link_faces) \
                        and e.calc_face_angle(0.0) >= lim:
                    e.seam = True
                    n += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n


def _aislar(nombre, caras):
    """Ultimo recurso quirurgico: costura alrededor de CADA cara solapada, y solo de ellas. El umbral 0 de `_refinar`
    corta todas las aristas de la isla: por 2 caras que se pisaban dejo una isla de 824 caras en quads sueltos."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    n = 0
    for i in caras:
        for e in bm.faces[i].edges:
            if not e.seam:
                e.seam = True
                n += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n


def caras_uv_nulas(nombre):
    """Caras con area en el modelo y area UV nula. Una isla que el despliegue no
    resuelve (cerrada, sin borde) se queda con sus UV en un punto: `uv_overlap`
    sigue en 0 y el horneado no escribe nada en ella. En la jaula de un grupo
    electrogeno fueron 582 caras; lo unico que lo delataba era un aviso de
    Blender ("Unwrap failed to solve 1 of 976 islands") en la salida."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    capa = bm.loops.layers.uv.active
    n = 0
    if capa:
        for f in bm.faces:
            a, b, c = [l[capa].uv for l in f.loops][:3]
            if abs((b - a).cross(c - a)) / 2 < 1e-12 and f.calc_area() > 1e-8:
                n += 1
    total = len(bm.faces)
    bm.free()
    return {"ok": capa is not None and n == 0, "nulas": n, "caras": total}


def _refinar_por_ejes(nombre, caras):
    """Anade costuras, SOLO en las islas que contienen `caras`, entre caras cuya
    normal tiene distinto eje dominante (+X, -X, +Y, -Y, +Z, -Z): parte la isla
    en hasta seis cartas, como una proyeccion en caja. Va ANTES de los umbrales
    de angulo: cortar todas las aristas de una isla la deja en triangulos sueltos
    (un lazo de timon acabo en 2 810 islas y el atlas en el 27 %)."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    bm.faces.ensure_lookup_table()

    def clase(f):
        n = f.normal
        i = max(range(3), key=lambda k: abs(n[k]))
        return (i, n[i] > 0)
    k = 0
    for isla in _islas(bm):
        if not any(f.index in caras for f in isla):
            continue
        dentro = {f.index for f in isla}
        for f in isla:
            for e in f.edges:
                if not e.seam and len(e.link_faces) == 2 and all(g.index in dentro for g in e.link_faces) \
                        and clase(e.link_faces[0]) != clase(e.link_faces[1]):
                    e.seam = True
                    k += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return k


def desplegar(nombres, margen=0.003, angulo_grados=50, vista=VISTA, extra=None, metodo="MINIMUM_STRETCH",
              refinado=("ejes", 25, 12, 5, 0)):
    """Costuras + despliegue + escala igualada + empaquetado. Todos los `nombres`
    comparten un mismo atlas 0-1.

    Red de seguridad: si tras desplegar alguna isla se pisa a si misma, se le
    anaden costuras con los umbrales de `refinado`, uno por pasada, y se vuelve a
    desplegar. Solo se tocan las islas con solape; el resto conserva sus islas
    grandes. Devuelve en `refinado` cuantas costuras anadio cada pasada.
    Un paso `"aislar"` en `refinado` separa solo las caras solapadas (una isla por cara): para mallas remalladas
    (QuadriFlow), donde los umbrales bajos trituran islas enteras, usar `refinado=("ejes", 25, 12, "aislar", "aislar")`."""
    info = {n: costuras(n, angulo_grados, vista, extra=extra) for n in nombres}
    info["refinado"] = []
    for paso in (None,) + tuple(refinado):
        if paso is not None:
            anadidas = 0
            for n in nombres:
                malas = caras_solapadas(n)
                if malas:
                    anadidas += _refinar_por_ejes(n, malas) if paso == "ejes" else (_aislar(n, malas) if paso == "aislar" else _refinar(n, malas, paso))
            if not anadidas:
                continue          # a este umbral no hay nada que cortar: probar el siguiente
            info["refinado"].append({"umbral": paso, "costuras": anadidas})
        _desplegar_una_vez(nombres, margen, metodo)
        if not any(caras_solapadas(n) for n in nombres):
            break
    return info


def _desplegar_una_vez(nombres, margen, metodo):
    area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    obs = [bpy.data.objects[n] for n in nombres]
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    bpy.context.view_layer.objects.active = obs[0]
    with bpy.context.temp_override(area=area, region=region, active_object=obs[0], object=obs[0],
                                   selected_objects=obs, selected_editable_objects=obs):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        # MINIMUM_STRETCH (SLIM) con no_flip: el despliegue por angulos dejaba un
        # pliegue en la punta de cada cuarto de cupula (460 celdas solapadas)
        bpy.ops.uv.unwrap(method=metodo, fill_holes=True, correct_aspect=True, margin=margen,
                          **({"no_flip": True, "iterations": 20} if metodo == "MINIMUM_STRETCH" else {}))
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin=margen, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")


def encoger_ocultas(nombre, factor=0.55, alcance=0.009, fraccion=0.7, margen=0.0022, tambien=None):
    """Reduce a `factor` las islas que no se ven y vuelve a empaquetar: el atlas que liberan sube la densidad de lo
    que si se ve. Una isla es oculta si mas de `fraccion` de su area lanza un rayo por su normal que da en la propia
    malla a menos de `alcance` (caras pegadas a otra pieza), o si `tambien(isla)` lo dice (el anima de un canon).
    Nacio en el cuchillo (vira e interior de la funda): 61 -> 75 % de ocupacion junto con las tiras de canto."""
    from mathutils.bvhtree import BVHTree
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    arbol = BVHTree.FromBMesh(bm)
    capa = bm.loops.layers.uv.active
    n, area_oc = 0, 0.0
    for isla in _islas(bm):
        tot = oc = 0.0
        for f in isla:
            a = f.calc_area()
            tot += a
            if arbol.ray_cast(f.calc_center_median() + f.normal * 5e-5, f.normal, alcance)[0] is not None:
                oc += a
        if tot and (oc / tot > fraccion or (tambien and tambien(isla))):
            ls = [l for f in isla for l in f.loops]
            c = sum((l[capa].uv for l in ls), Vector((0.0, 0.0))) / len(ls)
            for l in ls:
                l[capa].uv = c + (l[capa].uv - c) * factor
            n += 1
            area_oc += tot
    bm.to_mesh(ob.data)
    bm.free()
    area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(area=area, region=region, active_object=ob, object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(rotate=True, margin=margen, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")
    return {"islas": n, "area_cm2": round(area_oc * 1e4, 1), "factor": factor}


def soldar_uv(nombre, tol=0.0008):
    """Une las UV de un mismo vertice que quedaron a menos de `tol`: una costura que no llega a cerrar su isla deja
    los dos lados separados media celda y solapados."""
    me = bpy.data.objects[nombre].data
    uvs = me.uv_layers.active.data
    por_vertice = {}
    for l in me.loops:
        por_vertice.setdefault(l.vertex_index, []).append(l.index)
    n = 0
    for ls in por_vertice.values():
        hechos = set()
        for a in ls:
            if a in hechos:
                continue
            grupo = [b for b in ls if b not in hechos and (uvs[a].uv - uvs[b].uv).length < tol]
            hechos.update(grupo)
            if len(grupo) > 1 and any((uvs[a].uv - uvs[b].uv).length > 0 for b in grupo):
                m = sum((uvs[b].uv for b in grupo), uvs[a].uv * 0.0) / len(grupo)
                for b in grupo:
                    uvs[b].uv = m
                n += 1
    me.update()
    return n
