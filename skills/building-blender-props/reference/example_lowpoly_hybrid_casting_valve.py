"""Low poly de la valvula. Se REGENERA: las piezas de fundicion salen de los
mismos volumenes que el high poly, unidos con booleano a baja resolucion y
mecanizados con los cortes que se ven; las piezas exactas, de las mismas
funciones con `q` bajo.

Un solo objeto, un material, un atlas. Las piezas repetidas (tornillos del
bonete, esparragos del prensaestopas) comparten UV: se construye y hornea una
y las demas son replicas.
"""
import math

import bpy

import construir_valvula as CV
import formas as F
import lowpoly as L
import quads as Q

COL = "LP Collection"
NOMBRE = "Valvula_Compuerta_LP"
MM = F.MM
# cortes que se conservan en la LP: los que cambian la silueta o dejan ver el interior
CORTES_LP = {"_cara", "_resalte", "_paso", "_tal", "_techo", "_suelo", "_cavidad", "_cuadro", "_mesilla", "_refr"}
GRUPO_TORNILLO, GRUPO_ESPARRAGO = "Rep_Tornillo", "Rep_Esparrago"


def _vaciar():
    col = bpy.data.collections[COL]
    for o in list(col.all_objects):
        d = o.data
        bpy.data.objects.remove(o)
        if d and d.users == 0:
            bpy.data.meshes.remove(d)


def costura_extra(e):
    """Costuras propias de la valvula."""
    a, b = e.verts[0].co, e.verts[1].co
    tol = 0.15 * MM
    # cupula y cuello del bonete, partidos por x = 0 y por y = 0: en una pieza o en
    # dos mitades se pisaban al desplegar (medido: 719 celdas); en cuartos, no
    if abs(a.x) < tol and abs(b.x) < tol and all(89 * MM < p.z < 148 * MM and abs(p.y) > 12 * MM for p in (a, b)):
        return True
    if abs(a.y) < tol and abs(b.y) < tol and all(89 * MM < p.z < 148 * MM and abs(p.x) > 5 * MM for p in (a, b)):
        return True
    # base del cuello: donde la cupula asoma por los extremos del cuello, pared y
    # cupula se unen casi a ras y quedaban en la misma isla, plegada sobre si misma
    zc = CV.Z_CUELLO[0] * MM
    if abs(a.z - zc) < tol and abs(b.z - zc) < tol:
        return True
    # aro del volante: ecuador interior y exterior (queda en mitad de arriba y de abajo)
    z = CV.Z_ARO * MM
    if abs(a.z - z) > tol or abs(b.z - z) > tol:
        return False
    ra, rb = math.hypot(a.x, a.y), math.hypot(b.x, b.y)
    return all(abs(r - CV.R_ARO * MM) > 4.0 * MM and r > 40 * MM for r in (ra, rb))


def _cuerpo(q):
    """Cuerpo sin booleanos. Tubo, cubos conicos, resaltes y paso son UNA
    revolucion con el taladro en su perfil. Cada brida son cuatro sectores de
    placa con su taladro pasante (`F.anillo_radial` + `F.prisma_anillo`).
    Camara, panza y brida ovalada cruzan el tubo."""
    import numpy as np
    C = CV
    n = 4 * F.seg(24, q, 4)
    XF, RES, B = C.XF, C.RES, C.B
    xb = XF - RES - B                                   # 57: dorso de la brida
    rr = C.D2 / 2                                       # 51: resalte
    perfil = [(C.DN / 2, -XF), (rr, -XF), (rr, -xb), (C.R_CUBO, -xb), (C.R_TUBO, -40), (C.R_TUBO, 40), (C.R_CUBO, xb), (rr, xb),
              (rr, XF), (C.DN / 2, XF)]
    s = [F.revolucion("_tubo", [(r * MM, (x + XF) * MM) for r, x in perfil], n, CV._mm(-XF, 0, 0), "X", COL)]
    r0, r1, k = rr - 1.0, C.D / 2, n // 4
    for lado in (1, -1):
        x0 = (xb if lado > 0 else -(XF - RES)) * MM
        for i in range(4):
            a0 = math.pi / 2 * i
            arco = [a0 + math.pi / 2 * j / k for j in range(k + 1)]
            # por dentro el sector se cierra con una cuerda, no con el arco: desde el taladro el arco interior se tapa a si
            # mismo en sus extremos (el contorno deja de ser estrellado y los quads se doblan). La cuerda queda dentro del resalte.
            ext = [(r1 * math.cos(a), r1 * math.sin(a)) for a in arco] + [(r0 * math.cos(a), r0 * math.sin(a)) for a in (arco[-1], arco[0])]
            ac = a0 + math.pi / 4
            cy, cz = C.D1 / 2 * math.cos(ac), C.D1 / 2 * math.sin(ac)
            tal = [(cy + C.D_TAL / 2 * math.cos(t), cz + C.D_TAL / 2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
            E, I = F.anillo_radial(np.array(ext) * MM, np.array(tal) * MM, fundir=4.0)
            s.append(F.prisma_anillo("_brida", E, I, (x0, 0, 0), "X", (XF - RES - xb) * MM, COL))
    s.append(F.prisma("_camara", F.superelipse(C.CH_X * MM, C.CH_Y * MM, n, C.CH_EXP), CV._mm(0, 0, -6), "Z", 70 * MM, COL, suave=True))
    s.append(CV._elipsoide("_panza", CV._mm(*C.PANZA[:3]), CV._mm(0, 0, C.PANZA[3]), n, COL))
    s.append(CV._ovalo("_brida_ov", C.OV_X, C.OV_Y, C.OV_EXP, C.Z_OV_C, n, COL))
    # el mecanizado del techo (z = 74) aplana tambien lo alto de las dos bridas de tuberia, que llegan a 82.5:
    # sin esto la low poly las dejaba redondas (silueta frontal 1.6 %, fidelidad 4.8)
    zt = C.Z_OV_C[1] * MM
    for o in s:
        for v in o.data.vertices:
            if v.co.z > zt:
                v.co.z = zt
    return s


def _bonete(q):
    """Bonete: los solidos del high poly ya recortados a sus caras mecanizadas."""
    import numpy as np
    C = CV
    n = 4 * F.seg(24, q, 4)
    s = [CV._ovalo("_bon_brida", C.OV_X, C.OV_Y, C.OV_EXP, (C.Z_OV_B[0], C.Z_OV_B[1] + 1), n, COL)]
    secs = []
    for z, ax, ay, e in ((87.0, 28.0, 56.0, 2.6), (100.0, 27.0, 50.0, 2.5), (116.0, 24.0, 36.0, 2.3), (128.0, 22.0, 26.0, 2.1),
                         (137.0, 21.0, 22.0, 2.0)):
        p = F.superelipse(ax * MM, ay * MM, n, e)
        secs.append(np.concatenate([p, np.full((n, 1), z * MM)], 1))
    s.append(CV._loft("_bon_domo", secs, COL))
    s.append(CV._ovalo("_bon_cuello", C.CUELLO_X, C.CUELLO_Y, C.CUELLO_EXP, C.Z_CUELLO, n, COL))
    s.append(CV._caja("_bon_mesilla", (16, 28.0), (-C.PLACA_W / 2 - 3, C.PLACA_W / 2 + 3),
                      (C.PLACA_Z - C.PLACA_H / 2 - 3, C.PLACA_Z + C.PLACA_H / 2 + 3), COL))
    return s


def _prensa(q):
    C = CV
    n = F.seg(80, q, 14)
    return [CV._ovalo("_pr_brida", C.CUELLO_X, C.CUELLO_Y, C.CUELLO_EXP, C.Z_PRENSA, n, COL),
            CV._cil("_pr_boss", 13.0, "Z", C.Z_PRENSA[1] - 2, C.Z_PRENSA_BOSS, n, COL)]


def _volante(q):
    s = CV.solidos_volante(q, COL)
    cubo = s[1]                                         # cubo recortado a sus dos caras
    d = cubo.data
    bpy.data.objects.remove(cubo)
    bpy.data.meshes.remove(d)
    s[1] = CV._cil("_vol_cubo", 16.0, "Z", CV.Z_CUBO[0], CV.Z_CUBO[1], F.seg(64, q, 12), COL)
    return s


QUADS = {"Cuerpo_Piel": 9500, "Volante_LP": 3500}
# Solo se funde lo que es colada con acuerdos grandes y sin canto mecanizado a la vista: el cuerpo entre bridas (tubo,
# cubos conicos, camara y panza, con el paso y la camara de la cuna abiertos) y el volante. QuadriFlow no sigue un
# canto mecanizado redondeado a 0.5 mm (lo cruza y sale ondulado) y no admite la malla cortada sin remallar ("needs
# to be manifold"): bridas, resaltes, bonete y prensaestopas se CONSTRUYEN, como hasta ahora.
CORTES_FORMA = {"Cuerpo_Piel": ("_paso", "_cavidad"), "Volante_LP": ("_suelo", "_techo")}
FUENTES = {"Cuerpo_Piel": ("solidos_cuerpo", "cortes_cuerpo"), "Volante_LP": ("solidos_volante", "cortes_volante")}
VIVOS = {"Cuerpo_Piel": 32, "Volante_LP": 32}
# relajar (suavizar y volver a pegar) alisa los lazos de una piel sin escalones; en el cuerpo, el escalon de 2-4 mm
# del fondo de la camara sobre la panza salia desgarrado: cada vertice saltaba a un lado u otro del canto
RELAJAR = {"Cuerpo_Piel": 0, "Volante_LP": 2}
FUERA = {"Cuerpo_Piel": ("_brida", "_brida_ov")}


def _borrar(o):
    d = o.data
    bpy.data.objects.remove(o)
    if d.users == 0:
        bpy.data.meshes.remove(d)


def _fundida(nombre, info):
    """Una pieza de fundicion, de UNA piel: los solidos del high poly fundidos por voxeles con sus radios de colada,
    con los cortes que se ven, y remallados en quads (QuadriFlow). Hasta 2026-10-10 eran solidos cruzados: el
    encuentro de la camara con el tubo y con la panza y el de los radios con el aro eran aristas vivas, con todo
    el radio de colada fiado al mapa de normales."""
    import bmesh
    import tela as T
    fs, fc = FUENTES[nombre]
    solidos, cortes = getattr(CV, fs)(1.0, COL), getattr(CV, fc)(1.0, COL)
    for o in [x for x in solidos if x.name.split(".")[0] in FUERA.get(nombre, ())]:
        solidos.remove(o)
        _borrar(o)
    forma = [c for c in cortes if c.name.split(".")[0] in CORTES_FORMA[nombre]]
    for c in cortes:
        if c not in forma:
            _borrar(c)
    if nombre == "Cuerpo_Piel":
        # la camara de la cuna del high poly (76 mm de ancho hasta z = -38) asoma por la panza en sus dos esquinas de
        # abajo: aqui se abre solo lo que se ve desde el paso
        for c in [x for x in forma if x.name.split(".")[0] == "_cavidad"]:
            forma.remove(c)
            _borrar(c)
        forma.append(CV._caja("_cavidad", (-CV.CAV_X, CV.CAV_X), (-30, 30), (-30, 60), COL))
    lisa = F.fundir("_lisa_" + nombre, list(solidos), 0.8e-3, suavizado=8)
    F.mecanizar(lisa, forma)
    lisa = F.fundir("_lisa_" + nombre, [lisa], 0.6e-3, suavizado=2)        # estanca otra vez: QuadriFlow lo exige
    o = T.diezmar(nombre, lisa, 160000, COL)
    r = Q.retopo(o, QUADS[nombre], vivos=VIVOS[nombre], escala=10.0)
    a = Q.ajustar(o, [lisa])
    for _ in range(RELAJAR[nombre]):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.to_mesh(o.data)
        bm.free()
        a = Q.ajustar(o, [lisa])
    info[nombre] = {"censo": {k: r[k] for k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}, "ajuste": a, "desvio": Q.desvio(o, [lisa])}
    _borrar(lisa)
    if nombre == "Cuerpo_Piel":
        # el cubo conico acaba justo en el dorso de la brida (x = 57) con el canto redondeado: se estira 4 mm hacia
        # dentro de la brida para que el encuentro sea un corte limpio y no una linea ondulada
        for v in o.data.vertices:
            ax = abs(v.co.x) / MM
            if ax > 50:
                v.co.x += (1 if v.co.x > 0 else -1) * min(4.0, (ax - 50) * 4.0 / 6.0) * MM
    return o


def _cuerpo_mecanizado(q):
    """Lo mecanizado del cuerpo, construido: las dos bridas de tuberia en sectores con su taladro, el resalte con el
    paso y la brida ovalada con el techo plano. Cruzan la piel fundida en rincones concavos."""
    s = _cuerpo(q)
    for o in [x for x in s if x.name.split(".")[0] in ("_tubo", "_camara", "_panza")]:
        s.remove(o)
        _borrar(o)
    C = CV
    xb = C.XF - C.RES - C.B
    n = 4 * F.seg(24, q, 4)
    for lado in (1, -1):
        x0 = (xb + 0.5) if lado > 0 else -C.XF
        s.append(F.tubo("_resalte", C.D2 / 2 * MM, C.DN / 2 * MM, CV._mm(x0, 0, 0), "X", (C.XF - xb - 0.5) * MM, n, COL))
    return s


def construir(q=0.45, aspecto=16.0, fundir=True):
    """100 % quads. `fundir`: la colada del cuerpo y el volante como pieles de una pieza; False = todo solidos
    cruzados (hasta 2026-10-10)."""
    _vaciar()
    info = {}
    if fundir:
        partes = [_fundida("Cuerpo_Piel", info), Q.ensamblar("Cuerpo_LP", _cuerpo_mecanizado(q), aspecto=aspecto),
                  Q.ensamblar("Bonete_LP", _bonete(q), aspecto=aspecto), Q.ensamblar("Prensaestopas_LP", _prensa(q), aspecto=aspecto),
                  _fundida("Volante_LP", info)]
    else:
        partes = [Q.ensamblar("Cuerpo_LP", _cuerpo(q), aspecto=aspecto), Q.ensamblar("Bonete_LP", _bonete(q), aspecto=aspecto),
                  Q.ensamblar("Prensaestopas_LP", _prensa(q), aspecto=aspecto), Q.ensamblar("Volante_LP", _volante(q), aspecto=aspecto)]
    pend = {"cuerpos": [(o.get("sin_resolver"), o.get("ocultas")) for o in partes], "fundidas": info}
    CV.SIN_BOOLEANO = True
    try:
        ex = CV.piezas_exactas(q, COL)
    finally:
        CV.SIN_BOOLEANO = False
    # de las piezas repetidas se queda una: tornillo 1 y esparrago 1 con su arandela y tuerca
    rep_t = [o for n, o in ex.items() if n.startswith("Tornillo_Bonete_1")]
    rep_e = [o for n, o in ex.items() if n.startswith("Esparrago_Prensa_1")]
    for n, o in list(ex.items()):
        if n.startswith(("Tornillo_Bonete_", "Esparrago_Prensa_")) and o not in rep_t and o not in rep_e:
            d = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d)
            del ex[n]
    for n, o in ex.items():
        r = Q.cuadrar(o)
        Q.tramar(o, aspecto)
        if r["sin_resolver"] or r["tris"] or r["ngonos"]:
            pend[n] = (r["sin_resolver"], r["tris"], r["ngonos"])
    L.marcar(rep_t, GRUPO_TORNILLO)
    L.marcar(rep_e, GRUPO_ESPARRAGO)
    partes += list(ex.values())
    # placa sin remaches: van al normal
    hp = bpy.data.objects.get("Placa")
    x = min(v.co.x for v in hp.data.vertices) if hp else 0.0282
    partes.append(F.prisma("Placa_LP", F.perfil_rect(CV.PLACA_W * MM, CV.PLACA_H * MM), (x, 0, CV.PLACA_Z * MM), "X",
                           0.8 * MM, COL))
    Q.tramar(partes[-1], aspecto)
    mat = bpy.data.materials.get("LP_Valvula") or bpy.data.materials.new("LP_Valvula")
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


def replicar():
    x0, y0 = CV.TORN[0]
    return L.replicar(NOMBRE, {
        GRUPO_TORNILLO: [((x - x0) * MM, (y - y0) * MM, 0.0) for x, y in CV.TORN[1:]],
        GRUPO_ESPARRAGO: [(0.0, -2 * CV.PRENSA_Y * MM, 0.0)],
    })


def desplegar(margen=0.002):
    """UV con costuras por pieza. Las dos pieles remalladas no tienen lazos que seguir: la del cuerpo se abre por el
    plano y = 0 (dos medias conchas) con el paso y la camara aparte; el volante, en mitad de arriba y mitad de abajo.
    Lo construido conserva sus costuras de siempre (`costura_extra`) y el corte por angulo."""
    import uv
    ob = bpy.data.objects[NOMBRE]
    for e in ob.data.edges:
        e.use_seam = False
    pieza = [a.value for a in ob.data.attributes["pieza"].data]
    nombres = ob["piezas"].split(",")
    k_piel, k_vol = nombres.index("Cuerpo_Piel"), nombres.index("Volante_LP")

    def clase_piel(f):
        c, n = f.calc_center_median(), f.normal
        r = math.hypot(c.y, c.z)
        if abs(c.x) < 11 * MM and abs(c.y) < 31 * MM and c.z > -31 * MM and abs(n.x) > 0.5 and r > 20 * MM:
            return 3                                     # paredes de la camara de la cuna
        if r < 27 * MM and (c.y * n.y + c.z * n.z) < 0:
            return 2 if c.x > 0 else 4                   # paso
        if abs(c.x) > 56 * MM and abs(n.x) > 0.7:
            return 5 if c.x > 0 else 6                   # tapas enterradas en las bridas
        return 0 if c.y > 0 else 1

    def extra(e):
        if len(e.link_faces) != 2:
            return costura_extra(e)
        a, b = e.link_faces
        pa, pb = pieza[a.index], pieza[b.index]
        if pa != pb:
            return False
        if pa == k_piel:
            return clase_piel(a) != clase_piel(b)
        if pa == k_vol:
            return (a.normal.z > 0) != (b.normal.z > 0)
        return costura_extra(e)
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
