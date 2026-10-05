"""Material blando: bolsas de tela infladas, cinchas y pliegues por simulacion.

Orden de una pieza de tela:
1. `bolsa` (o cualquier malla cerrada y regular) -> el patron en grueso, con la
   forma del compartimento vacio.
2. `grupo` -> grupos de vertices: lo que queda fijo (panel de espalda, costuras a
   otra pieza), lo que encoge (costuras, cinchas) y lo que sobra (tela holgada).
3. `simular` -> presion interior + encogido; devuelve tiempos y deja la malla
   aplicada en el fotograma final.
4. `medir` -> cifras del resultado: caras cruzadas consigo misma, cambio de area,
   rugosidad. El ojo no distingue un pliegue de una malla que se atraviesa.

Unidades: metros. Ejes del lote: X lateral, -Y frente, Z arriba.
"""
import time

import bmesh
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

MM = 0.001

# rigidez por tipo de tejido: (tension, compresion, cizalla, flexion, masa por vertice kg)
TEJIDOS = {
    "cordura": (40.0, 40.0, 20.0, 4.0, 0.30),     # nailon 1000D: pliegues anchos, poco numerosos
    "lona": (80.0, 80.0, 40.0, 10.0, 0.40),       # lona encerada: casi carton
    "nailon_fino": (15.0, 15.0, 5.0, 0.5, 0.15),  # forro, funda de lluvia: arruga fina
    "cuero": (80.0, 80.0, 80.0, 25.0, 0.50),      # cuero curtido: se dobla, no se arruga
}


def bolsa(nombre, x, y, z, paso, coleccion, triangular=True, semilla=0):
    """Caja cerrada (x0,x1),(y0,y1),(z0,z1) mallada con aristas de ~`paso`.
    `triangular` parte los quads con diagonales alternas al azar: una rejilla de
    quads solo se pliega a lo largo de sus dos direcciones y el pliegue sale en
    escalera."""
    n = [max(2, int(round((b - a) / paso))) for a, b in (x, y, z)]
    ejes = [np.linspace(a, b, k + 1) for (a, b), k in zip((x, y, z), n)]
    verts, caras, idx = [], [], {}

    def v(i, j, k):
        c = (i, j, k)
        if c not in idx:
            idx[c] = len(verts)
            verts.append((ejes[0][i], ejes[1][j], ejes[2][k]))
        return idx[c]

    nx, ny, nz = n
    for i in range(nx):
        for j in range(ny):
            caras.append((v(i, j, 0), v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0)))
            caras.append((v(i, j, nz), v(i + 1, j, nz), v(i + 1, j + 1, nz), v(i, j + 1, nz)))
    for i in range(nx):
        for k in range(nz):
            caras.append((v(i, 0, k), v(i + 1, 0, k), v(i + 1, 0, k + 1), v(i, 0, k + 1)))
            caras.append((v(i, ny, k), v(i, ny, k + 1), v(i + 1, ny, k + 1), v(i + 1, ny, k)))
    for j in range(ny):
        for k in range(nz):
            caras.append((v(0, j, k), v(0, j, k + 1), v(0, j + 1, k + 1), v(0, j + 1, k)))
            caras.append((v(nx, j, k), v(nx, j + 1, k), v(nx, j + 1, k + 1), v(nx, j, k + 1)))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], caras)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if triangular:
        rng = np.random.default_rng(semilla)
        for f in bm.faces[:]:
            metodo = "FIXED" if rng.random() < 0.5 else "ALTERNATE"
            bmesh.ops.triangulate(bm, faces=[f], quad_method=metodo)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    bpy.data.collections[coleccion].objects.link(ob)
    return ob


def grupo(ob, nombre, peso):
    """Grupo de vertices desde `peso(co) -> 0..1` (co en coordenadas del objeto)."""
    g = ob.vertex_groups.get(nombre) or ob.vertex_groups.new(name=nombre)
    n = 0
    for vt in ob.data.vertices:
        w = float(peso(vt.co))
        if w > 0:
            g.add([vt.index], min(1.0, w), "REPLACE")
            n += 1
    return n


def simular(ob, tejido="cordura", presion=8.0, frames=40, fijo=None, encoge=None, encogido=(0.0, 0.0),
            gravedad=0.0, calidad=8, autocolision=False, distancia=1.5e-3, colisionadores=(), aplicar=True,
            amortiguacion=5.0):
    """Infla `ob` (malla cerrada) y deja el resultado aplicado.

    `fijo`: grupo de vertices clavados. `encoge`: grupo cuyo peso interpola el
    encogido entre `encogido[0]` (peso 0) y `encogido[1]` (peso 1); negativo =
    la tela CRECE (holgura), positivo = se frunce (costura, cincha).
    `colisionadores`: objetos contra los que choca (se les pone y se les quita
    el modificador de colision)."""
    sc = bpy.context.scene
    t0 = time.time()
    for c in colisionadores:
        if not any(m.type == "COLLISION" for m in c.modifiers):
            m = c.modifiers.new("_col", "COLLISION")
            c.collision.thickness_outer = distancia
            c.collision.cloth_friction = 15.0
    mod = ob.modifiers.new("_tela", "CLOTH")
    s = mod.settings
    te, co, ci, fl, masa = TEJIDOS[tejido]
    s.quality = calidad
    s.mass = masa
    s.tension_stiffness, s.compression_stiffness, s.shear_stiffness, s.bending_stiffness = te, co, ci, fl
    s.tension_damping = s.compression_damping = s.shear_damping = amortiguacion
    s.bending_damping = 0.5
    s.air_damping = 2.0
    s.use_pressure = presion != 0
    s.uniform_pressure_force = presion
    s.pressure_factor = 1.0
    s.effector_weights.gravity = gravedad
    if fijo:
        s.vertex_group_mass = fijo
        s.pin_stiffness = 1.0
    if encoge:
        s.vertex_group_shrink = encoge
    s.shrink_min, s.shrink_max = encogido
    c = mod.collision_settings
    c.use_collision = bool(colisionadores)
    c.distance_min = distancia
    c.use_self_collision = autocolision
    c.self_distance_min = distancia
    c.collision_quality = 3
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = frames
    sc.frame_start, sc.frame_end = 1, frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    seg = time.time() - t0
    if aplicar:
        dg = bpy.context.evaluated_depsgraph_get()
        nueva = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        vieja = ob.data
        ob.modifiers.remove(mod)
        ob.data = nueva
        nueva.name = vieja.name
        bpy.data.meshes.remove(vieja)
        for cl in colisionadores:
            for m in [m for m in cl.modifiers if m.name == "_col"]:
                cl.modifiers.remove(m)
        sc.frame_set(1)
    return {"s": round(seg, 1), "s_por_frame": round(seg / frames, 2), "verts": len(ob.data.vertices)}


def medir(ob, area_inicial=None):
    """Cifras de una piel de tela ya simulada."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    arbol = BVHTree.FromBMesh(bm, epsilon=0.0)
    cruces = set()
    bm.faces.ensure_lookup_table()
    for a, b in arbol.overlap(arbol):
        if a < b and not (set(v.index for v in bm.faces[a].verts) & set(v.index for v in bm.faces[b].verts)):
            cruces.add(a)
            cruces.add(b)
    area = sum(f.calc_area() for f in bm.faces)
    vol = bm.calc_volume(signed=False)
    # rugosidad: angulo diedro medio entre caras vecinas (grados); una bolsa lisa da < 2
    ang = [e.calc_face_angle(0.0) for e in bm.edges if len(e.link_faces) == 2]
    borde = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    lados = np.array([e.calc_length() for e in bm.edges])
    bm.free()
    out = {"caras": len(ob.data.polygons), "caras_cruzadas": len(cruces), "aristas_abiertas": borde,
           "area_cm2": round(area * 1e4, 1), "volumen_l": round(vol * 1e3, 2),
           "diedro_medio": round(float(np.degrees(np.mean(ang))), 2),
           "diedro_p95": round(float(np.degrees(np.percentile(ang, 95))), 2),
           "arista_mm": [round(float(lados.min() / MM), 2), round(float(np.median(lados) / MM), 2),
                         round(float(lados.max() / MM), 2)]}
    if area_inicial:
        out["area_pct"] = round(100 * (area / area_inicial - 1), 2)
    return out


# ------------------------------------------------------------------ cinchas

def _arbol(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    arbol = BVHTree.FromBMesh(bm)
    return arbol, bm


def arbol_de(objetos):
    """BVH de varios objetos juntos (la tela mas lo que ya lleva cosido encima):
    lo que se traza despues pasa POR ENCIMA de todo ello. Devuelve (arbol, bmesh);
    liberar el bmesh al terminar."""
    bm = bmesh.new()
    for ob in objetos:
        me = ob.data.copy()
        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    return BVHTree.FromBMesh(bm), bm


def apoyar(P, N, ancho, separacion, arbol, pasadas=4):
    """Levanta la polilinea lo justo para que una cinta de `ancho` no se hunda
    por los cantos: se traza por su eje, pero la tela es curva bajo todo su ancho."""
    from mathutils import Vector
    Tg = np.gradient(P, axis=0)
    Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-12
    S = np.cross(Tg, N)
    S /= np.linalg.norm(S, axis=1, keepdims=True) + 1e-12
    sube = np.zeros(len(P))
    for f in (-0.5, -0.3, 0.3, 0.5):
        for i in range(len(P)):
            q = P[i] + S[i] * f * ancho
            co, nr, _, _ = arbol.find_nearest(Vector(q))
            falta = separacion - float(np.dot(q - np.array(co), np.array(nr)))
            if falta > sube[i] and np.linalg.norm(q - np.array(co)) < 3 * ancho:
                sube[i] = falta
    for _ in range(pasadas):          # sin escalones: maximo con los vecinos y media
        m = sube.copy()
        m[1:-1] = np.maximum(sube[1:-1], 0.5 * (sube[:-2] + sube[2:]))
        sube = m
    return P + N * sube[:, None], float(sube.max())


def asentar(ob, arbol, n, holgura=0.2 * MM, alto=0.02):
    """Sube una pieza rigida a lo largo de `n` hasta que ningun vertice quede
    bajo la superficie. Mide con rayos lanzados desde `alto` por encima de cada
    vertice: la normal del punto mas cercano engana sobre dientes y cantos.
    Devuelve cuanto subio (m)."""
    from mathutils import Matrix, Vector
    n = Vector(n).normalized()
    peor = 0.0
    for v in ob.data.vertices:
        co, _, _, d = arbol.ray_cast(v.co + n * alto, -n)
        if co is not None and d < alto + holgura:
            peor = max(peor, alto + holgura - d)
    if peor > 0:
        ob.data.transform(Matrix.Translation(n * peor))
        ob.data.update()
    return peor


def trazar(superficie, guia, paso=3 * MM, separacion=0.6 * MM, tension=12, arbol=None, rayo=None, hacia=None,
           retroceso=None):
    """Lleva la polilinea `guia` (puntos 3D aproximados) a la superficie y la
    tensa. Devuelve (puntos, normales).

    Una cincha no baja al fondo de cada pliegue: va tirante entre los puntos
    altos. Por eso tras proyectar se suaviza `tension` veces y solo se devuelve
    a la superficie el punto que haya quedado POR DEBAJO de ella."""
    from mathutils import Vector
    G = np.asarray(guia, float)
    seg = np.linalg.norm(np.diff(G, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / paso)))
    t = np.linspace(0, s[-1], n + 1)
    P = np.stack([np.interp(t, s, G[:, k]) for k in range(3)], -1)
    libera = None
    if arbol is None:
        arbol, libera = _arbol(superficie)

    # `rayo`: direccion fija de proyeccion. El punto mas cercano resbala sobre una
    # superficie abombada y una fila horizontal sale ondulada; el rayo no.
    dr = None if rayo is None else Vector(rayo).normalized()

    # `hacia`: punto fijo al que apuntan los rayos (el eje de un bolsillo). Para
    # guias que rodean un bulto: el punto mas cercano salta al bulto vecino.
    # cuanto retrocede el origen del rayo. Hacia un punto fijo, poco: retroceder 80 mm desde
    # la guia de un bolsillo mete el origen DENTRO del bolsillo vecino y el rayo sale por el
    atras = retroceso if retroceso is not None else (0.012 if hacia is not None else 0.08)

    def proyecta(p):
        """(punto de la superficie, normal, direccion en la que se separa la cinta)."""
        d = dr
        if hacia is not None:
            d = (Vector(hacia) - Vector(p)).normalized()
        if d is not None:
            co, nr, _, _ = arbol.ray_cast(Vector(p) - d * atras, d)
            if co is not None:
                # con rayo, la cinta se separa CONTRA el rayo: separarla por la normal la hace
                # resbalar de lado un poco en cada pasada (4 mm en 40 pasadas sobre un bolsillo abombado)
                return np.array(co), np.array(nr), -np.array(d)
        co, nr, _, _ = arbol.find_nearest(Vector(p))
        return np.array(co), np.array(nr), np.array(nr)

    Q, N = np.zeros_like(P), np.zeros_like(P)
    for i, p in enumerate(P):
        c, nr, o = proyecta(p)
        Q[i], N[i] = c + o * separacion, nr
    for _ in range(tension):
        R = Q.copy()
        R[1:-1] = (Q[:-2] + 2 * Q[1:-1] + Q[2:]) / 4
        if dr is not None:
            # solo se tensa en profundidad: la fila no se mueve de su sitio
            R = Q + np.outer((R - Q) @ np.array(dr), np.array(dr))
        for i in range(1, len(R) - 1):
            c, nr, o = proyecta(R[i])
            if np.dot(R[i] - c, o) < separacion:
                R[i] = c + o * separacion
            N[i] = nr
        Q = R
    # normales suavizadas: una normal que salta de cara en cara retuerce la cinta
    for _ in range(6):
        N[1:-1] = N[:-2] + 2 * N[1:-1] + N[2:]
        N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    if libera is not None:
        libera.free()
    return Q, N


def cinta(nombre, puntos, normales, ancho, grueso, coleccion, canto=0.3 * MM):
    """Cinta de seccion rectangular (cantos redondeados) por `puntos`, con la
    cara ancha mirando a `normales`. La cara inferior queda en los puntos."""
    import formas as F
    # puntos casi repetidos (la guia de un cabo corto, un tramo levantado por `apoyar`) dan
    # caras de 0.01 mm de largo por 25 de ancho
    P, N = np.asarray(puntos, float), np.asarray(normales, float)
    deja = [0]
    for i in range(1, len(P)):
        if np.linalg.norm(P[i] - P[deja[-1]]) > 1.0 * MM or i == len(P) - 1:
            deja.append(i)
    if len(deja) > 2 and np.linalg.norm(P[deja[-1]] - P[deja[-2]]) < 1.0 * MM:
        deja.pop(-2)
    puntos, normales = P[deja], N[deja]
    # una cinta fina va a canto vivo: redondear 0.3 mm deja en la tapa un poligono con aristas
    # de 0.2 mm junto a otras de 25 (106:1)
    perfil = F.perfil_rect(ancho, grueso, min(canto, grueso * 0.45), 2) if grueso >= 2 * MM else F.perfil_rect(ancho, grueso)
    perfil = perfil + np.array([0.0, grueso / 2])
    return F.barrido(nombre, puntos, perfil, normales, coleccion)


def largo(P):
    """Abscisa curvilinea de cada punto de la polilinea."""
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def cincha(nombre, superficie, guia, ancho, grueso, coleccion, separacion=0.6 * MM, tension=12, arbol=None,
           onda=None, devolver=False, rayo=None, hacia=None, paso=3 * MM, pistas=5):
    """`trazar` + `cinta`: una cincha cosida sobre la tela. `onda` = (paso, alto):
    la cincha se despega `alto` entre costuras separadas `paso` (cincha portaequipo)."""
    libera = None
    if arbol is None:
        arbol, libera = _arbol(superficie)
    P, N = trazar(superficie, guia, paso=paso, separacion=separacion, tension=tension, arbol=arbol, rayo=rayo, hacia=hacia)
    if rayo is None:
        P, _ = apoyar(P, N, ancho, separacion, arbol)
    if rayo is not None:
        # fila cosida: se amolda a la tela tambien a lo ANCHO. Cinco trazas paralelas y una
        # cinta tendida entre ellas; una cinta rigida apoyada en lo mas alto flotaba varios mm
        # sobre un bolsillo abombado y el horneado dejaba agujeros negros
        d_ = np.asarray(rayo, float) / np.linalg.norm(rayo)
        G = np.asarray(guia, float)
        t = G[-1] - G[0]
        lado = np.cross(t / np.linalg.norm(t), -d_)
        fracciones = np.linspace(-0.5, 0.5, pistas)
        pistas = []
        for f in fracciones:
            Pk, _ = trazar(superficie, G + lado * f * ancho, paso=paso, separacion=separacion, tension=tension, arbol=arbol,
                           rayo=rayo)
            pistas.append(Pk)
        n = min(len(k) for k in pistas)
        pistas = [k[:n] for k in pistas]
        P = pistas[len(pistas) // 2]
        alza = np.zeros(n)
        if onda:
            alza = onda[1] * np.sin(np.pi * largo(P) / onda[0]) ** 2
        import formas as F
        secciones = []
        for i in range(n):
            abajo = [k[i] - d_ * alza[i] for k in pistas]
            arriba = [q - d_ * grueso for q in reversed(abajo)]
            secciones.append(np.array(abajo + arriba))
        ob = F.loft(nombre, secciones, coleccion)
        if libera is not None:
            libera.free()
        Pm = P - np.outer(alza, d_)
        Nm = np.broadcast_to(-d_, Pm.shape).copy()
        return (ob, Pm, Nm) if devolver else ob
    if onda:
        s = largo(P)
        P = P + N * (onda[1] * np.sin(np.pi * s / onda[0]) ** 2)[:, None]
    if libera is not None:
        libera.free()
    ob = cinta(nombre, P, N, ancho, grueso, coleccion)
    return (ob, P, N) if devolver else ob


def marco(p, t, n):
    """Matriz 4x4 que lleva una pieza construida con Y = largo, Z = grueso (base en
    z = 0) y X = ancho al punto `p`, con Y sobre la tangente `t` y Z sobre `n`."""
    from mathutils import Matrix, Vector
    y = Vector(t).normalized()
    z = Vector(n)
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z)
    M = Matrix.Identity(4)
    for i, c in enumerate((x, y, z, Vector(p))):
        for j in range(3):
            M[j][i] = c[j]
    return M


def cajitas(nombre, P, N, paso, tam, coleccion, alza=0.0):
    """Una fila de cajas (ancho, largo, alto) = `tam` cada `paso` a lo largo de la
    polilinea, en UNA malla: dientes de cremallera, pespuntes, remaches."""
    import formas as F
    s = largo(P)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    verts, caras = [], []
    w, l, h = tam[0] / 2, tam[1] / 2, tam[2]
    for d in np.arange(paso / 2, s[-1], paso):
        p = np.array([np.interp(d, s, P[:, k]) for k in range(3)])
        t = np.array([np.interp(d, s, T[:, k]) for k in range(3)])
        n = np.array([np.interp(d, s, N[:, k]) for k in range(3)])
        t /= np.linalg.norm(t)
        n -= t * np.dot(n, t)
        n /= np.linalg.norm(n)
        x = np.cross(t, n)
        b = len(verts)
        for dz in (alza, alza + h):
            for dx, dy in ((-w, -l), (w, -l), (w, l), (-w, l)):
                verts.append(p + x * dx + t * dy + n * dz)
        caras += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7)]
        caras += [(b + i, b + (i + 1) % 4, b + 4 + (i + 1) % 4, b + 4 + i) for i in range(4)]
    return F._objeto(nombre, verts, caras, coleccion, suave=False)




def diezmar(nombre, origen, tris, coleccion):
    """Copia de `origen` diezmada a ~`tris` triangulos (colapso de aristas). La
    low poly de una piel simulada: no hay solidos que regenerar a menor calidad."""
    me = origen.data.copy()
    ob = bpy.data.objects.new(nombre, me)
    me.name = nombre
    bpy.data.collections[coleccion].objects.link(ob)
    ob.matrix_world = origen.matrix_world.copy()
    me.calc_loop_triangles()
    m = ob.modifiers.new("_dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = min(1.0, tris / max(1, len(me.loop_triangles)))
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    nueva = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(m)
    ob.data = nueva
    bpy.data.meshes.remove(me)
    nueva.name = nombre
    for p in nueva.polygons:
        p.use_smooth = True
    return ob
