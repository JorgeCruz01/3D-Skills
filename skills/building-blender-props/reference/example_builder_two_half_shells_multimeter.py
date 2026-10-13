"""Multimetro digital de mano, 6000 cuentas, con su funda de goma. Marca ficticia OHMVEX.

Ejes: el aparato esta DE PIE sobre su canto inferior: Z arriba, cara en -Y. Unidades: metros; cotas en milimetros.
Envolvente publicada del aparato de referencia: 180 x 87 x 47 mm (alto x ancho x fondo). Pantalla de 65 x 43 mm.

La FUNDA son dos medias cascaras, delantera y trasera, que se encuentran en el plano medio (y = 0): cada una es un
campo de alturas sobre el mismo contorno de esquinas redondas, algo entallado a media altura. La delantera lleva el
rebaje por el que asoma la cara del aparato; la trasera, el alojamiento del soporte abatible, el de la placa de
caracteristicas y las estrias de agarre. La CARA del aparato es otra lamina, solo del high poly, con la ventana de la
pantalla, el pozo del selector y los alojamientos de las teclas: en la low poly va al mapa de normales.

`q` >= 1: high poly. `q` < 0.5: low poly."""
import math

import bmesh
import bpy
import numpy as np

import formas as F

MM = F.MM
COL = "Model Collection"

ALTO, ANCHO, FONDO = 180.0, 87.0, 47.0
W, H2, D2 = ANCHO / 2, ALTO / 2, FONDO / 2
ZC = H2
Y_BISEL = 0.0                         # plano medio: ahi se encuentran las dos medias fundas
Y_FRENTE = -D2
R_BISEL, RODADO = 14.0, 10.0
ENTALLE = dict(k=0.035, z=-8.0, s=38.0)
# rebaje de la funda por el que asoma la cara del aparato
# `fondo`: high poly, por detras del relieve mas hondo de la cara (si no, el suelo de la funda asoma por el pozo del
# selector). `fondo_lp`: low poly, a la altura de la cara, que se hornea sobre ese suelo dentro de la jaula.
CARA = dict(x=0.0, z=1.0, sx=36.5, sz=79.0, r=8.0, fondo=5.9, fondo_lp=4.9, talud=2.0)
CARA_SX, CARA_SZ, CARA_R = 34.2, 76.7, 6.0
Y_CARA = Y_FRENTE + 4.1
VENTANA = dict(x=0.0, z=48.0, sx=33.2, sz=22.3, r=1.5)       # ventana de la pantalla en la cara
LCD = dict(x=0.0, z=48.0, sx=32.5, sz=21.5)                  # 65 x 43 mm
SELECTOR = dict(x=0.0, z=-27.0, pozo=24.0, r=21.5, angulo=155.0)
TECLAS = [("Rango", -25.5, 11.0, "RAN"), ("Max", -8.5, 11.0, "MAX"), ("Rel", 8.5, 11.0, "REL"), ("Hz", 25.5, 11.0, "HZ")]
TECLA_SX, TECLA_SZ = 6.0, 3.0
REDONDAS = [("Amarilla", -26.0, -1.5, 4.3), ("Azul", 26.0, -1.5, 4.3)]
BORNES = [(-27.0, "10A"), (-9.0, "mA"), (9.0, "COM"), (27.0, "V")]
Z_BORNE = -66.0
# trasera
SOPORTE = dict(x=0.0, z=-12.0, sx=26.0, sz=40.0, r=4.0, fondo=3.0, talud=1.0)
PLACA_R = dict(x=0.0, z=55.0, sx=24.0, sz=17.0, r=2.0, fondo=0.8, talud=0.6)
PLACA = dict(x=0.0, z=55.0, sx=23.4, sz=16.4)
ESTRIAS = dict(z0=-82.0, paso=4.0, n=6, x=28.0, ancho=1.8, fondo=1.0)


def _suave(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _sd(x, z, f, crece=0.0):
    """Distancia con signo a un rectangulo de esquinas redondas: < 0 dentro."""
    r = f["r"] + crece
    qx, qz = np.abs(x - f["x"]) - (f["sx"] + crece - r), np.abs(z - f["z"]) - (f["sz"] + crece - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - r


def _esquinas(x, z, w, h, r):
    x, z = np.asarray(x, float), np.asarray(z, float)
    ax, az = np.abs(x) - (w - r), np.abs(z) - (h - r)
    en = (ax > 0) & (az > 0)
    m = np.maximum(ax, az)
    L = np.hypot(ax, az)
    k = np.where(en, m / np.maximum(L, 1e-9), 1.0)
    xo = np.where(en, np.sign(x) * (w - r + ax * k), x)
    zo = np.where(en, np.sign(z) * (h - r + az * k), z)
    d = np.where(en, r - m, np.minimum(w - np.abs(x), h - np.abs(z)))
    return xo, zo, d


def entalle(z):
    """Factor del ancho a la altura z (respecto al centro): la funda se estrecha un 3,5 % donde se agarra."""
    E = ENTALLE
    return 1.0 - E["k"] * np.exp(-((np.asarray(z, float) - E["z"]) / E["s"]) ** 2)


def distancia_al_borde(x_mundo, z):
    """Distancia al contorno de la funda (mm) de un punto del MUNDO (x, z respecto al centro)."""
    x = np.asarray(x_mundo, float) / entalle(z)
    return _esquinas(x, z, W, H2, R_BISEL)[2]


def _rodar(h, d):
    t = np.clip(d / RODADO, 0.0, 1.0)
    canto = D2 - RODADO
    return canto + (h - canto) * np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1))


def alto_frente(x, z, d=None, fino=True):
    """Lo que sobresale la media funda delantera del plano medio, en mm. (x, z) SIN entallar, respecto al centro."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    h = np.full(x.shape, D2) - CARA["fondo" if fino else "fondo_lp"] * _suave(-_sd(x, z, CARA) / CARA["talud"])
    if fino:        # bajo la cara, el suelo de la funda se hunde 3 mm mas: quedaba 0,2 mm POR DELANTE del pozo del selector
        h = h - 3.0 * _suave((-_sd(x, z, CARA) - 3.0) / 1.5)       # y asomaba: un anillo del color de la funda alrededor del mando
    if d is None:
        d = np.minimum(W - np.abs(x), H2 - np.abs(z))
    return _rodar(h, d)


def alto_tras(x, z, d=None, fino=True):
    """Lo que sobresale la media funda trasera del plano medio."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    h = np.full(x.shape, D2) - SOPORTE["fondo"] * _suave(-_sd(x, z, SOPORTE) / SOPORTE["talud"])
    if fino:
        h = h - PLACA_R["fondo"] * _suave(-_sd(x, z, PLACA_R) / PLACA_R["talud"])
        E = ESTRIAS
        for k in range(E["n"]):
            ze = E["z0"] + k * E["paso"]
            h = h - E["fondo"] * _suave((E["ancho"] / 2 + 0.4 - np.abs(z - ze)) / 0.8) * _suave((E["x"] - np.abs(x)) / 2.0)
    if d is None:
        d = np.minimum(W - np.abs(x), H2 - np.abs(z))
    return _rodar(h, d)


def relieve_cara(x, z):
    """Lo que se hunde la cara del aparato respecto a su plano, en mm. (x, z) del MUNDO, respecto al centro."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    S = SELECTOR
    h = 1.2 * _suave(-_sd(x, z, VENTANA) / 1.0) + 2.0 * _suave((S["pozo"] - np.hypot(x - S["x"], z - S["z"])) / 1.5)
    al = np.zeros(x.shape)
    for _, tx, tz, _r in TECLAS:
        al = np.maximum(al, _suave(-_sd(x, z, dict(x=tx, z=tz, sx=TECLA_SX, sz=TECLA_SZ, r=1.2), 0.8) / 0.6))
    for _, tx, tz, r in REDONDAS:
        al = np.maximum(al, _suave((r + 0.8 - np.hypot(x - tx, z - tz)) / 0.6))
    return h + 0.6 * al


def _yc(x, z):
    return Y_CARA + float(relieve_cara(np.array(x), np.array(z)))


def _lamina3(nombre, Pf, Pb, col, suave=True):
    """Cascara cerrada entre dos rejillas (N, M, 3) en mm: cara vista Pf y trasera Pb. Todo quads."""
    n, m = Pf.shape[:2]
    verts = [tuple(Pf[i, j] * MM) for i in range(n) for j in range(m)] + [tuple(Pb[i, j] * MM) for i in range(n) for j in range(m)]
    o = n * m
    caras = []
    for i in range(n - 1):
        for j in range(m - 1):
            a, b, c, d = i * m + j, (i + 1) * m + j, (i + 1) * m + j + 1, i * m + j + 1
            caras.append((a, b, c, d))
            caras.append((o + d, o + c, o + b, o + a))
    borde = [(i, 0) for i in range(n)] + [(n - 1, j) for j in range(1, m)] + [(i, m - 1) for i in range(n - 2, -1, -1)] + [(0, j) for j in range(m - 2, 0, -1)]
    for k in range(len(borde)):
        (i0, j0), (i1, j1) = borde[k], borde[(k + 1) % len(borde)]
        a, b = i0 * m + j0, i1 * m + j1
        caras.append((a, b, o + b, o + a))
    return F._objeto(nombre, verts, caras, col, suave=suave)


def _lineas(q, rasgos):
    if q >= 0.5:
        return np.linspace(-W, W, 219), np.linspace(-H2, H2, 451)
    rod = (0.0, 0.6, 2.2, 4.8, 7.4, RODADO, R_BISEL)
    xs = {0.0} | {s * (W - v) for v in rod for s in (-1, 1)}
    zs = {s * (H2 - v) for v in rod for s in (-1, 1)} | {float(v) for v in range(-60, 61, 15)}      # y lineas para la curva del entalle
    for f in rasgos:
        for s in (-1, 1):
            xs |= {f["x"] + s * f["sx"], f["x"] + s * (f["sx"] - f["talud"])}
            zs |= {f["z"] + s * f["sz"], f["z"] + s * (f["sz"] - f["talud"])}
    xs = sorted(v for v in xs if -W <= v <= W)
    zs = sorted(v for v in zs if -H2 <= v <= H2)

    def limpia(v):                                           # sin lineas a menos de 0,55 mm unas de otras
        out = [v[0]]
        for a in v[1:]:
            if a - out[-1] > 0.55:
                out.append(a)
        out[-1] = v[-1]
        return np.array(out)
    return limpia(xs), limpia(zs)


def media_funda(nombre, lado, q, col=COL):
    """`lado` = -1: delantera (cara en -Y); +1: trasera."""
    xs, zs = _lineas(q, (CARA,) if lado < 0 else (SOPORTE,))
    X0, Z0 = np.meshgrid(xs, zs, indexing="ij")
    X, Z, d = _esquinas(X0, Z0, W, H2, R_BISEL)
    H = (alto_frente if lado < 0 else alto_tras)(X, Z, d, fino=q >= 0.5)
    Xw = X * entalle(Z)
    Pf = np.stack([Xw, lado * H, Z + ZC], -1)
    Pb = np.stack([Xw, np.full_like(H, -lado * 1.0), Z + ZC], -1)
    return _lamina3(nombre, Pf, Pb, col)


def cara(col=COL):
    """Cara del aparato (solo high poly): lamina con su relieve, portadora del arte."""
    xs, zs = np.linspace(-CARA_SX, CARA_SX, 229), np.linspace(-CARA_SZ, CARA_SZ, 513)
    X0, Z0 = np.meshgrid(xs, zs, indexing="ij")
    X, Z, _d = _esquinas(X0, Z0, CARA_SX, CARA_SZ, CARA_R)
    Zm = Z + CARA["z"]
    Xw = X * entalle(Zm)
    Pf = np.stack([Xw, Y_CARA + relieve_cara(Xw, Zm), Zm + ZC], -1)
    Pb = np.stack([Xw, np.full(X.shape, Y_CARA + 2.4), Zm + ZC], -1)
    return _lamina3("Cara", Pf, Pb, col)


def _plano(nombre, f, y, col, n=(9, 7), fuera=-1):
    """Lamina plana portadora de arte: centro y medias medidas de `f`, cara vista en `y`."""
    xs = np.linspace(f["x"] - f["sx"], f["x"] + f["sx"], n[0])
    zs = np.linspace(f["z"] - f["sz"], f["z"] + f["sz"], n[1])
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    Pf = np.stack([X, np.full(X.shape, y), Z + ZC], -1)
    Pb = np.stack([X, np.full(X.shape, y - fuera * 0.5), Z + ZC], -1)
    return _lamina3(nombre, Pf, Pb, col, suave=False)


def _cil(nombre, r, eje, a, b, n, col, centro, bisel=0.0):
    return F.cil(nombre, r * MM, eje, a * MM, b * MM, n, col, (centro[0] * MM, centro[1] * MM), bisel=bisel * MM, s=2 if bisel else 0)


def _caja(nombre, x, y, z, col):
    return F.caja(nombre, (x[0] * MM, x[1] * MM), (y[0] * MM, y[1] * MM), (z[0] * MM, z[1] * MM), col)


def _bisel(ob, ancho, q, seg=2):
    if q < 0.5 or ancho <= 0:
        return ob
    m = ob.modifiers.new("b", "BEVEL")
    m.width, m.segments, m.limit_method, m.angle_limit = ancho * MM, seg, "ANGLE", math.radians(35)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    return ob


def _revolucion(nombre, perfil, x, z, y0, nt, col, onda=None):
    """Solido de revolucion en torno al eje Y que pasa por (x, z + ZC). `perfil`: (radio, avance hacia el frente desde y0)."""
    verts, caras = [], []
    for k in range(nt):
        t = 2 * math.pi * k / nt
        for r, a in perfil:
            rr = r * (onda(r, a, t) if onda else 1.0)
            verts.append(((x + rr * math.cos(t)) * MM, (y0 - a) * MM, (z + ZC + rr * math.sin(t)) * MM))
    m = len(perfil)
    for k in range(nt):
        for i in range(m - 1):
            if perfil[i][0] == 0.0 and perfil[i + 1][0] == 0.0:
                continue
            a, b = k * m + i, ((k + 1) % nt) * m + i
            caras.append((a, a + 1, b + 1, b))
    return F._objeto(nombre, verts, caras, col, suave=True)


def _girar_y(ob, cx, cz, grados):
    c, s = math.cos(math.radians(grados)), math.sin(math.radians(grados))
    for v in ob.data.vertices:
        dx, dz = v.co.x - cx * MM, v.co.z - cz * MM
        v.co.x, v.co.z = cx * MM + dx * c - dz * s, cz * MM + dx * s + dz * c
    ob.data.update()
    return ob


def piezas(q, col=COL):
    out = {}
    hi = q >= 0.5
    out["Frente"] = media_funda("Frente", -1, q, col)
    out["Trasera"] = media_funda("Trasera", 1, q, col)
    if hi:
        out["Cara"] = cara(col)
        out["LCD"] = _plano("LCD", LCD, Y_CARA + 1.2 - 0.3, col)
    # selector rotativo: disco estriado y barra de agarre, girada a su posicion
    S = SELECTOR
    y0 = Y_CARA + 2.0 + 0.3
    r = S["r"]
    perfil = [(0.0, 0.0), (r, 0.0), (r, 2.4), (r - 1.0, 3.5), (0.0, 3.5)]
    onda = (lambda rr, a, t: 1.0 + (0.012 * math.cos(40 * t) if rr >= r - 0.1 else 0.0)) if hi else None
    out["Selector"] = _revolucion("Selector", perfil, S["x"], S["z"], y0, 320 if hi else 32, col, onda)
    barra = _caja("Selector_Barra", (S["x"] - r + 0.8, S["x"] + r - 0.8), (Y_FRENTE, y0 - 3.0), (S["z"] + ZC - 4.2, S["z"] + ZC + 4.2), col)
    _bisel(barra, 1.2, q, 3)
    out["Selector_Barra"] = _girar_y(barra, S["x"], S["z"] + ZC, S["angulo"])
    if hi:
        marca = _caja("Selector_Marca", (S["x"] - r + 2.0, S["x"] - r + 9.0), (Y_FRENTE - 0.15, Y_FRENTE + 0.4), (S["z"] + ZC - 0.6, S["z"] + ZC + 0.6), col)
        out["Selector_Marca"] = _girar_y(marca, S["x"], S["z"] + ZC, S["angulo"] - 180.0)
    # teclas
    for nm, x, z, rot in TECLAS:
        yn = _yc(x, z)
        o = _caja("Tecla_" + nm, (x - TECLA_SX, x + TECLA_SX), (Y_CARA - 1.3, yn + 1.0), (z + ZC - TECLA_SZ, z + ZC + TECLA_SZ), col)
        out["Tecla_" + nm] = _bisel(o, 0.6, q)
        if hi:
            out["Rotulo_" + nm] = _plano("Rotulo_" + nm, dict(x=x, z=z, sx=TECLA_SX - 0.8, sz=TECLA_SZ - 0.8), Y_CARA - 1.3 - 0.1, col, n=(5, 3))
    for nm, x, z, rr in REDONDAS:
        yn = _yc(x, z)
        out["Tecla_" + nm] = _cil("Tecla_" + nm, rr, "Y", Y_CARA - 1.6, yn + 1.0, F.seg(32, q, 16), col, (x, z + ZC), 0.7 if hi else 0)
    # bornes de seguridad: casquillo con su taladro
    for k, (x, nm) in enumerate(BORNES, 1):
        perfil = [(0.0, -0.6), (5.6, -0.6), (5.6, 2.0), (5.0, 2.5), (2.7, 2.5), (2.1, 1.9), (2.1, 0.2), (0.0, 0.2)]
        out["Borne_%d" % k] = _revolucion("Borne_%d" % k, perfil, x, Z_BORNE, Y_CARA, 48 if hi else 16, col)
        if hi:
            out["Borne_%d_Contacto" % k] = _cil("Borne_%d_Contacto" % k, 1.9, "Y", Y_CARA - 1.0, Y_CARA + 0.4, 24, col, (x, Z_BORNE + ZC))
    # soporte abatible, plegado en su alojamiento de la trasera
    P = SOPORTE
    yf = D2 - P["fondo"]
    out["Soporte"] = _caja("Soporte", (P["x"] - P["sx"] + 0.8, P["x"] + P["sx"] - 0.8), (yf - 0.4, D2), (P["z"] + ZC - P["sz"] + 0.8, P["z"] + ZC + P["sz"] - 0.8), col)
    _bisel(out["Soporte"], 0.8, q)
    if hi:
        L = PLACA
        out["Placa"] = F.caja_rejilla("Placa", np.linspace(L["x"] - L["sx"], L["x"] + L["sx"], 9) * MM, np.array((D2 - PLACA_R["fondo"] - 0.3, D2 - PLACA_R["fondo"] + 0.2)) * MM,
                                      np.linspace(L["z"] + ZC - L["sz"], L["z"] + ZC + L["sz"], 7) * MM, col)
    for o in out.values():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    return out
