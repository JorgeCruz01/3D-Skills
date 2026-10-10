"""Low poly del taladro percutor, 100 % quads y sin booleanos: los mismos
volumenes que el high poly a baja resolucion, cruzados. La boca del portabrocas
va en el perfil de su revolucion y el chaflan de la bateria en las secciones de su
loft. Gatillo, inversor y selector cruzan la carcasa (sus alojamientos van a
los mapas, igual que ventilacion, avellanados, estrias, nervios del collar y
relieve de marca); los tornillos quedan a ras. Un objeto, un material. Los
siete tornillos comparten UV."""
import bpy

import construir_taladro as CT
import formas as F
import lowpoly as L
import quads as Q

COL = "LP Collection"
NOMBRE = "Taladro_Percutor_LP"
MM = F.MM
CORTES_LP = {"_trasera", "_frente", "_hueco_gatillo", "_paso_inversor", "_corredera", "_boca", "_hueco_boton", "_chaflan_bat",
             # los avellanados alojan los tornillos; ventilacion y estrias dan silueta
             "_avellanado", "_ventilacion", "_estria", "_estria_bat"}
GRUPO_TORNILLO = "Rep_Tornillo"


def _vaciar():
    col = bpy.data.collections[COL]
    for o in list(col.all_objects):
        d = o.data
        bpy.data.objects.remove(o)
        if d and d.users == 0:
            bpy.data.meshes.remove(d)


def _carcasa(q):
    sol = CT.solidos_carcasa(q, COL)
    motor, caja = sol[0], sol[1]
    for v in motor.data.vertices:              # la tapa trasera es plana en y = Y_TRAS (el high poly la corta)
        if v.co.y > CT.Y_TRAS * MM:
            v.co.y = CT.Y_TRAS * MM
    d = caja.data                              # la caja de engranajes empieza en la cara delantera, no 1.5 mm antes
    bpy.data.objects.remove(caja)
    bpy.data.meshes.remove(d)
    perfil = [(0, 1.5 * MM), (26.8 * MM, 1.5 * MM), (28.4 * MM, 9 * MM), (29.6 * MM, 18 * MM), (30.2 * MM, 27 * MM), (30.2 * MM, 32 * MM),
              (0, 32 * MM)]
    sol[1] = F.revolucion("_caja", perfil, 4 * F.seg(24, q, 5), CT._mm(0, -57.0, 0), "Y", COL)
    return sol


def _porta(q):
    """Portabrocas con la boca ciega en su perfil (el high poly la taladra)."""
    y0, y1 = CT.Y_PORTA
    Lp = y1 - y0
    R, B = CT.R_PORTA, CT.R_BOCA
    perfil = [(0, 16 * MM), (B * MM, 16 * MM), (B * MM, 0), (12.6 * MM, 0), (14.4 * MM, 0.9 * MM), (R * MM, 13 * MM), (R * MM, (Lp - 3) * MM),
              ((R - 0.7) * MM, (Lp - 1) * MM), ((R - 2.2) * MM, Lp * MM), (0, Lp * MM)]
    return F.revolucion("_porta", perfil, F.seg(96, q, 20), CT._mm(0, y0, 0), "Y", COL)


def _bateria(q):
    """Cuerpo de la bateria como loft a lo largo de Y: cada seccion es un
    rectangulo redondeado en (x, z) cuyo fondo sube por el chaflan delantero y
    cuyo ancho se cierra en arco en los dos extremos (las esquinas verticales
    de radio 10 del high poly). El cuello, tal como lo da el high poly."""
    import math
    import numpy as np
    (y0, y1), zb, zt, X, r = CT.BAT_Y, CT.BAT_Z[0], -184.0, CT.BAT_X, 10.0
    ys = [y0, y0 + 1.5, y0 + 4.5, y0 + r, y0 + 23.3, y0 + 45, y0 + 70, y1 - r - 12, y1 - r, y1 - 4.5, y1 - 1.5, y1]
    secs = []
    for y in ys:
        t = max(0.0, (y0 + r - y) / r, (y - (y1 - r)) / r)
        hw = X - r + r * math.sqrt(max(0.0, 1 - t * t))
        z0 = max(zb, zb - 2 + 0.75 * (y0 + 26 - y))
        p = F.perfil_rect(2 * hw * MM, (zt - z0) * MM, 4 * MM, 2)
        secs.append(np.stack([p[:, 0], np.full(len(p), y * MM), (zt + z0) / 2 * MM + p[:, 1]], -1))
    cuerpo = F.loft("_bateria", secs, COL)
    sol = CT.solidos_bateria(q, COL)
    viejo = sol.pop(0)
    d = viejo.data
    bpy.data.objects.remove(viejo)
    bpy.data.meshes.remove(d)
    return [cuerpo] + sol


QUADS = {"Carcasa_LP": 11000, "Bateria_LP": 4200}
CORTES_FORMA = {"Carcasa_LP": ("_trasera", "_frente"), "Bateria_LP": ("_chaflan_bat",)}       # los que cambian la silueta
SUAVIZADO = {"Carcasa_LP": 30, "Bateria_LP": 24}                                              # los del high poly


def _fundida(nombre, solidos, cortes, info):
    """Una pieza inyectada, de UNA piel: los mismos solidos que el high poly, fundidos por voxeles con sus acuerdos
    y con solo los cortes que cambian la silueta, y remallados en quads (QuadriFlow). Hasta 2026-10-10 eran solidos
    cruzados: el encuentro del motor con la empunadura y con el pie era una arista viva y el acuerdo quedaba todo
    al mapa de normales. Ventilacion, avellanados, estrias y huecos de mando siguen yendo a los mapas."""
    import bmesh
    import tela as T
    forma = [c for c in cortes if c.name.split(".")[0] in CORTES_FORMA[nombre]]
    for c in cortes:
        if c not in forma:
            d = c.data
            bpy.data.objects.remove(c)
            if d.users == 0:
                bpy.data.meshes.remove(d)
    lisa = F.fundir("_lisa_" + nombre, list(solidos), 0.8e-3, suavizado=SUAVIZADO[nombre])
    if forma:
        F.mecanizar(lisa, forma)
    o = T.diezmar(nombre, lisa, 140000, COL)
    r = Q.retopo(o, QUADS[nombre], vivos=32, escala=10.0)
    a = Q.ajustar(o, [lisa])
    for _ in range(2):                                  # QuadriFlow deja lazos ondulados donde no siguen una arista
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.to_mesh(o.data)
        bm.free()
        a = Q.ajustar(o, [lisa])
    info[nombre] = {"censo": {k: r[k] for k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}, "ajuste": a, "desvio": Q.desvio(o, [lisa])}
    d = lisa.data
    bpy.data.objects.remove(lisa)
    bpy.data.meshes.remove(d)
    return o


def construir(q=0.5, aspecto=16.0, fundir=True):
    """q = 0.5: por encima los constructores meten nervios, estrias y tornillos con booleano."""
    _vaciar()
    y0, y1 = CT.Y_COLLAR
    info = {}
    if fundir:
        partes = [
            _fundida("Carcasa_LP", CT.solidos_carcasa(1.0, COL), CT.cortes_carcasa(1.0, COL), info),
            F.tubo("Collar_LP", CT.R_COLLAR * MM, 13 * MM, CT._mm(0, y0, 0), "Y", (y1 - y0) * MM, F.seg(96, q, 20), COL),
            _porta(q),
            _fundida("Bateria_LP", CT.solidos_bateria(1.0, COL), CT.cortes_bateria(1.0, COL), info),
        ]
    else:
      partes = [
        Q.ensamblar("Carcasa_LP", _carcasa(q), CT.cortes_carcasa(q, COL), aspecto=aspecto),
        F.tubo("Collar_LP", CT.R_COLLAR * MM, 13 * MM, CT._mm(0, y0, 0), "Y", (y1 - y0) * MM, F.seg(96, q, 20), COL),
        _porta(q),
        Q.ensamblar("Bateria_LP", _bateria(q), CT.cortes_bateria(q, COL), aspecto=aspecto),
    ]
    pend = {"cuerpos": [(o.get("sin_resolver"), o.get("ocultas")) for o in (partes[0], partes[3])], "fundidas": info}
    ex = CT.piezas_exactas(q, COL)
    for n in list(ex):
        if n.startswith("Tornillo_"):
            o = ex.pop(n)
            d = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d)
    # tornillo a ras de la carcasa (0.2 mm fuera): el del high poly va 0.5 mm hundido en un avellanado que aqui es mapa
    y, z, xs = CT.TORNILLOS[0]
    primero = "Tornillo_LP_1"
    ex[primero] = F.cil(primero, 3.2 * MM, "X", (xs - 2.7) * MM, (xs + 0.2) * MM, F.seg(32, q, 8), COL, CT._mm(y, z))
    for o in partes[1:3] + list(ex.values()):
        r = Q.cuadrar(o)
        Q.tramar(o, aspecto)
        if r["sin_resolver"] or r["tris"] or r["ngonos"]:
            pend[o.name] = (r["sin_resolver"], r["tris"], r["ngonos"])
    L.marcar([ex[primero]], GRUPO_TORNILLO)
    partes += list(ex.values())
    mat = bpy.data.materials.get("LP_Taladro") or bpy.data.materials.new("LP_Taladro")
    mat.use_nodes = True
    mat.use_fake_user = True
    for o in partes:
        o.data.materials.clear()
        o.data.materials.append(mat)
    orden = []
    for k, o in enumerate(partes):                  # indice de pieza en cada cara: las costuras UV se escriben por pieza
        orden.append(o.name.split(".")[0])
        at = o.data.attributes.new("pieza", "INT", "FACE")
        at.data.foreach_set("value", [k] * len(o.data.polygons))
    lp = F.unir(NOMBRE, partes)
    lp["piezas"] = ",".join(orden)
    F.sombrear(lp, 50)
    lp.data.calc_loop_triangles()
    return {"censo": Q.censo(lp), "pendientes": pend, "piezas": orden}


def desplegar(margen=0.002):
    """UV con costuras por pieza. Las dos pieles remalladas no tienen aristas vivas ni lazos que seguir:
    la carcasa se abre por su plano de simetria (dos medias conchas) y suelta las tapas (trasera, frente y base del
    pie); la bateria, por la cara hacia la que mira cada quad (seis caras de caja). El resto, por angulo."""
    import uv
    ob = bpy.data.objects[NOMBRE]
    for e in ob.data.edges:
        e.use_seam = False
    pieza = [a.value for a in ob.data.attributes["pieza"].data]
    nombres = ob["piezas"].split(",")
    k_car, k_bat = nombres.index("Carcasa_LP"), nombres.index("Bateria_LP")

    def tapa(f):
        n = f.normal
        return 1 if n.y > 0.75 else (2 if n.y < -0.75 else (3 if n.z < -0.75 else 0))

    def dom(f):
        n = f.normal
        k = max(range(3), key=lambda i: abs(n[i]))
        return (k, n[k] > 0)

    def extra(e):
        if len(e.link_faces) != 2:
            return False
        a, b = e.link_faces
        pa, pb = pieza[a.index], pieza[b.index]
        if pa != pb:
            return False
        if pa == k_car:
            return tapa(a) != tapa(b) or (tapa(a) == 0 and (a.calc_center_median().x > 0) != (b.calc_center_median().x > 0))
        if pa == k_bat:
            return dom(a) != dom(b)
        return False
    info = uv.desplegar([NOMBRE], margen=margen, extra=extra, refinado=("ejes", 25, 12, "aislar", "aislar"))
    info["ocultas"] = uv.encoger_ocultas(NOMBRE, margen=margen)
    info["repaso"] = []
    for _ in range(3):
        malas = uv.caras_solapadas(NOMBRE) or []
        info["repaso"].append(len(malas))
        if not malas:
            break
        uv._aislar(NOMBRE, malas)
        uv._desplegar_una_vez([NOMBRE], margen, "MINIMUM_STRETCH")
        uv.encoger_ocultas(NOMBRE, margen=margen)
    return info


def replicar():
    y0, z0, x0 = CT.TORNILLOS[0]
    return L.replicar(NOMBRE, {GRUPO_TORNILLO: [((x - x0) * MM, (y - y0) * MM, (z - z0) * MM)
                                                for y, z, x in CT.TORNILLOS[1:]]})
