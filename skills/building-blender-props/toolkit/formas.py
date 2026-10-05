"""Formas parametricas del lote. Sustituye al `primitivas.py` del casco, sin
depender de ningun prop.

Dos familias:
- Solidos exactos: `barrido`, `prisma`, `revolucion`, `hexagono`. Piezas
  mecanizadas, tornilleria, ejes. Topologia limpia, regenerable a cualquier `q`.
- Fundicion: `fundir` une varios solidos en una sola piel con radios de colada
  (remallado por voxeles + suavizado) y `mecanizar` le corta despues caras,
  taladros y pasos con aristas vivas. Es el orden de una pieza real: se cuela y
  luego se mecaniza.

Unidades: metros. Ejes: X lateral, -Y frente, Z arriba. `q` = calidad: 1.0 es
el high poly, ~0.2 la low poly.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

MM = 0.001
EJES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}


def seg(n, q, minimo=3):
    return max(minimo, int(round(n * q)))


# ------------------------------------------------------------------ perfiles

def perfil_rect(w, h, r=0.0, s=0):
    """Rectangulo w x h centrado, esquinas redondeadas con `s` segmentos."""
    if s <= 0 or r <= 0:
        return np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]])
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0),
                       (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(s + 1):
            a = math.radians(a0 + 90 * k / s)
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return np.array(pts)


def perfil_circ(r, n, ry=None, fase=0.0):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + fase
    return np.stack([r * np.cos(a), (ry or r) * np.sin(a)], -1)


def superelipse(ax, ay, n, exp=2.5, t0=0.0, t1=2 * math.pi, cerrado=True):
    t = np.linspace(t0, t1, n, endpoint=not cerrado)
    c, s = np.cos(t), np.sin(t)
    g = (np.abs(c) ** exp + np.abs(s) ** exp) ** (-1.0 / exp)
    return np.stack([ax * g * c, ay * g * s], -1)


def spline(puntos, n=8, cerrada=True, vivos=()):
    """Curva suave (Catmull-Rom) por `puntos` (M, k), con `n` tramos entre cada par.
    Los indices de `vivos` conservan su esquina: ahi la tangente es nula. Sirve
    para que un contorno dibujado con una docena de puntos no se lea como poligono."""
    P = np.asarray(puntos, float)
    m = len(P)
    T = np.zeros_like(P)
    for i in range(m):
        if i in vivos:
            continue
        a, b = (i - 1) % m, (i + 1) % m
        if not cerrada and (i == 0 or i == m - 1):
            T[i] = P[min(i + 1, m - 1)] - P[max(i - 1, 0)]
        else:
            T[i] = (P[b] - P[a]) / 2
    out = []
    for i in range(m if cerrada else m - 1):
        j = (i + 1) % m
        for t in np.linspace(0, 1, n, endpoint=False):
            h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
            h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
            out.append(h00 * P[i] + h10 * T[i] + h01 * P[j] + h11 * T[j])
    if not cerrada:
        out.append(P[-1])
    return np.array(out)


def hexagono(entre_caras):
    """Contorno hexagonal dado el ancho entre caras."""
    return perfil_circ(entre_caras / math.sqrt(3), 6, fase=math.pi / 6)


def disco(n):
    """Rejilla (n+1)^2 -> (rho, theta) por mapeo concentrico: todo quads, sin polo."""
    t = np.linspace(-1.0, 1.0, n + 1)
    a, b = np.meshgrid(t, t, indexing="xy")
    r = np.zeros_like(a)
    phi = np.zeros_like(a)
    m = np.abs(a) > np.abs(b)
    r[m] = a[m]
    phi[m] = (np.pi / 4) * (b[m] / a[m])
    k = ~m & (b != 0)
    r[k] = b[k]
    phi[k] = np.pi / 2 - (np.pi / 4) * (a[k] / b[k])
    x, y = r * np.cos(phi), r * np.sin(phi)
    return np.hypot(x, y), np.arctan2(y, x)


# ------------------------------------------------------------------ mallas

def _objeto(nombre, verts, caras, coleccion, suave=True):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], caras)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = suave
    me.update()
    # SIEMPRE objeto nuevo. Reutilizar por nombre ha roto dos veces la valvula: la
    # segunda brida sustituyo a la primera, y al construir la low poly las tuercas,
    # arandelas y juntas del high poly (mismo nombre) fueron reemplazadas y unidas
    # a la LP: el HP paso de 31 piezas a 13 sin un solo error.
    ob = bpy.data.objects.new(nombre, me)
    bpy.data.collections[coleccion].objects.link(ob)
    return ob


def _marco(eje):
    """(u, v, w) con w = eje. Con eje Z: u = X, v = Y. Con eje horizontal: v = Z."""
    w = np.asarray(EJES[eje] if isinstance(eje, str) else eje, float)
    w = w / np.linalg.norm(w)
    if abs(w[2]) > 0.9:
        u = np.array([1.0, 0, 0])
    else:
        u = np.cross([0, 0, 1.0], w)
        u /= np.linalg.norm(u)
    return u, np.cross(w, u), w


def barrido(nombre, camino, perfil, arriba, coleccion, cerrado=False, suave=True):
    """Extruye `perfil` (M,2) a lo largo de `camino` (N,3). `arriba` (3,) o (N,3)
    orienta el eje v del perfil; el eje u es tangente x arriba."""
    P = np.asarray(camino, float)
    n, m = len(P), len(perfil)
    T = (np.roll(P, -1, 0) - np.roll(P, 1, 0)) if cerrado else np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    U = np.broadcast_to(np.asarray(arriba, float), P.shape).copy()
    U -= np.sum(U * T, 1, keepdims=True) * T
    U /= np.linalg.norm(U, axis=1, keepdims=True)
    S = np.cross(T, U)
    verts = (P[:, None, :] + perfil[None, :, 0, None] * S[:, None, :]
             + perfil[None, :, 1, None] * U[:, None, :]).reshape(-1, 3)
    caras = []
    for i in range(n if cerrado else n - 1):
        a, b = i * m, ((i + 1) % n) * m
        for j in range(m):
            k = (j + 1) % m
            caras.append((a + j, a + k, b + k, b + j))
    if not cerrado:
        caras.append(tuple(range(m)))
        caras.append(tuple((n - 1) * m + j for j in range(m)))
    return _objeto(nombre, verts, caras, coleccion, suave)


def prisma(nombre, contorno, origen, eje, alto, coleccion, bisel=0.0, s=0, suave=False, por_normal=False):
    """Extruye un contorno plano (M,2) a lo largo de `eje` desde `origen`.
    Con bisel, anade un chaflan redondeado de `s` tramos en ambas tapas."""
    u, v, w = _marco(eje)
    C = np.asarray(contorno, float)
    cen = C.mean(0)
    if bisel > 0 and s > 0:
        base = [(-bisel * (1 - math.sin(a)), bisel * (1 - math.cos(a)))
                for a in ((math.pi / 2) * k / s for k in range(s + 1))]
        niveles = base + [(d, alto - h) for d, h in reversed(base)]
    else:
        niveles = [(0.0, 0.0), (0.0, alto)]
    if por_normal:
        # desplazamiento por la normal del contorno (a inglete): un redondeo de canto
        # uniforme tambien en contornos alargados o concavos, donde "hacia el centro" no lo es
        sig = np.roll(C, -1, 0) - C
        area = float(np.sum(C[:, 0] * np.roll(C[:, 1], -1) - np.roll(C[:, 0], -1) * C[:, 1]))
        nrm = np.stack([sig[:, 1], -sig[:, 0]], -1) * (1.0 if area > 0 else -1.0)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        dirs = nrm + np.roll(nrm, 1, 0)
        largo = np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-12
        dirs = dirs / largo * np.minimum(2.0 / largo, 2.5)
    else:
        dirs = C - cen
        dirs = dirs / (np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-12)
    verts = []
    for d, h in niveles:
        for x, y in C + dirs * d:
            verts.append(np.asarray(origen, float) + u * x + v * y + w * h)
    m = len(C)
    caras = []
    for i in range(len(niveles) - 1):
        a, b = i * m, (i + 1) * m
        for j in range(m):
            k = (j + 1) % m
            caras.append((a + j, a + k, b + k, b + j))
    caras.append(tuple(range(m)))
    caras.append(tuple((len(niveles) - 1) * m + j for j in range(m)))
    return _objeto(nombre, verts, caras, coleccion, suave)


def cilindro(nombre, radio, origen, eje, alto, n, coleccion, bisel=0.0, s=0):
    return prisma(nombre, perfil_circ(radio, n), origen, eje, alto, coleccion, bisel, s, suave=True)


def revolucion(nombre, perfil_rz, n, origen, eje, coleccion, suave=True):
    """Solido de revolucion. `perfil_rz` = contorno CERRADO de puntos (r, z) con
    r >= 0, recorrido una vez; los puntos con r = 0 quedan sobre el eje."""
    u, v, w = _marco(eje)
    P = np.asarray(perfil_rz, float)
    m = len(P)
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    o = np.asarray(origen, float)
    verts = []
    for a in ang:
        d = u * math.cos(a) + v * math.sin(a)
        for r, z in P:
            verts.append(o + d * r + w * z)
    caras = []
    for i in range(n):
        a, b = i * m, ((i + 1) % n) * m
        for j in range(m):
            k = (j + 1) % m
            # el tramo del perfil que corre SOBRE el eje no genera cara: dejaba una
            # arista suelta en el eje (no estanca) en tornillos y husillo
            if P[j][0] < 1e-12 and P[k][0] < 1e-12:
                continue
            caras.append((a + j, b + j, b + k, a + k))
    return _objeto(nombre, verts, caras, coleccion, suave)


def caja(nombre, x, y, z, coleccion, r=0.0, s=0):
    """Caja por intervalos (x0, x1), (y0, y1), (z0, z1) en metros. `r`, `s`:
    radio y tramos de redondeo de las cuatro aristas verticales."""
    w, h = x[1] - x[0], y[1] - y[0]
    return prisma(nombre, perfil_rect(w, h, r, s), ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, z[0]), "Z",
                  z[1] - z[0], coleccion)


def caja_blanda(nombre, x, y, z, coleccion, r, s=6, canto=None, sc=4):
    """Caja con las DOCE aristas redondeadas: las cuatro verticales con radio `r`
    y `s` tramos, y las de las dos tapas con radio `canto` (por defecto r/2) y
    `sc` tramos. `caja` deja las tapas a canto vivo y, con pocos tramos, las
    esquinas se leen como chaflanes: asi nacieron las carcasas "duras" del lote."""
    w, h = x[1] - x[0], y[1] - y[0]
    canto = r / 2 if canto is None else canto
    # topes: con r mayor que medio lado el contorno se cruza y la caja se abomba (un pestillo de 3.4 mm
    # con r = 2.2 salio 1.8 mm mas ancho por cada lado y se metio en el armazon)
    r = min(r, 0.49 * min(w, h))
    canto = min(canto, r, 0.49 * (z[1] - z[0]))
    P = perfil_rect(w, h, r, s)
    # los lados rectos se parten: el primer anillo del canto mide canto*(1-cos) de
    # ancho y un lado entero de la caja daba caras de mas de 100:1 (131 en un boton)
    tope = 50 * canto * (1 - math.cos(math.pi / (2 * sc)))
    Q = []
    for a, b in zip(P, np.roll(P, -1, 0)):
        k = max(1, int(math.ceil(np.linalg.norm(b - a) / tope)))
        Q += [a + (b - a) * t / k for t in range(k)]
    return prisma(nombre, np.array(Q),((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, z[0]), "Z",
                  z[1] - z[0], coleccion, canto, sc, suave=True, por_normal=True)


def cil(nombre, radio, eje, a, b, n, coleccion, centro=(0.0, 0.0), bisel=0.0, s=0):
    """Cilindro a lo largo de `eje` entre las cotas a y b; `centro` son las otras
    dos coordenadas, en orden (para X: y, z; para Y: x, z; para Z: x, y)."""
    o = {"X": (a, centro[0], centro[1]), "Y": (centro[0], a, centro[1]), "Z": (centro[0], centro[1], a)}[eje]
    return cilindro(nombre, radio, o, eje, b - a, n, coleccion, bisel, s)


def loft(nombre, secciones, coleccion, suave=True):
    """Une secciones (cada una (M,3), mismo numero de puntos) y cierra con tapas."""
    m = len(secciones[0])
    verts = np.concatenate(secciones)
    caras = []
    for i in range(len(secciones) - 1):
        a, b = i * m, (i + 1) * m
        for j in range(m):
            k = (j + 1) % m
            caras.append((a + j, a + k, b + k, b + j))
    caras.append(tuple(range(m)))
    caras.append(tuple((len(secciones) - 1) * m + j for j in range(m)))
    return _objeto(nombre, verts, caras, coleccion, suave)


def tubo(nombre, r_ext, r_int, origen, eje, alto, n, coleccion, bisel=0.0):
    """Anillo o casquillo: revolucion de un rectangulo, con chaflan opcional."""
    b = bisel
    perfil = [(r_int, 0), (r_ext - b, 0), (r_ext, b), (r_ext, alto - b), (r_ext - b, alto), (r_int, alto)]
    if b <= 0:
        perfil = [(r_int, 0), (r_ext, 0), (r_ext, alto), (r_int, alto)]
    return revolucion(nombre, perfil, n, origen, eje, coleccion)


def domo(nombre, centro, lado, ry, rz, rx, n, coleccion, exp=0.75, plano=2.6):
    """Media superelipsoide cerrada por una tapa plana, creciendo en `lado`*X."""
    rho, th = disco(n)
    c, s = np.cos(th), np.sin(th)
    g = (np.abs(c) ** plano + np.abs(s) ** plano) ** (-1.0 / plano)
    phi = np.clip(rho, 0, 1) * (math.pi / 2)
    f = np.sin(phi)
    y, z, x = ry * g * c * f, rz * g * s * f, rx * np.cos(phi) ** exp
    cx, cy, cz = centro
    k = n + 1
    frente = np.stack([cx + lado * x, cy + y, cz + z], -1).reshape(-1, 3)
    tapa = np.stack([np.full_like(x, cx), cy + y, cz + z], -1).reshape(-1, 3)
    caras = []
    for j in range(n):
        for i in range(n):
            a = j * k + i
            caras.append((a, a + 1, a + k + 1, a + k))
            b = a + k * k
            caras.append((b, b + k, b + k + 1, b + 1))
    return _objeto(nombre, np.concatenate([frente, tapa]), caras, coleccion, True)


def texto(nombre, cadena, alto, relieve, coleccion, origen=(0, 0, 0), normal="-Y", fuente=None):
    """Texto extruido como solido cerrado, centrado en `origen` y mirando a
    `normal` ('-Y', '+Y', '+X', '-X', '+Z'). Para grabados y letras de fundicion."""
    cu = bpy.data.curves.new(nombre, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = cadena, alto, "CENTER", "CENTER"
    cu.extrude = relieve / 2
    cu.resolution_u = 4
    if fuente:
        cu.font = fuente
    ob = bpy.data.objects.new(nombre, cu)
    bpy.data.collections[coleccion].objects.link(ob)
    rot = {"-Y": (math.pi / 2, 0, 0), "+Y": (math.pi / 2, 0, math.pi), "+X": (math.pi / 2, 0, math.pi / 2),
           "-X": (math.pi / 2, 0, -math.pi / 2), "+Z": (0, 0, 0)}[normal]
    ob.rotation_euler = rot
    ob.location = origen
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.name = ob.data.name = nombre
    return ob


def unir(nombre, objetos):
    """Une objetos en `nombre` conservando el primero."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    if len(objetos) > 1:
        bpy.ops.object.join()
    objetos[0].name = nombre
    objetos[0].data.name = nombre
    return objetos[0]


def circular(objeto, n, eje="Z", centro=(0, 0, 0), incluir_original=True):
    """Devuelve `objeto` mas n-1 copias giradas alrededor de `eje`."""
    w = Vector(EJES[eje])
    c = Vector(centro)
    obs = [objeto] if incluir_original else []
    for k in range(1, n):
        o = objeto.copy()
        o.data = objeto.data.copy()
        for col in objeto.users_collection:
            col.objects.link(o)
        m = Matrix.Translation(c) @ Matrix.Rotation(2 * math.pi * k / n, 4, w) @ Matrix.Translation(-c)
        o.data.transform(m)
        obs.append(o)
    return obs


# ------------------------------------------------------------------ fundicion

def fundir(nombre, objetos, voxel, suavizado=6, factor=0.5):
    """Une `objetos` en una sola piel cerrada con radios de colada.

    Remalla por voxeles de tamano `voxel` (m) y suaviza. El radio de acuerdo que
    aparece en cada arista interior es del orden de `voxel * sqrt(suavizado)`.
    Las caras que deben quedar planas y las aristas vivas se cortan DESPUES con
    `mecanizar`: suavizar tambien redondea lo que no deberia."""
    ob = unir(nombre, list(objetos))
    bpy.context.view_layer.objects.active = ob
    ob.data.remesh_voxel_size = voxel
    ob.data.remesh_voxel_adaptivity = 0.0
    ob.data.use_remesh_fix_poles = False
    bpy.ops.object.voxel_remesh()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for _ in range(suavizado):
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=factor, use_axis_x=True, use_axis_y=True,
                              use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.update()
    return ob


def mecanizar(objeto, cortadores, soldar=0.0, operacion="DIFFERENCE", solver="EXACT"):
    """Corta (o une) `cortadores` sobre `objeto` con el booleano exacto, uno a uno,
    y los elimina. `soldar` (m): tras el corte, funde los vertices del objeto a
    menos de esa distancia SOLO dentro de la caja de cada cortador ampliada 2 mm,
    que es donde el booleano deja astillas; un merge global colapsaria detalle."""
    bpy.context.view_layer.objects.active = objeto
    cajas = []
    for c in cortadores:
        co = np.array([c.matrix_world @ v.co for v in c.data.vertices])
        cajas.append((co.min(0) - 2 * MM, co.max(0) + 2 * MM))
    # todos los cortadores en UNA pasada (operando = coleccion): 23 cortes uno a
    # uno sobre 900k caras tardaban 111 s
    tmp = bpy.data.collections.new("_cortadores")
    bpy.context.scene.collection.children.link(tmp)
    for c in cortadores:
        tmp.objects.link(c)
    mod = objeto.modifiers.new("corte", "BOOLEAN")
    mod.operation = operacion
    mod.solver = solver
    mod.operand_type = "COLLECTION"
    mod.collection = tmp
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.scene.collection.children.unlink(tmp)
    bpy.data.collections.remove(tmp)
    for c in cortadores:
        d = c.data
        bpy.data.objects.remove(c)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    if soldar > 0 and cajas:
        bm = bmesh.new()
        bm.from_mesh(objeto.data)
        P = np.array([v.co[:] for v in bm.verts])
        dentro = np.zeros(len(P), bool)
        for lo, hi in cajas:
            dentro |= np.all((P >= lo) & (P <= hi), axis=1)
        bm.verts.ensure_lookup_table()
        bmesh.ops.remove_doubles(bm, verts=[bm.verts[i] for i in np.nonzero(dentro)[0]], dist=soldar)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-7)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(objeto.data)
        bm.free()
    objeto.data.update()
    return objeto


def sombrear(objeto, angulo_grados=40):
    for p in objeto.data.polygons:
        p.use_smooth = True
    objeto.data.set_sharp_from_angle(angle=math.radians(angulo_grados))
    return objeto


def volumen_cm3(nombre):
    """Volumen encerrado por la malla, en cm3. Solo tiene sentido si es estanca."""
    ob = bpy.data.objects[nombre]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=False)
    bm.free()
    return v * 1e6
