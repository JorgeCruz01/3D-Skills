"""Utilidades de low poly compartidas por el lote.

- `union_mecanizada`: LP de una pieza de fundicion a partir de los mismos
  volumenes y cortes que el high poly, con booleano y limpieza.
- `limpiar`: suelda, triangula y ordena la triangulacion de las caras planas.
- `marcar` / `replicar` / `proxy_bake`: piezas repetidas que comparten UV. Se
  construye una, se hornea esa, y las copias se excluyen del horneado.
"""
import math

import bmesh
import bpy

import formas as F

MM = F.MM
GRUPO_REPLICAS = "Replicas"


def limpiar(ob, soldar=0.05 * MM):
    """Suelda vertices a menos de `soldar`, triangula todo y reordena la
    triangulacion SOLO dentro de cada zona plana.

    El booleano deja las caras planas (la cara de una brida con sus taladros)
    trianguladas en abanicos de triangulos largos. `beautify_fill` gira aristas
    para acercarse a Delaunay; se le pasan unicamente las aristas entre caras
    coplanares, de modo que la forma no cambia ni una micra."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # Las aristas cortas se COLAPSAN (dissolve_degenerate), no se sueldan por
    # distancia. remove_doubles funde cualquier par de vertices cercanos aunque no
    # compartan arista, y en la carcasa de un taladro eso pellizco la malla: 2
    # aristas no estancas con 0.3 mm. Colapsando, misma pieza: estanca y sin caras
    # degeneradas con 0.7 mm.
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.02 * MM)
    for _ in range(3):
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                              ngon_method="BEAUTY")
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=soldar)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    bm.normal_update()
    planas = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(1.0) < math.radians(0.5)]
    if planas:
        bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=planas, method="ANGLE")
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-6)
    # el colapso final puede fundir dos triangulos en un n-gon (durometro: 1)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


PLANOS = {}      # {nombre de objeto: {eje: [cotas de los planos de troceo]}}


def costura_en_planos(eje, cotas, tol=0.05 * MM, donde=None):
    """Predicado de costura UV: aristas contenidas en alguno de los planos
    `eje` = cota. Parte en tramos las islas muy largas (una horquilla de 1150 mm
    desplegada entera obliga a encoger todo el atlas). `donde`: filtro opcional
    sobre el punto medio de la arista."""
    i = "XYZ".index(eje)

    def f(e):
        a, b = e.verts[0].co, e.verts[1].co
        if donde and not donde((a + b) / 2):
            return False
        return any(abs(a[i] - c) < tol and abs(b[i] - c) < tol for c in cotas)
    return f


def costura_por_orientacion(ref, umbral=0.0, donde=None):
    """Predicado de costura UV: aristas entre dos caras de distinta clase segun
    normal . ref (> umbral, < -umbral o entre medias). Con umbral 0 parte un tubo
    en dos medias canas; con 0.5 separa techo, costados y fondo de una chapa con
    los cantos redondeados, que por angulo quedarian en una sola isla enrollada."""
    from mathutils import Vector
    r = Vector(ref).normalized()

    def clase(f):
        d = f.normal.dot(r)
        return 1 if d > umbral else (-1 if d < -umbral else 0)

    def f(e):
        if len(e.link_faces) != 2:
            return False
        if donde and not donde((e.verts[0].co + e.verts[1].co) / 2):
            return False
        return clase(e.link_faces[0]) != clase(e.link_faces[1])
    return f


def costura_por_lado(eje, cotas, donde=None):
    """Predicado de costura UV: aristas entre dos caras cuyo centro cae a
    distinto lado de alguno de los planos `eje` = cota. Para mallas de quads sin
    aristas sobre el plano (una piel remallada): cortar la malla con el plano
    meteria triangulos, y esto deja una costura en escalera por los lazos que ya
    hay. `donde`: filtro sobre el punto medio de la arista."""
    i = "XYZ".index(eje)
    cs = sorted(cotas)

    def clase(f):
        c = f.calc_center_median()[i]
        return sum(1 for k in cs if c > k)

    def f(e):
        if len(e.link_faces) != 2:
            return False
        if donde and not donde((e.verts[0].co + e.verts[1].co) / 2):
            return False
        return clase(e.link_faces[0]) != clase(e.link_faces[1])
    return f


def cualquiera(*predicados):
    return lambda e: any(p(e) for p in predicados)


def trocear(ob, paso, ejes="XYZ", soldar=0.05 * MM):
    """Corta la malla con planos cada `paso` (m) a lo largo de `ejes` y la vuelve
    a limpiar. Para piezas largas y finas (una horquilla de 1150 x 3 mm, un tubo
    de 750 mm): sin cortes sus caras pasan de 100:1 por mucho que se reordene la
    triangulacion, porque no hay vertices intermedios."""
    from mathutils import Vector
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for i, e in enumerate("XYZ"):
        if e not in ejes:
            continue
        cs = [v.co[i] for v in bm.verts]
        lo, hi = min(cs), max(cs)
        n = int((hi - lo) / paso)
        if n < 1:
            continue
        real = (hi - lo) / (n + 1)
        no = Vector([1.0 if j == i else 0.0 for j in range(3)])
        PLANOS.setdefault(ob.name, {})[e] = [lo + real * k for k in range(1, n + 1)]
        for k in range(1, n + 1):
            co = Vector([lo + real * k if j == i else 0.0 for j in range(3)])
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, dist=1e-6)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return limpiar(ob, soldar=soldar)


def cortar_en(ob, eje, cotas, ajuste=0.6 * MM):
    """Corta la malla por los planos `eje` = cota y deja ahi un lazo de aristas
    limpio, para usarlo de costura UV con `costura_en_planos`. Una piel organica
    (tela simulada y diezmada) no tiene aristas vivas: sin estos cortes se
    despliega como una sola isla, y partirla por clases de cara deja la frontera
    en zigzag y cientos de islas de un triangulo (965 islas, ocupacion 39 %).
    `ajuste`: los vertices a menos de esa distancia se llevan al plano en vez de
    cortar a su lado, que es lo que deja astillas."""
    from mathutils import Vector
    i = "XYZ".index(eje)
    no = Vector([1.0 if j == i else 0.0 for j in range(3)])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for c in cotas:
        for v in bm.verts:
            if abs(v.co[i] - c) < ajuste:
                v.co[i] = c
        co = Vector([c if j == i else 0.0 for j in range(3)])
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, dist=1e-7)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    PLANOS.setdefault(ob.name, {})[eje] = list(cotas)
    return ob


def union_mecanizada(nombre, solidos, cortes, conservar, solver="MANIFOLD", soldar=0.3 * MM):
    """Une `solidos` y aplica los `cortes` cuyo nombre base esta en `conservar`
    (los que cambian la silueta o dejan ver el interior). El resto se descarta:
    su detalle va al mapa de normales."""
    base = solidos[0]
    base.name = base.data.name = nombre
    if len(solidos) > 1:
        F.mecanizar(base, solidos[1:], operacion="UNION", solver=solver)
    usar = [c for c in cortes if c.name.split(".")[0] in conservar]
    for c in cortes:
        if c not in usar:
            d = c.data
            bpy.data.objects.remove(c)
            bpy.data.meshes.remove(d)
    if usar:
        F.mecanizar(base, usar, solver=solver)
    # 0.3 mm: el booleano deja aristas de ~0.1 mm en los cruces de superficies curvas
    return limpiar(base, soldar=soldar)


def marcar(objetos, grupo):
    """Mete todos los vertices de `objetos` en el grupo `grupo` (antes de unir)."""
    for o in objetos:
        g = o.vertex_groups.new(name=grupo)
        g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")


def replicar(nombre, destinos):
    """Copia las caras de cada grupo a nuevas posiciones, con la misma UV.
    `destinos` = {grupo: [matriz 4x4 o (dx, dy, dz), ...]}. Las copias quedan en
    el grupo `Replicas`. Llamar despues de desplegar y antes de medir silueta."""
    from mathutils import Matrix, Vector
    lp = bpy.data.objects[nombre]
    if GRUPO_REPLICAS not in lp.vertex_groups:
        lp.vertex_groups.new(name=GRUPO_REPLICAS)
    gr = lp.vertex_groups[GRUPO_REPLICAS].index
    bm = bmesh.new()
    bm.from_mesh(lp.data)
    dl = bm.verts.layers.deform.verify()
    if any(gr in v[dl] for v in bm.verts):
        bm.free()
        return {"ok": False, "error": "ya estaba replicado"}
    hechas = 0
    for grupo, lista in destinos.items():
        gi = lp.vertex_groups[grupo].index
        caras = [f for f in bm.faces if all(gi in v[dl] for v in f.verts)]
        for t in lista:
            m = t if isinstance(t, Matrix) else Matrix.Translation(Vector(t))
            dup = bmesh.ops.duplicate(bm, geom=caras)
            nuevos_v = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMVert)]
            nuevas_f = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMFace)]
            for v in nuevos_v:
                v.co = m @ v.co
                del v[dl][gi]
                v[dl][gr] = 1.0
            if m.determinant() < 0:          # espejo: hay que invertir el giro de las caras
                bmesh.ops.reverse_faces(bm, faces=nuevas_f)
            hechas += 1
    bm.to_mesh(lp.data)
    bm.free()
    lp.data.update()
    lp.data.calc_loop_triangles()
    return {"ok": True, "copias": hechas, "tris": len(lp.data.loop_triangles)}


def proxy_bake(nombre, coleccion="LP Collection"):
    """Copia de la LP SIN las replicas, para hornear: comparten UV con su
    original y hornearlas encima escribiria varias veces el mismo texel."""
    lp = bpy.data.objects[nombre]
    px = lp.copy()
    px.data = lp.data.copy()
    px.name = px.data.name = nombre + "_bake"
    bpy.data.collections[coleccion].objects.link(px)
    if GRUPO_REPLICAS in px.vertex_groups:
        gi = px.vertex_groups[GRUPO_REPLICAS].index
        bm = bmesh.new()
        bm.from_mesh(px.data)
        dl = bm.verts.layers.deform.verify()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if gi in v[dl]], context="VERTS")
        bm.to_mesh(px.data)
        bm.free()
        px.data.update()
    return px.name


def quitar_proxy(nombre):
    o = bpy.data.objects.get(nombre + "_bake")
    if o:
        d = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(d)


def costura_tiras(paso, ancho=None, ejes="XYZ"):
    """Predicado de costura UV: parte las TIRAS largas (el canto de una placa de
    2.5 m de perimetro y 16 mm de alto, una columna) cada `paso` metros a lo
    largo de cada eje. Una tira entera obliga a encoger todo el atlas: el
    soporte de un motor se quedaba en el 18 % de ocupacion. Solo corta entre
    caras estrechas (menos de `ancho`, por defecto paso / 4, en la direccion
    transversal), asi que una cara grande y plana no se trocea."""
    from mathutils import Vector
    ancho = paso / 4 if ancho is None else ancho
    ax = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]

    def estrecha(f, k):
        t = f.normal.cross(ax[k])
        if t.length < 1e-6:
            return False
        t.normalize()
        d = [v.co.dot(t) for v in f.verts]
        return max(d) - min(d) < ancho

    def f(e):
        if len(e.link_faces) != 2:
            return False
        a, b = e.link_faces
        ca, cb = a.calc_center_median(), b.calc_center_median()
        for k in range(3):
            if "XYZ"[k] not in ejes or abs(a.normal[k]) > 0.3 or abs(b.normal[k]) > 0.3:
                continue
            if int(ca[k] // paso) != int(cb[k] // paso) and estrecha(a, k) and estrecha(b, k):
                return True
        return False
    return f
