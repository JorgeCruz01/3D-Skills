"""Osciloscopio digital de banco, dos canales, 60 MHz. Marca ficticia TRAZKOR.

Ejes: Z arriba, frente en -Y. Unidades: metros; cotas en milimetros.
Envolvente publicada de la clase de aparato: 326,3 x 158,0 x 124,2 mm (ancho x alto x fondo), con mandos y topes.

El FRENTE es una pieza de plastico inyectado: un campo de alturas sobre un rectangulo de esquinas redondas, con la
ventana de la pantalla, el rebaje del panel de mandos, la franja de la marca, la bandeja del puerto USB y, en el high
poly, el alojamiento de cada boton y de cada mando. Sale de la misma funcion en el high poly (rejilla de 0,5 mm) y en
la low poly (lineas en los cambios de forma). Las pieles de la carcasa llevan las ranuras de ventilacion en el high
poly; en la low poly la carcasa es una caja.

`q` >= 1: high poly. `q` < 0.5: low poly."""
import math

import bmesh
import bpy
import numpy as np

import formas as F

MM = F.MM
COL = "Model Collection"

ANCHO, ALTO, FONDO = 326.3, 158.0, 124.2
PIE = 6.0
SALIENTE = 14.1                       # lo que sobresalen los mandos grandes del plano del frente
Y_FRENTE = -FONDO / 2 + SALIENTE      # plano dominante del frente
Y_BISEL = Y_FRENTE + 20.0             # plano trasero del frente de plastico
Y_TRAS = FONDO / 2 - 7.1              # cara trasera de la carcasa; detras, los cuatro topes
R_BISEL, RODADO = 10.0, 4.0
ZC = PIE + (ALTO - PIE) / 2           # centro del frente
H2 = (ALTO - PIE) / 2
# rasgos del frente: centro (x, z respecto al centro del frente), medio ancho, medio alto, radio, fondo (+ hundido) y talud
PANTALLA = dict(x=-77.0, z=6.0, sx=60.0, sz=45.5, r=2.0, fondo=3.5, talud=3.0)
LCD = dict(x=-77.0, z=6.0, sx=57.9, sz=43.45)         # 5,7 pulgadas, 4:3
MARCA = dict(x=-80.0, z=63.5, sx=72.0, sz=5.5, r=0.8, fondo=0.6, talud=0.5)
PANEL = dict(x=83.0, z=2.0, sx=75.0, sz=63.0, r=6.0, fondo=1.6, talud=1.5)
BANDEJA = dict(x=-68.0, z=-64.0, sx=63.0, sz=7.0, r=2.0, fondo=1.0, talud=0.8)
RASGOS = (PANTALLA, MARCA, PANEL, BANDEJA)
# mandos: (nombre, x, z, radio, alto sobre su asiento, estrias)
MANDOS = [("Multi", 28.0, 51.0, 9.0, 13.5, 14), ("Pos_1", 45.0, 20.0, 6.5, 12.0, 10), ("Pos_2", 77.0, 20.0, 6.5, 12.0, 10),
          ("Pos_H", 105.0, 20.0, 6.5, 12.0, 10), ("Nivel", 140.0, 20.0, 6.5, 12.0, 10), ("Volt_1", 45.0, -26.0, 9.5, SALIENTE + 1.6, 14),
          ("Volt_2", 77.0, -26.0, 9.5, SALIENTE + 1.6, 14), ("Seg", 105.0, -26.0, 9.5, SALIENTE + 1.6, 14)]
# botones: (nombre, x, z, medio ancho, medio alto, clave del rotulo impreso en la tecla o None). Medio alto 0 = redondo de radio `sx`
_FILA = (48.0, 64.0, 80.0, 96.0, 112.0, 128.0)
BOTONES = ([("F1_%d" % (i + 1), x, 58.0, 5.5, 3.8, None) for i, x in enumerate(_FILA)] +
           [("F2_%d" % (i + 1), x, 45.0, 5.5, 3.8, r) for i, (x, r) in enumerate(zip(_FILA, ("REF", None, None, None, None, "SEC")))] +
           [("Activar", 146.0, 51.5, 5.5, 4.2, "RUN"), ("Imprimir", 26.0, 26.0, 5.5, 0.0, "IMP"),
            ("Menu_1", 45.0, 0.0, 5.0, 3.5, "CH1"), ("Menu_Mat", 61.0, 0.0, 5.0, 3.5, "MAT"), ("Menu_2", 77.0, 0.0, 5.0, 3.5, "CH2"),
            ("Menu_H", 105.0, 5.0, 5.0, 3.5, "HOR"), ("Cero", 105.0, -6.0, 5.0, 3.5, "CER"),
            ("Disp_1", 140.0, 6.0, 5.0, 3.5, "DIS"), ("Disp_2", 140.0, -5.0, 5.0, 3.5, "M50"), ("Disp_3", 140.0, -16.0, 5.0, 3.5, "FOR"),
            ("Disp_4", 140.0, -27.0, 5.0, 3.5, "VER")] +
           [("Opcion_%d" % (i + 1), -3.0, z, 4.5, 4.0, None) for i, z in enumerate((33.0, 18.0, 3.0, -12.0, -27.0))] +
           [("Sonda", -3.0, -40.0, 3.0, 0.0, None)])
BNC = [("CH1", 45.0), ("CH2", 77.0), ("EXT", 105.0)]
Z_BNC = -52.0
COMP = (132.0, -52.0)                 # terminales de compensacion de sonda
USB = dict(x=-16.0, z=-64.0, sx=6.6, sz=2.8)
CARCASA = dict(x=159.0, z0=8.0, z1=153.0, r=6.0)
RANURAS_TECHO = dict(x=[(-145.0, -78.0), (78.0, 145.0)], y=(-12.0, 38.0), paso=6.0, ancho=2.6, fondo=1.6)
RANURAS_LADO = dict(y=[(-14.0, 40.0)], z=(62.0, 122.0), paso=6.0, ancho=2.6, fondo=1.6)
ASA = dict(x=65.0, y=(2.0, 26.0), z=(152.4, ALTO))
TRASERA = dict(x=90.0, z=(48.0, 118.0))
PLACA = dict(x=-20.0, z=83.0, sx=45.0, sz=22.0)
RED = dict(x=(92.0, 124.0), z=(16.0, 44.0))
USB_B = dict(x=(-128.0, -112.0), z=(60.0, 73.0))
TOPES = [(sx * 141.0, z) for sx in (-1, 1) for z in (24.0, 137.0)]


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


def alto_frente(x, z, d=None, fino=True):
    """Lo que sobresale la cara del frente de su plano trasero, en mm. (x, z) respecto al centro del frente."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    h = np.full(x.shape, Y_BISEL - Y_FRENTE)
    for f in RASGOS:
        h = h - f["fondo"] * _suave(-_sd(x, z, f) / f["talud"])
    if fino:
        al = np.zeros(x.shape)                                # alojamientos de botones y mandos: no se suman entre si
        for _, bx, bz, sx, sz, _r in BOTONES:
            f = dict(x=bx, z=bz, sx=sx, sz=sz or sx, r=sx if not sz else 1.2)
            al = np.maximum(al, _suave(-_sd(x, z, f, 0.9) / 0.6))
        for _, mx, mz, r, _a, _e in MANDOS:
            al = np.maximum(al, _suave((r + 1.0 - np.hypot(x - mx, z - mz)) / 0.6))
        for _, bx in BNC:
            al = np.maximum(al, _suave((8.4 - np.hypot(x - bx, z - Z_BNC)) / 0.6))
        f = dict(x=USB["x"], z=USB["z"], sx=USB["sx"], sz=USB["sz"], r=0.6)
        h = h - 0.8 * al - 4.0 * _suave(-_sd(x, z, f) / 0.7)
    if d is None:
        d = np.minimum(ANCHO / 2 - np.abs(x), H2 - np.abs(z))
    t = np.clip(d / RODADO, 0.0, 1.0)
    canto = Y_BISEL - Y_FRENTE - RODADO
    return canto + (h - canto) * np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1))


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


def _lineas_frente(q):
    w, h = ANCHO / 2, H2
    if q >= 0.5:
        return np.linspace(-w, w, 653), np.linspace(-h, h, 305)
    xs = {-w, w, -w + 1.5, w - 1.5, -w + RODADO, w - RODADO, -w + R_BISEL, w - R_BISEL}
    zs = {-h, h, -h + 1.5, h - 1.5, -h + RODADO, h - RODADO, -h + R_BISEL, h - R_BISEL}
    for f in (PANTALLA, PANEL):                               # la franja de la marca y la bandeja (menos de 1 mm): al mapa de normales
        for s in (-1, 1):
            xs |= {f["x"] + s * f["sx"], f["x"] + s * (f["sx"] - f["talud"])}
            zs |= {f["z"] + s * f["sz"], f["z"] + s * (f["sz"] - f["talud"])}
    xs = sorted(v for v in xs if -w <= v <= w)
    zs = sorted(v for v in zs if -h <= v <= h)

    def limpia(v):                                           # sin lineas a menos de 1,2 mm unas de otras
        out = [v[0]]
        for a in v[1:]:
            if a - out[-1] > 1.2:
                out.append(a)
        out[-1] = v[-1]
        return np.array(out)
    return limpia(xs), limpia(zs)


def frente(q, col=COL):
    xs, zs = _lineas_frente(q)
    X0, Z0 = np.meshgrid(xs, zs, indexing="ij")
    X, Z, d = _esquinas(X0, Z0, ANCHO / 2, H2, R_BISEL)
    H = alto_frente(X, Z, d, fino=q >= 0.5)
    Pf = np.stack([X, Y_BISEL - H, Z + ZC], -1)
    Pb = np.stack([X, np.full_like(H, Y_BISEL + 4.0), Z + ZC], -1)
    return _lamina3("Frente", Pf, Pb, col)


def _yn(x, z):
    """Y nominal de la cara del frente en (x, z): sin los alojamientos."""
    return Y_BISEL - float(alto_frente(np.array(x), np.array(z), fino=False))


def _parche(nombre, f, col, sobre=0.3, n=(13, 7), margen=0.6, y=None):
    """Pieza plana portadora de arte dentro de un rasgo `f`, `sobre` mm por delante de su fondo."""
    xs = np.linspace(f["x"] - f["sx"] + margen, f["x"] + f["sx"] - margen, n[0])
    zs = np.linspace(f["z"] - f["sz"] + margen, f["z"] + f["sz"] - margen, n[1])
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    y0 = (Y_FRENTE + f["fondo"]) if y is None else y
    Pf = np.stack([X, np.full(X.shape, y0 - sobre), Z + ZC], -1)
    Pb = np.stack([X, np.full(X.shape, y0 + 0.5), Z + ZC], -1)
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


def _prisma_y(nombre, w, h, r, seg, cx, cz, y0, y1, col, tramos=1):
    """Prisma de seccion rectangular de esquinas redondas, a lo largo de Y."""
    import quads as Q
    o = F.prisma(nombre, F.perfil_rect(w * MM, h * MM, r * MM, seg), (cx * MM, cz * MM, y0 * MM), "Z", (y1 - y0) * MM, col, tramos=tramos)
    for v in o.data.vertices:                   # nace con su eje en Z: (x, z_local, y) -> (x, y, z)
        xx, yy, zz = v.co
        v.co = (xx, zz, yy)
    o.data.flip_normals()
    Q.cuadrar(o)
    return o


def _revolucion(nombre, perfil, x, z, y0, nt, col, onda=None):
    """Solido de revolucion en torno al eje Y que pasa por (x, z + ZC). `perfil`: (radio, avance hacia el frente desde
    y0). `onda(radio, avance, angulo)` devuelve el factor del radio (estrias del high poly)."""
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
    return F._objeto(nombre, verts, caras, col, suave=True)       # los vertices del eje se sueldan: quedan tapas en abanico


def _mando(nombre, x, z, r, alto, estrias, q, col):
    """Mando estriado con casquete: falda, cuerpo acanalado y tapa algo hundida."""
    y0 = _yn(x, z) + 0.6
    h = alto + 0.6
    perfil = [(0.0, 0.0), (r, 0.0), (r, 0.16 * h), (0.9 * r, 0.2 * h), (0.83 * r, 0.8 * h), (0.74 * r, 0.95 * h), (0.6 * r, h), (0.0, h)]
    hi = q >= 0.5
    onda = (lambda rr, a, t: 1.0 + (0.05 * math.cos(estrias * t) if 0.2 * h <= a <= 0.8 * h else 0.0)) if hi else None
    return _revolucion(nombre, perfil, x, z, y0, (estrias * 8) if hi else 24, col, onda)


def _boton(nombre, x, z, sx, sz, q, col):
    yn = _yn(x, z)
    if not sz:
        o = _cil(nombre, sx, "Y", yn - 2.2, yn + 1.5, F.seg(32, q, 16), col, (x, z + ZC), 0.7 if q >= 0.5 else 0)
    else:
        o = _caja(nombre, (x - sx, x + sx), (yn - 2.2, yn + 1.5), (z + ZC - sz, z + ZC + sz), col)
        _bisel(o, 0.7, q)
    return o


def _rotulo_boton(nombre, x, z, sx, sz, col):
    """Lamina que lleva el rotulo impreso de una tecla, a ras de su cara (solo high poly)."""
    yn = _yn(x, z) - 2.2
    f = dict(x=x, z=z, sx=sx, sz=sz or sx * 0.72)
    return _parche(nombre, f, col, sobre=0.12, n=(5, 5), margen=0.9, y=yn)


def _bnc(nombre, x, q, col, out):
    """Conector BNC hembra de panel: tuerca, cuerpo con sus dos tetones, aislante y vastago."""
    z = Z_BNC
    yn = _yn(x, z)
    hi = q >= 0.5
    perfil = [(0.0, -0.6), (7.2, -0.6), (7.2, 1.8), (6.4, 2.2), (5.6, 2.2), (5.6, 3.0), (4.85, 3.2), (4.85, 11.2), (4.55, 11.5),
              (4.0, 11.5), (4.0, 4.5), (0.0, 4.5)]
    out["BNC_%s" % nombre] = _revolucion("BNC_%s" % nombre, perfil, x, z, yn, 48 if hi else 20, col)
    if hi:
        out["BNC_%s_Aislante" % nombre] = _cil("BNC_%s_Aislante" % nombre, 3.9, "Y", yn - 5.4, yn - 4.2, 32, col, (x, z + ZC))
        out["BNC_%s_Vastago" % nombre] = _cil("BNC_%s_Vastago" % nombre, 0.9, "Y", yn - 6.3, yn - 4.0, 16, col, (x, z + ZC), 0.3)       # corto: mas largo queda fuera de la jaula del horneado
        for k, s in enumerate((-1, 1), 1):
            a, b = sorted((s * 4.4, s * 6.3))
            out["BNC_%s_Teton_%d" % (nombre, k)] = F.cil("BNC_%s_Teton_%d" % (nombre, k), 1.0 * MM, "X", (x + a) * MM, (x + b) * MM, 16, col,
                                                        ((yn - 8.6) * MM, (z + ZC) * MM))


def _piel(nombre, lado, q, col):
    """Piel de la carcasa con sus ranuras de ventilacion (solo high poly). `lado`: 'izq', 'der' o 'techo'."""
    C = CARCASA
    g = 1.0
    if lado == "techo":
        R = RANURAS_TECHO
        us = np.arange(-C["x"] + 9.0, C["x"] - 8.99, 0.5)
        vs = np.arange(Y_BISEL + 8.0, Y_TRAS - 8.99, 0.5)
        U, V = np.meshgrid(us, vs, indexing="ij")
        h = np.zeros_like(U)
        for x0, x1 in R["x"]:
            k = np.round((U - x0) / R["paso"])
            du = np.abs(U - (x0 + k * R["paso"]))
            en = (k >= 0) & (x0 + k * R["paso"] <= x1 + 0.01)
            h = np.maximum(h, np.where(en, _suave((R["ancho"] / 2 + 0.3 - du) / 0.6) * _suave((V - R["y"][0]) / 1.5) * _suave((R["y"][1] - V) / 1.5), 0.0))
        Pf = np.stack([U, V, C["z1"] + g - R["fondo"] * h], -1)
        Pb = np.stack([U, V, np.full_like(U, C["z1"] - 1.2)], -1)
    else:
        R = RANURAS_LADO
        s = -1 if lado == "izq" else 1
        us = np.arange(Y_BISEL + 8.0, Y_TRAS - 8.99, 0.5)
        vs = np.arange(C["z0"] + 9.0, C["z1"] - 8.99, 0.5)
        U, V = np.meshgrid(us, vs, indexing="ij")
        h = np.zeros_like(U)
        for y0, y1 in R["y"]:
            k = np.round((U - y0) / R["paso"])
            du = np.abs(U - (y0 + k * R["paso"]))
            en = (k >= 0) & (y0 + k * R["paso"] <= y1 + 0.01)
            h = np.maximum(h, np.where(en, _suave((R["ancho"] / 2 + 0.3 - du) / 0.6) * _suave((V - R["z"][0]) / 1.5) * _suave((R["z"][1] - V) / 1.5), 0.0))
        Pf = np.stack([s * (C["x"] + g - R["fondo"] * h), U, V], -1)
        Pb = np.stack([np.full_like(U, s * (C["x"] - 1.2)), U, V], -1)
    return _lamina3(nombre, Pf, Pb, col, suave=False)


def piezas(q, col=COL):
    out = {}
    hi = q >= 0.5
    n = F.seg(32, q, 16)
    out["Frente"] = frente(q, col)
    C = CARCASA
    # carcasa trasera: caja de cantos redondos, del frente a la cara trasera
    w, h = 2 * C["x"], C["z1"] - C["z0"]
    car = F.prisma("Carcasa", F.perfil_rect(w * MM, h * MM, C["r"] * MM, 4 if hi else 2), (0, (C["z0"] + C["z1"]) / 2 * MM, (Y_BISEL - 1.0) * MM), "Z",
                   (Y_TRAS - Y_BISEL + 1.0) * MM, col, tramos=6 if hi else 1)
    for v in car.data.vertices:                 # la caja nace con su eje en Z: (x, z_local, y) -> (x, y, z)
        xx, yy, zz = v.co
        v.co = (xx, zz, yy)
    car.data.flip_normals()
    if hi:                                      # las dos tapas son n-gonos alargados: en rejilla
        import quads as Q
        Q.cuadrar(car)
    out["Carcasa"] = car
    if hi:
        for lado in ("izq", "der", "techo"):
            out["Carcasa_Piel_" + lado] = _piel("Carcasa_Piel_" + lado, lado, q, col)
    # asa de transporte, tumbada sobre el techo
    A = ASA
    out["Asa"] = _caja("Asa", (-A["x"], A["x"]), A["y"], A["z"], col)
    _bisel(out["Asa"], 1.8, q, 3)
    if hi:
        for k, s in enumerate((-1, 1), 1):
            out["Asa_Eje_%d" % k] = _caja("Asa_Eje_%d" % k, sorted((s * (A["x"] - 1.0), s * (A["x"] + 9.0))), (A["y"][0] + 4.0, A["y"][1] - 4.0), (A["z"][0] - 0.2, A["z"][0] + 2.2), col)
            _bisel(out["Asa_Eje_%d" % k], 1.0, q)
    # trasera: realce, placa de caracteristicas, entrada de red, puerto USB y cuatro topes
    yt = Y_TRAS
    T = TRASERA
    out["Trasera"] = _caja("Trasera", (-T["x"], T["x"]), (yt - 0.5, yt + 1.6), T["z"], col)
    _bisel(out["Trasera"], 1.0, q)
    R = RED
    out["Red"] = _caja("Red", R["x"], (yt - 0.5, yt + 2.6), R["z"], col)
    _bisel(out["Red"], 0.8, q)
    out["Puerto"] = _caja("Puerto", USB_B["x"], (yt - 0.5, yt + 1.8), USB_B["z"], col)
    _bisel(out["Puerto"], 0.6, q)
    if hi:
        out["Red_Hueco"] = _caja("Red_Hueco", (R["x"][0] + 5.0, R["x"][1] - 5.0), (yt + 2.2, yt + 2.8), (R["z"][0] + 5.0, R["z"][1] - 5.0), col)
        xm, zm = (R["x"][0] + R["x"][1]) / 2, (R["z"][0] + R["z"][1]) / 2
        for k, (px, pz) in enumerate(((xm - 6.0, zm - 2.5), (xm + 6.0, zm - 2.5), (xm, zm + 4.0)), 1):
            out["Red_Patilla_%d" % k] = _caja("Red_Patilla_%d" % k, (px - 0.7, px + 0.7), (yt + 2.6, yt + 4.6), (pz - 2.2, pz + 2.2), col)
        ux, uz = (USB_B["x"][0] + USB_B["x"][1]) / 2, (USB_B["z"][0] + USB_B["z"][1]) / 2
        out["Puerto_Hueco"] = _caja("Puerto_Hueco", (ux - 4.2, ux + 4.2), (yt + 1.5, yt + 2.0), (uz - 3.8, uz + 3.8), col)
        P = PLACA
        out["Placa"] = F.caja_rejilla("Placa", np.linspace(P["x"] - P["sx"], P["x"] + P["sx"], 13) * MM, np.array((yt + 1.4, yt + 1.95)) * MM,
                                      np.linspace(P["z"] - P["sz"], P["z"] + P["sz"], 7) * MM, col)
        for k, (tx, tz) in enumerate(((-148.0, 62.0), (-148.0, 100.0), (148.0, 62.0), (148.0, 100.0)), 1):
            out["Tornillo_%d" % k] = _cil("Tornillo_%d" % k, 3.0, "Y", yt - 0.5, yt + 1.2, 24, col, (tx, tz), 0.5)
            out["Tornillo_%d_Cruz" % k] = _caja("Tornillo_%d_Cruz" % k, (tx - 2.0, tx + 2.0), (yt + 0.9, yt + 1.35), (tz - 0.45, tz + 0.45), col)
    for k, (tx, tz) in enumerate(TOPES, 1):
        out["Tope_%d" % k] = _prisma_y("Tope_%d" % k, 26.0, 26.0, 6.0, 4 if hi else 2, tx, tz, yt - 1.0, FONDO / 2, col)
        _bisel(out["Tope_%d" % k], 2.0, q, 3)
    # patas: dos abatibles delante y dos de goma detras
    for k, s in enumerate((-1, 1), 1):
        out["Pata_%d" % k] = _caja("Pata_%d" % k, sorted((s * 104.0, s * 136.0)), (Y_BISEL + 6.0, Y_BISEL + 34.0), (0.0, C["z0"] + 1.0), col)
        _bisel(out["Pata_%d" % k], 1.5, q)
        out["Pie_%d" % k] = _cil("Pie_%d" % k, 8.0, "Z", 0.0, C["z0"] + 1.0, n, col, (s * 120.0, 38.0), 1.2 if hi else 0)
    # portadores del arte: pantalla, etiqueta de marca y panel de mandos
    if hi:
        out["Pantalla"] = _parche("Pantalla", PANTALLA, col, sobre=0.5, margen=2.6, n=(17, 13))
        out["Etiqueta_Marca"] = _parche("Etiqueta_Marca", MARCA, col, sobre=0.2, margen=0.4, n=(21, 3))
        out["Panel"] = _parche("Panel", PANEL, col, sobre=0.2, margen=1.4, n=(31, 25))
        out["Bandeja"] = _parche("Bandeja", dict(BANDEJA, x=BANDEJA["x"] - 12.0, sx=BANDEJA["sx"] - 13.0), col, sobre=0.15, margen=0.8, n=(17, 3))
    # mandos, botones y conectores
    for nm, x, z, r, alto, est in MANDOS:
        out["Mando_" + nm] = _mando("Mando_" + nm, x, z, r, alto, est, q, col)
    for nm, x, z, sx, sz, rot in BOTONES:
        out["Boton_" + nm] = _boton("Boton_" + nm, x, z, sx, sz, q, col)
        if hi and rot:
            out["Rotulo_" + nm] = _rotulo_boton("Rotulo_" + nm, x, z, sx, sz, col)
    for nm, x in BNC:
        _bnc(nm, x, q, col, out)
    if hi:
        cx, cz = COMP
        for k, dz in enumerate((3.5, -3.5), 1):                 # terminales de compensacion de sonda: dos pletinas
            yn = _yn(cx, cz + dz)
            out["Comp_%d" % k] = _caja("Comp_%d" % k, (cx - 2.2, cx + 2.2), (yn - 2.0, yn + 0.6), (cz + dz + ZC - 0.5, cz + dz + ZC + 0.5), col)
        yu = _yn(USB["x"], USB["z"])
        out["USB_Lengua"] = _caja("USB_Lengua", (USB["x"] - 5.4, USB["x"] + 5.4), (yu + 0.8, yu + 5.0), (USB["z"] + ZC - 1.6, USB["z"] + ZC - 0.4), col)
    for o in out.values():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    return out
