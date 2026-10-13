"""Piezas con UV ANALITICA: lofts, cintas barridas y placas cuya UV se escribe al construirlas en vez de fiarla al
desplegador. Nacio en la katana (prop 11): las cintas del encintado, retorcidas, se pisaban al desplegarse y el
refinado las trituraba; la vaina y la hoja, desarrollables, salian torcidas; las tablas del soporte se solapaban.

Cada pieza guarda en el atributo de esquina `uva` su (u, v) en METROS reales (y en la tercera componente la coordenada
a traves de una cinta, -1..1) y marca sus caras con `cosida`. Despues del despliegue automatico del resto,
`prep.uv_analitica(objeto)` copia `uva` a la capa UV, iguala escalas y empaqueta.

Unidades de entrada: MILIMETROS (se convierten al crear la malla). Todo sale en quads.
"""
import math

import bmesh
import bpy
import numpy as np

import formas as F

MM = F.MM


def suave(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def loft(nombre, secciones, col, suave=True):
    return F.loft(nombre, [np.asarray(s, float) * MM for s in secciones], col, suave)


def casar(me, P, tol=2e-6):
    """Indice canonico de cada vertice de la malla entre los puntos `P` (metros): el del punto mas cercano, y el mismo
    para todos los puntos que coinciden. Por arbol k-d: casar por coordenadas redondeadas fallaba en una de cada
    muchas caras (la malla guarda float32 y el redondeo cae a veces del otro lado)."""
    from mathutils.kdtree import KDTree
    kd = KDTree(len(P))
    for i, c in enumerate(P):
        kd.insert(c, i)
    kd.balance()
    canon = [min(j for _, j, _ in kd.find_range(c, tol)) for c in P]
    out = []
    for v in me.vertices:
        _, i, d = kd.find(v.co)
        out.append(canon[i] if d < 2e-5 else None)
    return canon, out
HUECO = 0.004                               # separacion (m) entre trozos de una misma pieza en su UV analitica


def escribir_uva(ob, datos, atributo="uva"):
    """UV ANALITICA de una pieza de la low poly: `datos` = caras, cada una [(punto en metros, (u, v, c)), ...]. Se
    guarda en el atributo de esquina `uva` (u, v en metros reales; c = coordenada a traves de una cinta, -1..1) y la
    cara se marca `cosida`. `preparar_sp.uv_analitica` la copia a la capa UV despues del despliegue automatico: una
    hoja, una vaina o una cinta barrida tienen un desarrollo exacto que el desplegador no acierta (las cintas del
    encintado, retorcidas, se pisaban a si mismas y el refinado las trituraba)."""
    P = [c for cara in datos for c, _ in cara]
    me = ob.data
    canon, de_malla = casar(me, P)
    tabla, k = {}, 0
    for cara in datos:
        ids = canon[k: k + len(cara)]
        tabla[frozenset(ids)] = {i: uv for i, (_, uv) in zip(ids, cara)}
        k += len(cara)
    at = me.attributes.get(atributo) or me.attributes.new(atributo, "FLOAT_VECTOR", "CORNER")
    n = 0
    marcas = [False] * len(me.polygons)
    for pl in me.polygons:
        ks = [de_malla[v] for v in pl.vertices]
        t = tabla.get(frozenset(ks)) if None not in ks else None
        if t is None:
            continue
        for li, k in zip(pl.loop_indices, ks):
            at.data[li].vector = t[k]
        marcas[pl.index] = True
        n += 1
    if atributo == "uva":
        car = me.attributes.get("cosida") or me.attributes.new("cosida", "BOOLEAN", "FACE")
        car.data.foreach_set("value", marcas)
    return n


def marca(ob, V, n, m, js, cada=0, cortes=(), a_traves=None, ultimo=None):
    """Costura y UV analitica de un loft de `n` secciones de `m` puntos (`V`, en metros): se abre por las generatrices
    `js` y se parte en las secciones `cortes` (o cada `cada`). u = longitud a lo largo; v = desarrollo de la seccion."""
    me = ob.data
    canon, de_malla = casar(me, [tuple(c) for c in np.asarray(V, float).reshape(-1, 3)])
    ij = [None if k is None else (k // m, k % m) for k in de_malla]
    cortes = sorted(set(cortes) | {i for i in range(1, n - 1) if cada and i % cada == 0})

    def es(a, b):
        if not (ij[a] and ij[b]):
            return False
        (ia, ja), (ib, jb) = ij[a], ij[b]
        if ja == jb and ia != ib:
            return ja in js
        return ia == ib and ia in cortes
    cos = me.attributes.new("costura", "BOOLEAN", "EDGE")
    cos.data.foreach_set("value", [es(a, b) for a, b in (e.vertices for e in me.edges)])
    G = np.asarray(V, float).reshape(n, m, 3)
    j0 = min(js)
    orden = [(j0 + k) % m for k in range(m)]
    sig = orden[1:] + orden[:1]
    cum = np.concatenate([np.zeros((n, 1)), np.cumsum(np.linalg.norm(G[:, sig] - G[:, orden], axis=2), 1)], 1)
    u = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(G, axis=0), axis=2).mean(1))])
    c = (lambda j: float(a_traves[j])) if a_traves is not None else (lambda j: 0.0)
    datos = []
    for i in range(n - 1 if ultimo is None else ultimo):     # de `ultimo` en adelante (un remate en cupula) despliega el automatico
        so = HUECO * sum(1 for x in cortes if x <= i)
        for k in range(m):
            ja, jb = orden[k], sig[k]
            bo = HUECO * sum(1 for j in js if j != j0 and ((j - j0) % m) <= k)
            datos.append([(G[i, ja], (u[i] + so, cum[i, k] + bo, c(ja))), (G[i, jb], (u[i] + so, cum[i, k + 1] + bo, c(jb))),
                          (G[i + 1, jb], (u[i + 1] + so, cum[i + 1, k + 1] + bo, c(jb))), (G[i + 1, ja], (u[i + 1] + so, cum[i + 1, k] + bo, c(ja)))])
    escribir_uva(ob, datos)


def perfil_cinta(fino):
    """Seccion unitaria de una cinta trenzada: x en [-1, 1] (medio ancho), y en [0, 1] (grueso). La base va hundida."""
    if not fino:
        return np.array([(-1.0, 0.0), (1.0, 0.0), (0.82, 1.0), (-0.82, 1.0)])
    arr = [(-1.0, 0.0), (1.0, 0.0)]
    for a in np.linspace(0.0, math.pi, 11):
        c, s = math.cos(a), math.sin(a)
        g = (abs(c) ** 3.2 + abs(s) ** 3.2) ** (-1 / 3.2)
        arr.append((g * c, 0.34 + 0.66 * g * s))
    return np.array(arr)


def cinta(nombre, P, N, w, t, fino, col, hundir=0.35, cada=0):
    """Cinta de ancho `w` y grueso `t` (por punto) a lo largo de `P` (mm), con `N` la normal de la superficie en cada
    punto. Loft cerrado; en la low poly lleva su costura: la cara de abajo en una isla y el resto en una tira."""
    P, N = np.asarray(P, float), np.asarray(N, float)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = N - np.sum(N * T, 1, keepdims=True) * T
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    S = np.cross(T, N)
    pf = perfil_cinta(fino)
    w, t = np.broadcast_to(np.asarray(w, float), (len(P),)), np.broadcast_to(np.asarray(t, float), (len(P),))
    sec = P[:, None, :] + S[:, None, :] * (pf[None, :, 0, None] * w[:, None, None] / 2) \
        + N[:, None, :] * (pf[None, :, 1, None] * (t[:, None, None] + hundir) - hundir)
    ob = loft(nombre, list(sec), col)
    if not fino:
        marca(ob, (sec * MM).reshape(-1, 3), len(P), len(pf), {0, 1}, cada, a_traves=pf[:, 0])
    return ob


def elipsoide(nombre, centro, ejes, radios, n, m, col):
    """Elipsoide (o media: el eje w se aplasta) con `ejes` = (u, v, w) ortonormales en el mundo y `radios` en mm."""
    ob = F.revolucion(nombre, [(math.sin(a), -math.cos(a)) for a in np.linspace(0, math.pi, m)], n, (0, 0, 0), "Z", col)
    u, v, w = (np.asarray(e, float) for e in ejes)
    co = np.array([x.co[:] for x in ob.data.vertices])
    out = np.asarray(centro, float)[None] + co[:, :1] * radios[0] * u + co[:, 1:2] * radios[1] * v + co[:, 2:] * radios[2] * w
    ob.data.vertices.foreach_set("co", (out * MM).ravel())
    ob.data.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def placa(nombre, G, punto, w0, w1, col, nw=1, uva=False, ident=0.0, escala_abajo=1.0, desarrollo=False):
    """Placa cerrada de grueso w0..w1 cuya cara es la rejilla `G` (nu, nv, 2) de puntos (u, v). `punto(u, v, w)` da el
    punto del mundo (mm). Todo quads: dos caras en rejilla y el canto. `uva`: escribe su UV analitica (las dos caras
    son su proyeccion plana exacta; el canto, tiras rectas partidas cada 0,2 m). `ident`: numero de pieza que se guarda
    en la tercera componente de `uva` (+ident en la cara w1, la vista; -ident en la w0), para que `prep.arte_uva`
    sepa a que pieza pertenece cada texel. `escala_abajo`: reduce la UV de la cara w0 cuando no se ve (apoyada en otra).
    `desarrollo`: la cara es un campo de alturas con paredes (la campana y la teja de una silla); su patron plano deja
    esas paredes casi sin texeles. Se escribe ademas `uvd`: u = longitud recorrida a lo largo de las filas (la misma en
    todas, para que la rejilla no se pliegue), v = a lo largo de cada columna, medidas sobre la malla. `prep.uv_analitica` usa `uvd` para el atlas y `uva` sigue siendo el
    patron donde se dibuja el arte."""
    G = np.asarray(G, float)
    nu, nv = G.shape[0], G.shape[1] - 1
    V, idx = [], {}

    def v(i, j, k):
        if (i, j, k) not in idx:
            idx[(i, j, k)] = len(V)
            V.append(punto(G[i, j, 0], G[i, j, 1], w0 + (w1 - w0) * k / nw))
        return idx[(i, j, k)]
    caras, datos, datos_d = [], [], []
    for k in (0, nw):
        e, z = (escala_abajo, -ident) if k == 0 else (1.0, ident)
        g = lambda i, j: (G[i, j, 0] * MM * e, G[i, j, 1] * MM * e, z)
        if desarrollo:
            Pk = np.array([[V[v(i, j, k)] for j in range(nv + 1)] for i in range(nu)]) * MM
            paso = np.linalg.norm(np.diff(Pk, axis=0), axis=2)
            # el mismo avance para todas las filas de una estacion (entre el medio y el de la fila que mas sube): con el
            # avance propio de cada fila, las del centro (que trepan la campana) y las del borde se pisaban en el atlas
            paso = (0.4 * paso.mean(1) + 0.6 * paso.max(1))[:, None] * np.ones((1, nv + 1))
            du = np.concatenate([np.zeros((1, nv + 1)), np.cumsum(paso, 0)], 0)
            dv = np.concatenate([np.zeros((nu, 1)), np.cumsum(np.linalg.norm(np.diff(Pk, axis=1), axis=2), 1)], 1)
            dv = dv - dv[:, -1:] / 2
            gd = lambda i, j: (du[i, j] * e, dv[i, j] * e + (0.0 if k else 50.0), 1.0)
        for i in range(nu - 1):
            for j in range(nv):
                q = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                caras.append(tuple(v(a, b, k) for a, b in q))
                datos.append([(np.array(V[v(a, b, k)]) * MM, g(a, b)) for a, b in q])
                if desarrollo:
                    datos_d.append([(np.array(V[v(a, b, k)]) * MM, gd(a, b)) for a, b in q])
    gr = abs(w1 - w0) * MM / nw

    def tira(lazo, banda):
        """Canto a lo largo de `lazo` = [(i, j), ...]: una tira recta, partida cada 0,2 m."""
        P = np.array([G[i, j] for i, j in lazo]) * MM
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        for k in range(nw):
            for t in range(len(lazo) - 1):
                (ia, ja), (ib, jb) = lazo[t], lazo[t + 1]
                caras.append((v(ia, ja, k), v(ib, jb, k), v(ib, jb, k + 1), v(ia, ja, k + 1)))
                so = HUECO * int(0.5 * (L[t] + L[t + 1]) / 0.2) + banda * 10.0
                datos.append([(np.array(V[v(ia, ja, k)]) * MM, (L[t] + so, gr * k, 0.0)), (np.array(V[v(ib, jb, k)]) * MM, (L[t + 1] + so, gr * k, 0.0)),
                              (np.array(V[v(ib, jb, k + 1)]) * MM, (L[t + 1] + so, gr * (k + 1), 0.0)), (np.array(V[v(ia, ja, k + 1)]) * MM, (L[t] + so, gr * (k + 1), 0.0))])
    tira([(i, 0) for i in range(nu)], 1)
    tira([(i, nv) for i in range(nu)], 2)
    tira([(0, j) for j in range(nv + 1)], 3)
    tira([(nu - 1, j) for j in range(nv + 1)], 4)
    ob = F._objeto(nombre, np.array(V) * MM, caras, col, suave=False)
    if uva:
        escribir_uva(ob, datos)
        if desarrollo:
            escribir_uva(ob, datos_d, "uvd")
    return ob


def losa(nombre, us, lo, hi, nv, punto, w0, w1, col, nw=1, uva=False, ident=0.0, escala_abajo=1.0, filas=None, desarrollo=False):
    """Losa entre dos curvas: para cada `u` de `us`, la cara va de lo(u) a hi(u) en `nv` tramos."""
    us = np.asarray(us, float)
    t = np.linspace(0, 1, nv + 1) if filas is None else np.asarray(filas, float)      # `filas`: fracciones 0..1 propias (mas juntas donde la hoja se curva)
    G = np.stack([np.repeat(us[:, None], len(t), 1), lo(us)[:, None] * (1 - t)[None] + hi(us)[:, None] * t[None]], -1)
    return placa(nombre, G, punto, w0, w1, col, nw, uva, ident, escala_abajo, desarrollo)


def fundida(ob, voxel, suavizado=3):
    """Mata los cantos de una pieza de madera: remallado por voxeles y suavizado (radio ~ voxel * raiz(suavizado))."""
    return F.fundir(ob.name, [ob], voxel * MM, suavizado=suavizado)


def bisel(ob, ancho_mm, tramos=3, angulo=50.0):
    """Mata los cantos vivos de una placa del HIGH POLY (el canto bruñido de un cuero grueso, el de una tabla): bisel
    redondo en las aristas de mas de `angulo` grados. Sobre una rejilla de quads sale limpio; no usa voxeles.
    Las celdas de la rejilla tienen que ser mas anchas que el bisel: en celdas de decimas deja aristas minimas, y
    limpiarlas despues (soldar o colapsar) rompio la estanqueidad dos veces (casco y acion de la silla)."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("Bisel", "BEVEL")
    m.width, m.segments, m.limit_method, m.angle_limit = ancho_mm * MM, tramos, "ANGLE", math.radians(angulo)
    m.harden_normals = False
    bpy.ops.object.modifier_apply(modifier=m.name)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob
