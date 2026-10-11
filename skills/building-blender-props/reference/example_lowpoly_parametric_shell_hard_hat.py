"""Low poly del casco, 100 % quads: se REGENERA desde las mismas funciones que
el high poly, a baja resolucion, en dos objetos (dos sets): `Casco` (todo lo
opaco) y `Visor` (policarbonato transparente).

La carcasa y las copas no usan aqui la rejilla en disco del high poly: sus
quads de las diagonales tienen un angulo casi llano (son triangulos con cuatro
vertices) y habia que partirlos. Van en anillos y meridianos, con la coronilla
cerrada por una rejilla (`Q.cuadrar`).
"""
import math
import bpy
import bmesh
import construir_carcasa as CC
import construir_piezas as CP
import primitivas
import quads as Q

COL = "LP Collection"
NOMBRE = "Casco_Seguridad_LP"
VISOR = "Visor_Careta_LP"
GRUPO_OREJERA = "Orejera"
ANGULO_DURO = math.radians(60)     # arista dura = costura UV: mismo umbral en ambos


def _vaciar():
    col = bpy.data.collections[COL]
    for o in list(col.all_objects):
        d = o.data
        bpy.data.objects.remove(o)
        if d and d.users == 0:
            bpy.data.meshes.remove(d)


# anillos de la carcasa: fraccion del radio de la cupula (dos juntos en el escalon de la banda) y del ala
# Hasta 2026-10-11 eran 10 anillos y 64 meridianos: en gris y de cerca la coronilla salia abollada (la cresta de 3 mm
# con su escalon de 4 mm caia entre dos meridianos, y la rejilla de la coronilla se pegaba al high poly a saltos) y
# la silueta de la cupula, poligonal. Ahora 17 anillos y 128 meridianos: el escalon de la cresta tiene su meridiano.
ANILLOS_CUPULA = (0.08, 0.16, 0.24, 0.32, 0.40, 0.48, 0.56, 0.63, 0.70, 0.76, 0.81, 0.855, 0.8964, 0.9108, 0.94, 0.97, 1.0)
ANILLOS_ALA = (CC.U_ARCO / 2, CC.U_ARCO, CC.U_ARCO + (1 - CC.U_ARCO) / 3, CC.U_ARCO + 2 * (1 - CC.U_ARCO) / 3, 1.0)


def _carcasa(nombre, nt=128):
    """Carcasa en anillos y meridianos: `nt` meridianos (par) y un abanico en la
    coronilla, que `Q.cuadrar` convierte en rejilla abombada hacia el apice."""
    import numpy as np
    rhos = [f * CC.RHO_D for f in ANILLOS_CUPULA] + [CC.RHO_D + u * (1 - CC.RHO_D) for u in ANILLOS_ALA]
    RHO, TH = np.meshgrid(np.array(rhos), np.linspace(0, 2 * math.pi, nt, endpoint=False), indexing="ij")
    Po, Pi = CC.superficie_en(RHO, TH, cresta_t=14 * CC.MM)
    ao, ai = CC.superficie_en(np.array([[0.0]]), np.array([[0.0]]))
    nr = len(rhos)
    verts = np.concatenate([Po.reshape(-1, 3), ao.reshape(-1, 3), Pi.reshape(-1, 3), ai.reshape(-1, 3)])
    caras = []
    for off in (0, nr * nt + 1):
        apice = off + nr * nt
        for k in range(nt):
            n = (k + 1) % nt
            caras.append((apice, off + k, off + n))
            for r in range(nr - 1):
                a, b = off + r * nt, off + (r + 1) * nt
                caras.append((a + k, b + k, b + n, a + n))
    ult, off = (nr - 1) * nt, nr * nt + 1
    for k in range(nt):
        n = (k + 1) % nt
        caras.append((ult + k, off + ult + k, off + ult + n, ult + n))
    ob = primitivas._objeto(nombre, verts, caras, COL, True)
    Q.cuadrar(ob)
    # la rejilla de la coronilla es una interpolacion: se pega al high poly (alli esta la cresta)
    lim = (math.sin(ANILLOS_CUPULA[0] * math.pi / 2) * 0.97) ** 2
    Q.ajustar(ob, ["Carcasa"], solo=lambda w: (w.x / CC.B) ** 2 + (w.y / CC.A) ** 2 < lim and w.z > CC.Z0 + 0.6 * CC.H)
    return ob


def _domo(nombre, centro, eje_x, ry, rz, rx, n, coleccion, exp=0.75, plano=2.6):
    """Copa de la orejera en anillos y meridianos (misma forma que `primitivas.domo`)."""
    import numpy as np
    nt, nr = 40, 8
    cx, cy, cz = centro
    verts = []
    for k in range(1, nr + 1):
        phi = k / nr * math.pi / 2
        for t in np.linspace(0, 2 * math.pi, nt, endpoint=False):
            c, s_ = math.cos(t), math.sin(t)
            g = (abs(c) ** plano + abs(s_) ** plano) ** (-1.0 / plano)
            f = math.sin(phi)
            verts.append((cx + eje_x * rx * max(0.0, math.cos(phi)) ** exp, cy + ry * g * c * f, cz + rz * g * s_ * f))
    apice = len(verts)
    verts.append((cx + eje_x * rx, cy, cz))
    caras = []
    for k in range(nt):
        n_ = (k + 1) % nt
        caras.append((apice, k, n_))
        for r in range(nr - 1):
            a, b = r * nt, (r + 1) * nt
            caras.append((a + k, b + k, b + n_, a + n_))
    caras.append(tuple((nr - 1) * nt + k for k in range(nt)))
    return primitivas._objeto(nombre, verts, caras, coleccion, True)


def construir(q=0.2, aspecto=30.0):
    _vaciar()
    car = _carcasa("Carcasa_LP")
    partes = [car] + CP.alojamientos(q, COL, "_LP")
    partes += CP.arnes(q, COL, "_LP")
    # las dos orejeras son simetricas y comparten UV: se construye y hornea solo
    # la derecha, y `espejar_orejera` anade la izquierda despues del bake. Asi el
    # atlas no gasta dos veces el mismo detalle y la densidad sube para todo el set.
    original = CP.domo
    CP.domo = _domo
    try:
        oreja = CP.orejera(1, q, COL, "_LP")
    finally:
        CP.domo = original
    sop, visor = CP.careta(q, COL, "_LP")
    partes += oreja + [sop]
    pend = {}
    for o in partes[1:] + [visor]:
        r = Q.cuadrar(o)
        Q.tramar(o, aspecto)
        if r["sin_resolver"] or r["tris"] or r["ngonos"]:
            pend[o.name] = (r["sin_resolver"], r["tris"], r["ngonos"])
    for o in oreja:
        g = o.vertex_groups.new(name=GRUPO_OREJERA)
        g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    m_casco = bpy.data.materials.get("LP_Casco") or bpy.data.materials.new("LP_Casco")
    m_visor = bpy.data.materials.get("LP_Visor") or bpy.data.materials.new("LP_Visor")
    for m in (m_casco, m_visor):
        m.use_nodes = True
        m.use_fake_user = True
    for o in partes:
        o.data.materials.clear()
        o.data.materials.append(m_casco)
    visor.data.materials.clear()
    visor.data.materials.append(m_visor)
    for k, o in enumerate(partes):                  # indice de pieza en cada cara: las costuras UV se escriben por pieza
        at = o.data.attributes.new("pieza", "INT", "FACE")
        at.data.foreach_set("value", [k] * len(o.data.polygons))
    # un objeto por set: las puertas UV se miden por objeto y cada set ocupa su 0-1
    lp = primitivas.unir(NOMBRE, partes)
    visor.name = visor.data.name = VISOR
    info = {"pendientes": pend}
    for ob in (lp, visor):
        for p_ in ob.data.polygons:
            p_.use_smooth = True
        ob.data.set_sharp_from_angle(angle=ANGULO_DURO)
        ob.data.update()
        info[ob.name] = Q.censo(ob)
    return info


def espejar_orejera():
    """Duplica en -X las caras de la orejera derecha, con su misma UV. Se llama
    DESPUES del bake: la copia comparte el detalle horneado de la original."""
    lp = bpy.data.objects[NOMBRE]
    gi = lp.vertex_groups[GRUPO_OREJERA].index
    bm = bmesh.new()
    bm.from_mesh(lp.data)
    dl = bm.verts.layers.deform.verify()
    if any(v.co.x < -0.09 and gi in v[dl] for v in bm.verts):
        bm.free()
        return {"ok": False, "error": "la orejera ya esta espejada"}
    caras = [f for f in bm.faces if all(gi in v[dl] for v in f.verts)]
    dup = bmesh.ops.duplicate(bm, geom=caras)
    nv = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMVert)]
    nf = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMFace)]
    for v in nv:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=nf)
    bm.to_mesh(lp.data)
    bm.free()
    lp.data.update()
    lp.data.calc_loop_triangles()
    return {"ok": True, "caras_copiadas": len(nf), "tris": len(lp.data.loop_triangles)}


def desplegar(margen=0.002):
    """UV con costuras propias. La carcasa (pieza 0) se abre por lo que es: el casquete sobre la banda es un disco; la
    banda con el ala, dos medias coronas cortadas en los costados (bajo los alojamientos de las orejeras, no por el
    rotulo del frente ni por el de la nuca); el interior, otro disco. El resto, por angulo, con la red de seguridad
    de `uv.desplegar`. Hasta 2026-10-11 era `smart_project` (58.9 %)."""
    import uv
    from mathutils import Vector
    ob = bpy.data.objects[NOMBRE]
    for e in ob.data.edges:
        e.use_seam = False
    pieza = [a.value for a in ob.data.attributes["pieza"].data]
    C0 = Vector((0.0, 0.0, CC.Z0 + 0.03))
    zb = CC.Z0 + CC.BANDA_Z + 1.5 * CC.MM

    def clase(f):
        c = f.calc_center_median()
        if f.normal.dot(c - C0) < 0:
            return 9                                     # interior
        if c.z > zb:
            return 0                                     # casquete
        # mitad de delante y mitad de atras: el corte cae en los costados, bajo los alojamientos. Partida por x = 0
        # la costura cruzaba el rotulo del frente (BRUN | DEK en dos islas) y el de la nuca
        return 1 if c.y < CP.ALOJ_Y else 2

    def extra(e):
        if len(e.link_faces) != 2:
            return False
        a, b = e.link_faces
        if pieza[a.index] != 0 or pieza[b.index] != 0:
            return False
        return clase(a) != clase(b)
    # ninguna tira de mas de 120 mm: la banda del arnes, el aro de la careta y el canto del visor (1.3 m por 1 mm)
    # fijaban la escala de todo el atlas (visor al 20 %)
    import lowpoly as L
    tiras = L.costura_tiras(0.12)
    # ...pero la carcasa y las dos caras del visor no son tiras: troceadas salian en ocho gajos y veinte rectangulos
    solo_tiras = lambda e: len(e.link_faces) == 2 and pieza[e.link_faces[0].index] != 0 and tiras(e)
    canto = lambda e: len(e.link_faces) == 2 and max(f.calc_area() for f in e.link_faces) < 2e-5 and tiras(e)
    info = {NOMBRE: uv.desplegar([NOMBRE], margen=margen, angulo_grados=60, extra=L.cualquiera(extra, solo_tiras))}
    info[VISOR] = uv.desplegar([VISOR], margen=margen, angulo_grados=60, extra=canto)
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
