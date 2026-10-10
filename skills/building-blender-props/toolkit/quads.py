"""Topologia en quads para la low poly.

Las formas de `formas.py` ya nacen en quads salvo por dos cosas: las tapas (un
n-gono) y los polos de las revoluciones (un abanico de triangulos). `cuadrar`
sustituye ambas por una rejilla de quads sin mover el contorno. Lo que sale de
un booleano o de un remallado no tiene arreglo local: se rehace con `retopo`
(QuadriFlow) o, mejor, se construye sin booleano.

- `censo`: triangulos, quads, n-gonos y polos de un objeto.
- `cuadrar`: tapas y abanicos -> rejillas de quads.
- `retopo`: remallado en quads de una pieza organica.
- `ventana`: abre un hueco en una rejilla borrando quads y hundiendo el borde.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

MM = 0.001


def censo(ob):
    """{tris, quads, ngonos, caras, pct_quads, polos}: `polos` = vertices
    interiores con valencia distinta de 4."""
    me = ob.data if hasattr(ob, "data") else ob
    bm = bmesh.new()
    bm.from_mesh(me)
    t = sum(1 for f in bm.faces if len(f.verts) == 3)
    q = sum(1 for f in bm.faces if len(f.verts) == 4)
    n = len(bm.faces) - t - q
    polos = sum(1 for v in bm.verts if not v.is_boundary and len(v.link_edges) != 4)
    abiertas = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    total = len(bm.faces)
    nv = len(bm.verts)
    bm.free()
    return {"caras": total, "tris": t, "quads": q, "ngonos": n, "pct_quads": round(100.0 * q / max(1, total), 2),
            "polos": polos, "pct_polos": round(100.0 * polos / max(1, nv), 1), "aristas_no_estancas": abiertas}


# ------------------------------------------------------------------ rejilla de Coons

def _rejilla(P, a, b):
    """Puntos (a+1, b+1, 3) de la rejilla de Coons del lazo P (2a+2b puntos)."""
    N = len(P)
    B = P[0:a + 1]
    R = P[a:a + b + 1]
    T = P[[2 * a + b - i for i in range(a + 1)]]
    Lf = P[[(N - j) % N for j in range(b + 1)]]
    s = np.linspace(0, 1, a + 1)[:, None, None]
    t = np.linspace(0, 1, b + 1)[None, :, None]
    G = (1 - t) * B[:, None, :] + t * T[:, None, :] + (1 - s) * Lf[None, :, :] + s * R[None, :, :]
    G -= (1 - s) * (1 - t) * P[0] + s * (1 - t) * P[a] + (1 - s) * t * Lf[b] + s * t * R[b]
    return G


def _nota(G, normal):
    """Calidad de una rejilla: minimo de (area con signo / arista mayor^2) entre
    sus quads, medido en cada esquina. Negativo = algun quad esta doblado."""
    A, Bq, C, D = G[:-1, :-1], G[1:, :-1], G[1:, 1:], G[:-1, 1:]
    peor = np.inf
    e = np.maximum.reduce([np.sum((Bq - A) ** 2, -1), np.sum((C - Bq) ** 2, -1), np.sum((D - C) ** 2, -1), np.sum((A - D) ** 2, -1)])
    for p, q, r in ((A, Bq, D), (Bq, C, A), (C, D, Bq), (D, A, C)):
        cr = np.cross(q - p, r - p)
        peor = min(peor, float(np.min(np.sum(cr * normal, -1) / (e + 1e-30))))
    return peor


def _mejor_rejilla(P, normal):
    N = len(P)
    cen = P.mean(0)
    Q = P - cen
    w, _ = np.linalg.eigh(Q.T @ Q)
    r = math.sqrt(max(w[2], 1e-30) / max(w[1], 1e-30))          # alargamiento del contorno
    a0 = int(round(N / 2 * r / (1 + r)))
    cands = sorted({min(N // 2 - 1, max(1, x)) for x in (a0 - 1, a0, a0 + 1, N // 4, N // 2 - N // 4)})
    mejor = (-np.inf, None)
    for a in cands:
        b = N // 2 - a
        for off in range(N // 2 if a == b else N):
            G = _rejilla(np.roll(P, -off, 0), a, b)
            n = _nota(G, normal)
            if n > mejor[0]:
                mejor = (n, (a, b, off, G))
    return mejor


def _tapar(bm, lazo, normal, apice=None):
    """Rellena el lazo cerrado de vertices `lazo` (numero PAR) con quads. Devuelve
    la nota de la rejilla o None si no se pudo (impar, o se dobla)."""
    N = len(lazo)
    if N == 4:
        bm.faces.new(lazo)
        return 1.0
    if N % 2 or N < 4:
        return None
    P = np.array([v.co[:] for v in lazo])
    normal = np.asarray(normal, float)
    nota, mejor = _mejor_rejilla(P, normal)
    if mejor is None or nota <= 1e-4:
        return None
    a, b, off, G = mejor
    lz = lazo[off:] + lazo[:off]
    if apice is not None:                       # casquete: el interior sube hacia donde estaba el polo
        cen = P.mean(0)
        d = np.asarray(apice, float) - cen
        rad = np.linalg.norm(P - cen, axis=1).mean()
        rho = np.linalg.norm(G - cen - np.outer((G - cen) @ d, d).reshape(G.shape) / (d @ d + 1e-30), axis=-1) / (rad + 1e-30)
        G = G + np.clip(1 - rho ** 2, 0, 1)[..., None] * d
    V = [[None] * (b + 1) for _ in range(a + 1)]
    for i in range(a + 1):
        V[i][0] = lz[i]
        V[i][b] = lz[2 * a + b - i]
    for j in range(b + 1):
        V[a][j] = lz[a + j]
        V[0][j] = lz[(N - j) % N]
    for i in range(1, a):
        for j in range(1, b):
            V[i][j] = bm.verts.new(G[i, j])
    for i in range(a):
        for j in range(b):
            bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]))
    return nota


def _tapar_con_aro(bm, lazo, normal, apice=None):
    """Para contornos que la rejilla no admite (un dentado, una estrella): un
    aro de quads hasta un lazo interior alisado y encogido, y la rejilla dentro."""
    P = np.array([v.co[:] for v in lazo])
    cen = P.mean(0)
    S = P.copy()
    for _ in range(12):
        S = (np.roll(S, 1, 0) + 2 * S + np.roll(S, -1, 0)) / 4
    for k in (0.8, 0.65, 0.5):
        I = cen + (S - cen) * k
        dentro = [bm.verts.new(q) for q in I]
        caras = [bm.faces.new((lazo[i], lazo[(i + 1) % len(lazo)], dentro[(i + 1) % len(lazo)], dentro[i]))
                 for i in range(len(lazo))]
        r = _tapar(bm, dentro, normal, apice)
        if r is not None:
            return r
        bmesh.ops.delete(bm, geom=dentro, context="VERTS")
    return None


def _lazo_de(v):
    """Vertices del anillo que rodea a un polo `v` (todas sus caras, triangulos), en orden."""
    caras = v.link_faces[:]
    if len(caras) < 5 or any(len(f.verts) != 3 for f in caras) or v.is_boundary:
        return None
    sig = {}
    for f in caras:
        vs = f.verts[:]
        k = vs.index(v)
        sig[vs[(k + 1) % 3]] = vs[(k + 2) % 3]
    ini = next(iter(sig))
    lazo, x = [ini], sig.get(ini)
    while x is not None and x is not ini and len(lazo) <= len(caras):
        lazo.append(x)
        x = sig.get(x)
    return lazo if x is ini and len(lazo) == len(caras) else None


def _anillo(e, desde=None):
    """Aristas del anillo de `e` (las opuestas a traves de quads). Con `desde`,
    solo hacia el lado contrario a esa cara. Se para en la primera cara que no
    es un quad."""
    anillo, vistos = [e], {e}
    for f0 in e.link_faces:
        if f0 is desde:
            continue
        cur, f = e, f0
        while f is not None and len(f.verts) == 4:
            op = next(x for x in f.edges if x.verts[0] not in cur.verts and x.verts[1] not in cur.verts)
            if op in vistos:
                break
            vistos.add(op)
            anillo.append(op)
            sig = [g for g in op.link_faces if g is not f]
            cur, f = op, (sig[0] if len(sig) == 1 else None)
    return anillo


def _emparejar(bm):
    """Deja pares los contornos impares (tapas n-gono y abanicos de polo): parte
    por la mitad el anillo de aristas que nace de su arista mas larga. El anillo
    recorre el costado hasta la tapa opuesta, que gana el mismo vertice. Sin
    esto una tapa de 13 lados no admite rejilla."""
    hechas = 0
    for _ in range(64):
        obj = None
        for f in bm.faces:
            if len(f.verts) > 4 and len(f.verts) % 2:
                obj = (max(f.edges, key=lambda x: x.calc_length()), f)
                break
        if obj is None:
            for v in bm.verts:
                if len(v.link_faces) >= 5 and len(v.link_faces) % 2 and not v.is_boundary                         and all(len(f.verts) == 3 for f in v.link_faces):
                    f = max(v.link_faces, key=lambda t: next(x for x in t.edges if v not in x.verts).calc_length())
                    obj = (next(x for x in f.edges if v not in x.verts), f)
                    break
        if obj is None:
            break
        bmesh.ops.subdivide_edges(bm, edges=_anillo(*obj), cuts=1, use_grid_fill=False)
        hechas += 1
    return hechas


def cuadrar(ob, soldar=0.02 * MM):
    """Convierte en rejillas de quads los n-gonos (tapas) y los abanicos de
    triangulos (polos de revolucion). No mueve ningun vertice del contorno.
    Devuelve el censo mas `sin_resolver`: lazos impares o que se doblan."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    if soldar:
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=soldar)
    pares = _emparejar(bm)
    bm.normal_update()
    sin, hechas = [], 0
    for v in [v for v in bm.verts if len(v.link_faces) >= 5]:
        if not v.is_valid:
            continue
        lazo = _lazo_de(v)
        if not lazo:
            continue
        if len(lazo) % 2:
            sin.append(("polo impar", len(lazo)))
            continue
        normal = Vector(v.normal)
        apice = v.co.copy()
        suave = all(f.smooth for f in v.link_faces)
        mat = v.link_faces[0].material_index
        P = np.array([w.co[:] for w in lazo])
        plano = abs(float((np.asarray(apice) - P.mean(0)) @ np.asarray(normal))) < 1e-7
        antes = set(bm.faces)
        bmesh.ops.delete(bm, geom=[v], context="VERTS")
        vivos = set(bm.faces)
        r = _tapar(bm, lazo, normal, None if plano else apice)
        if r is None:
            r = _tapar_con_aro(bm, lazo, normal, None if plano else apice)
        if r is None:
            sin.append(("polo que se dobla", len(lazo)))
            bmesh.ops.contextual_create(bm, geom=lazo)
        for f in set(bm.faces) - vivos:
            f.smooth, f.material_index = suave, mat
        hechas += 1
    bm.normal_update()
    for f in [f for f in bm.faces if len(f.verts) > 4]:
        lazo = f.verts[:]
        if len(lazo) % 2:
            sin.append(("tapa impar", len(lazo)))
            continue
        normal, suave, mat = Vector(f.normal), f.smooth, f.material_index
        vivos = set(bm.faces)
        bm.faces.remove(f)
        vivos.discard(f)
        r = _tapar(bm, lazo, normal)
        if r is None:
            r = _tapar_con_aro(bm, lazo, normal)
        if r is None:
            sin.append(("tapa que se dobla", len(lazo)))
            bm.faces.new(lazo)
        for g in set(bm.faces) - vivos:
            g.smooth, g.material_index = suave, mat
        hechas += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    c = censo(ob)
    c.update(rejillas=hechas, sin_resolver=sin, emparejados=pares)
    return c


def tramar(ob, aspecto=40.0, pasadas=200, crecer=6.0):
    """Parte los quads de mas de `aspecto`:1 metiendo lazos a traves de su lado
    largo (se divide el anillo entero, asi que todo sigue en quads). Sustituye a
    `lowpoly.trocear`, que cortaba con planos y dejaba triangulos. Se detiene si
    la malla pasa de `crecer` veces sus caras: una tira de 0.5 mm de ancho en un
    marco de 300 mm lo llevo a 20 000 caras persiguiendo el aspecto."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = 0
    tope = max(200, len(bm.faces) * crecer)
    for _ in range(pasadas):
        if len(bm.faces) > tope:
            break
        peor, arista = aspecto, None
        for f in bm.faces:
            if len(f.verts) != 4:
                continue
            ls = [e.calc_length() for e in f.edges]
            a, b = max(ls[0], ls[2]), max(ls[1], ls[3])
            corto = max(min(a, b), 1e-9)
            r = max(a, b) / corto
            if r > peor:
                peor, arista = r, f.edges[0 if a >= b else 1]
        if arista is None:
            break
        cortes = max(1, min(int(math.ceil(peor / (aspecto * 0.6))) - 1, 24))
        bmesh.ops.subdivide_edges(bm, edges=_anillo(arista), cuts=cortes, use_grid_fill=True)
        n += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n


def _dentro(arbol, p):
    """Punto dentro de una malla cerrada: paridad de cruces en tres rayos."""
    votos = 0
    for d in ((0.5377, 0.2811, 0.7949), (-0.6124, 0.7071, -0.3536), (0.1826, -0.9129, 0.3651)):
        d = Vector(d)
        o, k = Vector(p), 0
        while k < 64:
            h = arbol.ray_cast(o, d)
            if h[0] is None:
                break
            k += 1
            o = h[0] + d * 1e-6
        votos += k % 2
    return votos >= 2


def quitar_ocultas(solidos, eps=0.05 * MM, tol=0.02 * MM):
    """Borra de cada solido las caras que nadie puede ver porque quedan dentro
    de OTRO solido del mismo grupo, y las duplicadas (dos tapas coplanares que
    miran al mismo lado: se queda la del solido que la contiene). Una cara es
    oculta si sus nueve muestras (centro, vertices, medios de arista), sacadas
    `eps` hacia fuera, caen dentro de algun otro solido cerrado. El borde que
    queda abierto esta enterrado. Devuelve (ocultas, duplicadas)."""
    from mathutils.bvhtree import BVHTree
    datos = []
    for o in solidos:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bm.normal_update()
        cerrado = all(len(e.link_faces) == 2 for e in bm.edges)
        P = np.array([v.co[:] for v in bm.verts]) if bm.verts else np.zeros((1, 3))
        datos.append(dict(bm=bm, arbol=BVHTree.FromBMesh(bm), lo=P.min(0) - 2 * tol, hi=P.max(0) + 2 * tol, cerrado=cerrado))
    n = len(solidos)
    ocultas = [set() for _ in range(n)]
    coinc = {}
    for i, d in enumerate(datos):
        otros = [j for j in range(n) if j != i and np.all(datos[j]["lo"] <= d["hi"]) and np.all(d["lo"] <= datos[j]["hi"])]
        if not otros:
            continue
        cache = {}

        def dentro(p, clave=None):
            if clave is not None and clave in cache:
                return cache[clave]
            r = False
            for j in otros:
                e = datos[j]
                if e["cerrado"] and all(e["lo"][k] < p[k] < e["hi"][k] for k in range(3)) and _dentro(e["arbol"], p):
                    r = True
                    break
            if clave is not None:
                cache[clave] = r
            return r
        for f in d["bm"].faces:
            nrm = f.normal
            pts = [f.calc_center_median()] + [v.co for v in f.verts] + [(e.verts[0].co + e.verts[1].co) / 2 for e in f.edges]
            if all(dentro(p + nrm * eps) for p in pts):
                ocultas[i].add(f.index)
                continue
            for j in otros:
                e = datos[j]
                ok = True
                for p in pts:
                    h = e["arbol"].find_nearest(p, tol)
                    if h[0] is None or h[1].dot(nrm) < 0.95:
                        ok = False
                        break
                if ok:
                    coinc.setdefault((i, j), []).append(f)
    dup = [set() for _ in range(n)]
    for (i, j), fs in coinc.items():
        if i > j and (j, i) in coinc:
            continue
        a = sum(f.calc_area() for f in fs)
        gs = coinc.get((j, i), [])
        b = sum(f.calc_area() for f in gs)
        if a > b * 1.001 or (abs(a - b) <= b * 0.001 and i > j) or not gs:
            dup[i].update(f.index for f in fs)
        else:
            dup[j].update(f.index for f in gs)
    tot_o = tot_d = 0
    for i, o in enumerate(solidos):
        quitar = ocultas[i] | dup[i]
        datos[i]["bm"].free()
        if not quitar or len(quitar) >= len(o.data.polygons):
            continue
        tot_o += len(ocultas[i])
        tot_d += len(dup[i] - ocultas[i])
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[k] for k in quitar], context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    return tot_o, tot_d


def ensamblar(nombre, solidos, cortes=(), aspecto=40.0, ocultas=True):
    """Low poly de una pieza de fundicion SIN booleano: los mismos solidos que
    `lowpoly.union_mecanizada`, cada uno cuadrado por separado y unidos en un
    objeto donde se cruzan. La silueta es la de la union; lo que cambia es que
    no hay arista compartida en los encuentros. Las caras enterradas del todo
    en otro solido se borran (`quitar_ocultas`). Los `cortes` se descartan: lo
    que deba cambiar la silueta se construye ya en los solidos (perfil con
    hueco, `prisma_anillo`, `ventana`)."""
    for c in cortes:
        d = c.data
        bpy.data.objects.remove(c)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    sin = []
    for o in solidos:
        r = cuadrar(o)
        if r["sin_resolver"] or r["tris"] or r["ngonos"]:
            sin.append((o.name, r["sin_resolver"], r["tris"], r["ngonos"]))
        if aspecto:
            tramar(o, aspecto)
    quitadas = list(quitar_ocultas(solidos)) if ocultas and len(solidos) > 1 else [0, 0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in solidos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = solidos[0]
    if len(solidos) > 1:
        bpy.ops.object.join()
    ob = solidos[0]
    ob.name = ob.data.name = nombre
    ob["sin_resolver"] = str(sin)
    ob["ocultas"] = quitadas
    return ob


# ------------------------------------------------------------------ remallado en quads

def retopo(ob, caras, vivos=None, semilla=0, contorno=True, suavizar=0, escala=1.0):
    """Remalla `ob` en ~`caras` quads con QuadriFlow. `vivos` (grados): marca
    como vivas las aristas de mas de ese angulo y las conserva. Para piezas
    organicas (madera tallada, tela, goma); en mecanica deja los cantos
    ondulados y hay que comprobar la silueta.

    `escala`: QuadriFlow da por no estanca ("the mesh needs to be manifold") cualquier malla con una arista de menos
    de 0.1 mm, aunque sea estanca: es su prueba de aristas de longitud cero, con tolerancia fija de 1e-4 unidades. Una
    pieza pequena medida en metros (un martillo de 40 mm con 20 000 caras) la incumple siempre. Con `escala=100` se
    remalla cien veces mayor y se devuelve a su tamano."""
    from mathutils import Matrix
    if escala != 1.0:
        ob.data.transform(Matrix.Scale(escala, 4))
        ob.data.update()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    if vivos is not None:
        for p in ob.data.polygons:
            p.use_smooth = True
        ob.data.set_sharp_from_angle(angle=math.radians(vivos))
    r = bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False, use_preserve_sharp=vivos is not None,
                                        use_preserve_boundary=contorno, preserve_attributes=False, smooth_normals=False,
                                        mode="FACES", target_faces=int(caras), seed=semilla)
    if escala != 1.0:
        ob.data.transform(Matrix.Scale(1.0 / escala, 4))
        ob.data.update()
    c = censo(ob)
    c["quadriflow"] = list(r)
    return c


def ajustar(ob, sobre, solo=None, mezcla=1.0):
    """Lleva cada vertice de `ob` al punto mas cercano de las mallas `sobre`
    (el high poly). Una jaula de quads construida con cotas aproximadas queda
    asi pegada a la forma real sin cambiar su topologia. `solo(co) -> bool`
    limita que vertices se mueven. Devuelve el desplazamiento maximo y medio (mm)."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for o in sobre:
        o = bpy.data.objects[o] if isinstance(o, str) else o
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    arbol = BVHTree.FromBMesh(bm)
    d = []
    inv = ob.matrix_world.inverted()
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co
        if solo and not solo(w):
            continue
        co, _, _, dist = arbol.find_nearest(w)
        if co is None:
            continue
        v.co = inv @ w.lerp(co, mezcla)
        d.append(dist)
    bm.free()
    ob.data.update()
    return {"max_mm": round(max(d) * 1000, 2) if d else 0, "media_mm": round(sum(d) / max(1, len(d)) * 1000, 2), "movidos": len(d)}


def desvio(ob, sobre, tope=2.0):
    """Distancia (mm) de los centros de cara y de arista de `ob` a las mallas
    `sobre`. Los vertices de una jaula ajustada estan sobre el high poly, pero
    sus cuerdas no: una cara que se hunde mas que la extrusion del horneado
    sale negra. Devuelve p50, p95, maximo y cuantas muestras pasan de `tope`."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for o in sobre:
        o = bpy.data.objects[o] if isinstance(o, str) else o
        if o.type != "MESH":
            continue
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    arbol = BVHTree.FromBMesh(bm)
    bm.free()
    b2 = bmesh.new()
    b2.from_mesh(ob.data)
    M = ob.matrix_world
    pts = [M @ f.calc_center_median() for f in b2.faces] + [M @ ((e.verts[0].co + e.verts[1].co) / 2) for e in b2.edges]
    b2.free()
    d = np.array([arbol.find_nearest(p)[3] or 0.0 for p in pts]) * 1000
    return {"p50_mm": round(float(np.percentile(d, 50)), 2), "p95_mm": round(float(np.percentile(d, 95)), 2),
            "max_mm": round(float(d.max()), 2), "sobre_tope": int((d > tope).sum()), "muestras": len(d)}


# ------------------------------------------------------------------ huecos en una rejilla

def ventana(ob, dentro, fondo, soldar=0.0):
    """Abre un rebaje en una malla de quads: borra las caras cuyo centro cumple
    `dentro(centro, normal)` y hunde el borde del hueco hasta `fondo(co) -> co`,
    cerrandolo con las mismas caras desplazadas. Todo sigue en quads y estanco.
    Devuelve cuantas caras se hundieron."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    caras = [f for f in bm.faces if dentro(f.calc_center_median(), f.normal)]
    if not caras:
        bm.free()
        return 0
    r = bmesh.ops.extrude_face_region(bm, geom=caras)
    nuevos = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    for v in nuevos:
        v.co = Vector(fondo(v.co))
    bmesh.ops.delete(bm, geom=[f for f in caras if f.is_valid], context="FACES")
    if soldar:
        bmesh.ops.remove_doubles(bm, verts=nuevos, dist=soldar)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return len(caras)


def bloque(nombre, x, y, z, coleccion, rebajes=(), tol=0.4 * MM):
    """Bloque mecanizado sin booleano: una caja con rejilla (`formas.caja_rejilla`)
    cuyos lazos caen en los bordes de cada rebaje, y los rebajes abiertos con
    `ventana`. `x`, `y`, `z`: (minimo, maximo) en metros. Cada rebaje:

        {"cara": "-Y", "rect": (a0, a1, b0, b1), "fondo": profundidad}
        {"cara": "+Z", "centro": (a, b), "r": radio, "fondo": profundidad}

    `a`, `b` son los dos ejes del plano de la cara, en orden XYZ (cara +-Y:
    x, z). El rebaje redondo sale octogonal (el mapa de normales lo redondea).
    Con "pasante": True el rebaje atraviesa el bloque (no hace falta "fondo"):
    se hunde hasta la cara opuesta y se borran su suelo y las caras de enfrente,
    que coinciden porque la rejilla es la misma en las dos caras.
    Las cotas a menos de `tol` de un lazo ya existente se llevan a el: dos
    lazos a 0.1 mm dejan una tira de caras de 300:1."""
    import formas
    lim = [tuple(x), tuple(y), tuple(z)]
    lineas = [list(l) for l in lim]

    def anadir(eje, v):
        if lim[eje][0] + tol < v < lim[eje][1] - tol and all(abs(v - w) >= tol for w in lineas[eje]):
            lineas[eje].append(v)

    def cerca(eje, v):
        return min(lineas[eje], key=lambda w: abs(w - v))
    prep = []
    for r in rebajes:
        n = "XYZ".index(r["cara"][1])
        sg = -1.0 if r["cara"][0] == "-" else 1.0
        a, b = [k for k in range(3) if k != n]
        if "r" in r:
            ca, cb = r["centro"]
            R, k = r["r"], r["r"] * 0.41421356
            la, lb = [ca - R, ca - k, ca + k, ca + R], [cb - R, cb - k, cb + k, cb + R]
        else:
            la, lb = list(r["rect"][:2]), list(r["rect"][2:])
        for v in la:
            anadir(a, v)
        for v in lb:
            anadir(b, v)
        prep.append((n, sg, a, b, la, lb, r))
    ob = formas.caja_rejilla(nombre, sorted(lineas[0]), sorted(lineas[1]), sorted(lineas[2]), coleccion)
    hechos = 0
    for n, sg, a, b, la, lb, r in prep:
        la, lb = [cerca(a, v) for v in la], [cerca(b, v) for v in lb]
        p = lim[n][1] if sg > 0 else lim[n][0]
        q_ = lim[n][0] if sg > 0 else lim[n][1]          # cara opuesta
        pasante = bool(r.get("pasante"))
        hondo = abs(p - q_) if pasante else r["fondo"]
        if "r" in r:                    # las cuatro esquinas del cuadrado pasan a la diagonal del octogono
            ca, cb = (la[0] + la[-1]) / 2, (lb[0] + lb[-1]) / 2
            ra, rb = (la[-1] - la[0]) / 2 * 0.70710678, (lb[-1] - lb[0]) / 2 * 0.70710678
            for v in ob.data.vertices:
                en_cara = abs(v.co[n] - p) < 1e-7 or (pasante and abs(v.co[n] - q_) < 1e-7)
                if en_cara and min(abs(v.co[a] - la[0]), abs(v.co[a] - la[-1])) < 1e-7 \
                        and min(abs(v.co[b] - lb[0]), abs(v.co[b] - lb[-1])) < 1e-7:
                    v.co[a] = ca + (ra if v.co[a] > ca else -ra)
                    v.co[b] = cb + (rb if v.co[b] > cb else -rb)

        def dentro(c, nrm, n=n, sg=sg, a=a, b=b, la=la, lb=lb, p=p):
            return nrm[n] * sg > 0.9 and abs(c[n] - p) < 1e-6 and la[0] < c[a] < la[-1] and lb[0] < c[b] < lb[-1]

        def fondo(co, n=n, sg=sg, p=p, f=hondo):
            q = Vector(co)
            q[n] = p - sg * f
            return q
        hechos += 1 if ventana(ob, dentro, fondo) else 0
        if pasante:
            # el suelo del rebaje coincide con las caras de enfrente (misma rejilla): se borran ambos
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bm.normal_update()
            quitar = []
            for f in bm.faces:
                c = f.calc_center_median()
                if abs(c[n] - q_) < 1e-6 and abs(f.normal[n]) > 0.9 and la[0] < c[a] < la[-1] and lb[0] < c[b] < lb[-1]:
                    quitar.append(f)
            bmesh.ops.delete(bm, geom=quitar, context="FACES")
            junto = [v for v in bm.verts if abs(v.co[n] - q_) < 1e-6 and la[0] - 1e-6 < v.co[a] < la[-1] + 1e-6
                     and lb[0] - 1e-6 < v.co[b] < lb[-1] + 1e-6]
            bmesh.ops.remove_doubles(bm, verts=junto, dist=1e-6)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            bm.to_mesh(ob.data)
            bm.free()
            ob.data.update()
    ob["rebajes"] = "%d de %d" % (hechos, len(prep))
    return ob


# ------------------------------------------------------------------ lamina de control

def lamina(nombres, ruta, desde=(-1.0, -0.6, 0.45), ancho=2000, grosor=0.00035, centro=None, radio=None):
    """Render rapido (Workbench) de la malla con sus aristas REALES, para mirar
    la topologia sin depender del visor. `desde`: direccion hacia la camara."""
    esc = bpy.context.scene
    obs = [bpy.data.objects[n] if isinstance(n, str) else n for n in nombres]
    previo = {o: o.hide_render for o in esc.objects}
    tmp = []
    for o in esc.objects:
        o.hide_render = True
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for o in obs:
        for tipo in ("solido", "malla"):
            d = o.copy()
            d.data = o.data.copy()
            esc.collection.objects.link(d)
            d.hide_render = False
            d.hide_set(False)
            d.data.materials.clear()
            if tipo == "malla":
                m = d.modifiers.new("w", "WIREFRAME")
                m.thickness, m.use_replace = grosor, True
                d.color = (0.02, 0.02, 0.02, 1)
            else:
                d.color = (0.78, 0.78, 0.76, 1)
            tmp.append(d)
        P = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        lo, hi = np.minimum(lo, P.min(0)), np.maximum(hi, P.max(0))
    cen, rad = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
    if centro is not None:
        cen, rad = np.asarray(centro, float), radio
    cd = bpy.data.cameras.new("_cam_q")
    cam = bpy.data.objects.new("_cam_q", cd)
    esc.collection.objects.link(cam)
    d = Vector(desde).normalized()
    cam.location = Vector(cen) + d * 3.0
    cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    cd.type, cd.ortho_scale, cd.clip_end = "ORTHO", rad * 2.1, rad * 10 + 10
    g = dict(cam=esc.camera, eng=esc.render.engine, x=esc.render.resolution_x, y=esc.render.resolution_y,
             p=esc.render.resolution_percentage, f=esc.render.filepath, t=esc.render.film_transparent)
    esc.camera, esc.render.engine = cam, "BLENDER_WORKBENCH"
    esc.render.resolution_x, esc.render.resolution_y, esc.render.resolution_percentage = ancho, int(ancho * 0.62), 100
    sh = esc.display.shading
    sh.light, sh.color_type, sh.show_cavity = "STUDIO", "OBJECT", False
    esc.render.film_transparent = False
    esc.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    esc.camera, esc.render.engine = g["cam"], g["eng"]
    esc.render.resolution_x, esc.render.resolution_y, esc.render.resolution_percentage = g["x"], g["y"], g["p"]
    esc.render.filepath, esc.render.film_transparent = g["f"], g["t"]
    for d in tmp + [cam]:
        dat = d.data
        bpy.data.objects.remove(d)
        if dat.users == 0:
            (bpy.data.cameras if isinstance(dat, bpy.types.Camera) else bpy.data.meshes).remove(dat)
    for o, h in previo.items():
        o.hide_render = h
    return ruta
