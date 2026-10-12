"""Extintor de polvo ABC de 6 kg, presion incorporada. Marca ficticia IGNIFEX.

Ejes: Z = arriba, eje de la botella en el origen. Frente en -Y (manometro). La
manguera sale por -X y las palancas apuntan a +X. Unidades: metros; cotas en mm.

Publicado (ficha de un 6 kg): botella de 160 mm de diametro, 525 mm de alto total.
La escala la fija el diametro; el alto sale de las proporciones de la foto.
"""
import math

import numpy as np
from mathutils import Matrix

import chapa
import formas as F

MM = F.MM
COL = "Model Collection"

R = 80.0                      # radio de la botella
PARED = 1.5                   # chapa de la botella
# botella, contorno exterior (r, z): fondo embutido concavo, pared, cordon, hombro en ojiva, cuello, collarin
FONDO = [(0, 11), (30, 10.5), (52, 8), (66, 3.2), (71, 0.4), (75, 0), (78.4, 1.6), (80, 5.5)]
CORDON = [(80, 327.2), (80.9, 328.4), (81.1, 330), (80.9, 331.6), (80, 332.8)]
HOMBRO = [(80, 338), (79.2, 350), (76.5, 364), (71.5, 378), (63.5, 391), (53, 401), (42, 407.5), (33, 410.5), (27.5, 411.5)]
CUELLO = [(27.5, 414), (30.5, 414.6), (30.5, 424.4), (27.5, 425), (0, 425)]
ETIQUETA = (168.0, 320.0)     # z0, z1 de la banda impresa
Z_V = 425.0                   # asiento de la valvula

COLUMNA = (16.0, 421.0, 471.0)                 # r, z0, z1
TUERCA = (38.0, 425.0, 435.0)                  # entre caras, z0, z1
BOSS_MANO = dict(r=11.0, y=(-31.0, 0.0), z=450.0)
SALIDA = dict(r=11.5, x=(-37.0, 0.0), z=452.0)
OREJA = dict(x=(-27.0, -8.0), y=(-8.0, 8.0), z=(466.0, 484.6))        # donde pivota la palanca
TORRE = dict(x=(15.0, 33.0), y=(-7.5, 7.5), z=(466.0, 486.6))         # por donde pasa el pasador
PIVOTE = dict(x=-17.5, z=479.6, r=2.6, y=13.6, cabeza=(4.6, 1.5))
VASTAGO = dict(x=4.0, r=3.6, z=(468.0, 486.0))
PASADOR = dict(x=24.0, z=482.5, r=2.3, y=(-16.5, 19.0))
ANILLA = dict(r=12.5, alambre=1.6, caida=math.radians(52))
MANOMETRO = dict(r=19.5, y=(-45.0, -31.0), bisel=(21.2, 17.4, -47.6, -42.6), esfera=-45.0)
FERULA = dict(r=13.0, x=(-65.0, -37.0), z=452.0, dientes=36)
MANGUERA_R = 9.5
X_M = -(R + MANGUERA_R + 3.0)                  # eje de la manguera donde baja pegada al cuerpo
MANGUERA = [(-65, 452), (-86, 452), (-108, 444), (-120, 424), (-119, 398), (-108, 368), (-97.5, 340), (X_M, 318),
            (X_M, 300), (X_M, 132)]            # (x, z) del eje
BOQUILLA = dict(ferula=(11.6, 108.0, 133.0), punta=[(8.0, 108), (10.6, 108), (11.0, 92), (12.0, 50), (12.0, 44), (8.6, 44),        # campana <= 12: a 13.6 entraba 1.1 mm en la botella
                                                     
                                                      (8.6, 64), (8.0, 66)])
ABRAZADERA = dict(z=(136.0, 160.0), banda=(81.9, 79.4), lazo=(12.2, 9.0), hebilla=dict(x=(64.0, 74.0), y=(-56.0, -38.0)))
# palancas de chapa estampada en canal: (x, z) de la cara exterior del alma, ancho y ala en mm
CHAPA = 1.6
PALANCA = dict(camino=[(-26, 487.0), (-10, 487.6), (12, 489.4), (40, 493.8), (72, 500.0), (104, 507.0), (128, 512.6), (142, 517.5), (150, 523.0)],
               ancho=[24, 24, 24, 24.5, 26, 27.5, 28, 27, 23], ala=[11.5, 11.5, 11.5, 10.5, 8.5, 6.5, 4.8, 3.0, 2.0], lado=-1)
ASA = dict(camino=[(-25, 467.0), (-8, 466.6), (14, 465.8), (38, 462.6), (64, 455.2), (90, 446.4), (114, 437.6), (130, 430.6), (139, 425.0)],
           ancho=[27, 27, 27, 27, 27, 27, 26.5, 25, 21], ala=[8.5, 8.5, 8.5, 8.5, 8.5, 8.0, 6.6, 4.0, 2.0], lado=1)
PRECINTO = dict(placa=dict(x=(20.0, 40.0), y=(30.0, 31.3), z=(430.0, 458.0)))


def _mm(*v):
    return tuple(x * MM for x in v)


def _rz(perfil):
    return [(r * MM, z * MM) for r, z in perfil]


def _chaikin(puntos, veces, abierto=True):
    p = np.asarray(puntos, float)
    for _ in range(veces):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        q.append(p[-1])
        p = np.array(q)
    return p


def _remuestrear(p, n):
    p = np.asarray(p, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    t = np.linspace(0, d[-1], n)
    return np.stack([np.interp(t, d, p[:, k]) for k in range(p.shape[1])], -1), t / d[-1]


# ------------------------------------------------------------------ botella

def perfil_botella(q, interior=False):
    v = 3 if q > 0.5 else 1
    fondo = _chaikin(FONDO, v)
    hombro = _chaikin(HOMBRO, v)
    cordon = CORDON if q > 0.5 else []                       # en la low poly el cordon va al mapa de normales
    p = [tuple(x) for x in fondo] + list(cordon) + [tuple(x) for x in hombro] + CUELLO
    if not interior:
        return p
    # pared de 1.5 mm hacia dentro, sin collarin: para medir la capacidad
    P = np.array([tuple(x) for x in fondo] + [tuple(x) for x in hombro] + [(24.0, 414.0), (0, 414.0)], float)
    Q = P.copy()
    Q[:, 0] = np.maximum(P[:, 0] - PARED, 0)
    Q[:, 1] = np.where(P[:, 1] < 20, P[:, 1] + PARED, P[:, 1])
    Q[0, 0] = Q[-1, 0] = 0
    return [tuple(x) for x in Q]


def botella(q, col=COL, nombre="Botella"):
    return F.revolucion(nombre, _rz(perfil_botella(q)), F.seg(144, q, 32), (0, 0, 0), "Z", col)


def etiqueta(q, col=COL):
    z0, z1 = ETIQUETA
    return F.tubo("Etiqueta", (R + 0.25) * MM, (R - 0.5) * MM, (0, 0, z0 * MM), "Z", (z1 - z0) * MM, F.seg(144, q, 32), col)


# ------------------------------------------------------------------ valvula colada

def solidos_valvula(q, col=COL):
    n = F.seg(72, q, 16)
    c, t, b, s = COLUMNA, TUERCA, BOSS_MANO, SALIDA
    o, w = OREJA, TORRE
    return [F.cil("_columna", c[0] * MM, "Z", c[1] * MM, c[2] * MM, n, col),
            F.prisma("_tuerca", F.hexagono(t[0] * MM), (0, 0, t[1] * MM), "Z", (t[2] - t[1]) * MM, col),
            F.cil("_boss_mano", b["r"] * MM, "Y", b["y"][0] * MM, b["y"][1] * MM, n, col, _mm(0, b["z"])),
            F.cil("_salida", s["r"] * MM, "X", s["x"][0] * MM, s["x"][1] * MM, n, col, _mm(0, s["z"])),
            F.caja("_oreja", _mm(*o["x"]), _mm(*o["y"]), _mm(*o["z"]), col, r=3.0 * MM, s=4),
            F.caja("_torre", _mm(*w["x"]), _mm(*w["y"]), _mm(*w["z"]), col, r=2.5 * MM, s=4),
            F.caja("_puente", _mm(-10.0, 17.0), _mm(-6.5, 6.5), _mm(464.0, 478.0), col)]


def cortes_valvula(q, col=COL):
    if q <= 0.5:
        return []
    p, a = PIVOTE, PASADOR
    return [F.cil("_taladro_pivote", (p["r"] + 0.25) * MM, "Y", -12 * MM, 12 * MM, 20, col, _mm(p["x"], p["z"])),
            F.cil("_taladro_pasador", (a["r"] + 0.3) * MM, "Y", -12 * MM, 12 * MM, 20, col, _mm(a["x"], a["z"]))]


# ------------------------------------------------------------------ chapa estampada

def canal(nombre, P, col=COL, q=1.0):
    """Canal de chapa a lo largo de un camino (x, z): alma + dos alas, esquinas redondeadas, todo quads.
    `lado` = -1: alas hacia abajo (palanca); +1: alas hacia arriba (asa)."""
    n = F.seg(84, q, 14)
    k = 4 if q > 0.5 else 1                                    # segmentos por esquina
    cam, t = _remuestrear(_chaikin(P["camino"], 3 if q > 0.5 else 1), n)
    t0 = np.linspace(0, 1, len(P["ancho"]))
    ancho, ala = np.interp(t, t0, P["ancho"]), np.interp(t, t0, P["ala"])
    # punta en cuchara: el ancho se cierra en arco en los ultimos milimetros, como la chapa troquelada
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(cam, axis=0), axis=1))])
    Lr = P.get("punta", 12.0)
    s_ = np.clip((d - (d[-1] - Lr)) / Lr, 0, 1)
    ancho = ancho * np.sqrt(np.maximum(1 - s_ ** 2, 0.22))
    T = np.gradient(cam, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.stack([-T[:, 1], T[:, 0]], -1)                      # normal en el plano XZ, hacia +z
    g, lado = CHAPA, P["lado"]
    secs = []
    for i in range(n):
        w, a = ancho[i] / 2, max(ala[i], g + 0.4)                # con el ala a cero salian caras de 281:1 y triangulos en la low poly
        r_o = max(min(3.2, a - 0.2, w - g - 0.3), g + 0.25)
        r_i = max(r_o - g, 0.25)
        ext, inte = [(-w, a)], [(-w + g, a)]
        for sx in (-1, 1):                                     # esquina exterior e interior, pareadas
            ang = np.linspace(math.pi, math.pi / 2, k + 1) if sx < 0 else np.linspace(math.pi / 2, 0, k + 1)
            cx = sx * (w - r_o)
            ext += [(cx + r_o * math.cos(u), r_o - r_o * math.sin(u)) for u in ang]
            inte += [(cx + r_i * math.cos(u), r_o - r_i * math.sin(u)) for u in ang]
        ext.append((w, a))
        inte.append((w - g, a))
        sec = np.array(ext + inte[::-1], float)                # (y, h): h = 0 en la cara exterior del alma
        x = cam[i, 0] + lado * sec[:, 1] * N[i, 0]
        z = cam[i, 1] + lado * sec[:, 1] * N[i, 1]
        secs.append(np.stack([x, sec[:, 0], z], -1) * MM)
    m = len(secs[0])
    h = m // 2
    verts = np.concatenate(secs)
    caras = []
    for i in range(n - 1):
        a0, b0 = i * m, (i + 1) * m
        for j in range(m):
            caras.append((a0 + j, a0 + (j + 1) % m, b0 + (j + 1) % m, b0 + j))
    for base, rev in ((0, False), ((n - 1) * m, True)):         # tapas: tiras de quads entre exterior e interior
        for j in range(h - 1):
            c = (base + j, base + j + 1, base + m - 2 - j, base + m - 1 - j)
            caras.append(c[::-1] if rev else c)
    if lado * 1 > 0:
        caras = [c[::-1] for c in caras]
    return F._objeto(nombre, verts, caras, col, True)


# ------------------------------------------------------------------ piezas exactas

def _aro(nombre, radio, alambre, n, na, col, matriz):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    cam = np.stack([radio * np.cos(a), radio * np.sin(a), np.zeros(n)], -1) * MM
    ob = F.barrido(nombre, cam, F.perfil_circ(alambre * MM, na), (0, 0, 1), col, cerrado=True)
    ob.data.transform(matriz)
    return ob


def camino_manguera(q):
    p = _chaikin(MANGUERA, 3 if q > 0.5 else 2)
    p, _ = _remuestrear(p, F.seg(120, q, 28))
    return np.stack([p[:, 0], np.zeros(len(p)), p[:, 1]], -1) * MM


def piezas_exactas(q, col=COL):
    hp = q > 0.5
    n = F.seg(72, q, 16)
    o = {"Botella": botella(q, col), "Palanca": canal("Palanca", PALANCA, col, q), "Asa": canal("Asa", ASA, col, q)}
    # pivote remachado y vastago de la valvula
    p = PIVOTE
    eje = F.cil("Pivote", p["r"] * MM, "Y", -p["y"] * MM, p["y"] * MM, F.seg(24, q, 8), col, _mm(p["x"], p["z"]))
    cab = [F.cil("_cab", p["cabeza"][0] * MM, "Y", s * p["y"] * MM, s * (p["y"] + p["cabeza"][1]) * MM if s > 0 else s * p["y"] * MM,
                 F.seg(24, q, 8), col, _mm(p["x"], p["z"])) for s in (1,)]
    cab.append(F.cil("_cab", p["cabeza"][0] * MM, "Y", -(p["y"] + p["cabeza"][1]) * MM, -p["y"] * MM, F.seg(24, q, 8), col, _mm(p["x"], p["z"])))
    o["Pivote"] = F.unir("Pivote", [eje] + cab)
    v = VASTAGO
    o["Vastago"] = F.cil("Vastago", v["r"] * MM, "Z", v["z"][0] * MM, v["z"][1] * MM, F.seg(24, q, 8), col, _mm(v["x"], 0), 0.6 * MM if hp else 0, 2 if hp else 0)
    # pasador de seguridad y su anilla
    a = PASADOR
    pas = F.cil("Pasador", a["r"] * MM, "Y", a["y"][0] * MM, a["y"][1] * MM, F.seg(20, q, 8), col, _mm(a["x"], a["z"]))
    A = ANILLA
    cy = a["y"][1] + A["r"] * math.cos(A["caida"]) + 1.2      # la anilla cuelga por fuera del ala del asa
    cz = a["z"] - A["r"] * math.sin(A["caida"])
    m = Matrix.Translation((a["x"] * MM, cy * MM, cz * MM)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
    ani = _aro("_anilla", A["r"], A["alambre"], F.seg(64, q, 16), F.seg(14, q, 6), col, m)
    o["Pasador"] = F.unir("Pasador", [pas, ani])
    # manometro: caja, bisel y aguja
    M_ = MANOMETRO
    b = BOSS_MANO
    caja = F.cil("Manometro", M_["r"] * MM, "Y", M_["y"][0] * MM, M_["y"][1] * MM, n, col, _mm(0, b["z"]), 1.0 * MM if hp else 0, 2 if hp else 0)
    be = M_["bisel"]
    bis = F.tubo("_bisel", be[0] * MM, be[1] * MM, (0, be[2] * MM, b["z"] * MM), "Y", (be[3] - be[2]) * MM, n, col, 1.2 * MM)
    o["Manometro"] = F.unir("Manometro", [caja, bis])
    # ferula moleteada de la manguera, manguera, boquilla
    f = FERULA
    if hp:
        fer = chapa.moleteado("Ferula", f["r"], "X", f["x"][0], f["x"][1], (0, f["z"]), col, f["dientes"], 0.7)
    else:
        fer = F.cil("Ferula", f["r"] * MM, "X", f["x"][0] * MM, f["x"][1] * MM, n, col, _mm(0, f["z"]))
    o["Ferula"] = fer
    o["Manguera"] = F.barrido("Manguera", camino_manguera(q), F.perfil_circ(MANGUERA_R * MM, F.seg(32, q, 10)), (0, 1, 0), col)
    B = BOQUILLA
    fe = F.cil("Boquilla_Ferula", B["ferula"][0] * MM, "Z", B["ferula"][1] * MM, B["ferula"][2] * MM, n, col, _mm(X_M, 0), 0.8 * MM if hp else 0, 2 if hp else 0)
    o["Boquilla_Ferula"] = fe
    o["Boquilla"] = F.revolucion("Boquilla", _rz(B["punta"]), n, (X_M * MM, 0, 0), "Z", col)
    # abrazadera: banda alrededor de la botella y lazo alrededor de la manguera
    Z = ABRAZADERA
    banda = F.tubo("Abrazadera", Z["banda"][0] * MM, Z["banda"][1] * MM, (0, 0, Z["z"][0] * MM), "Z", (Z["z"][1] - Z["z"][0]) * MM, F.seg(144, q, 32), col, 0.5 * MM if hp else 0)
    lazo = F.tubo("_lazo", Z["lazo"][0] * MM, Z["lazo"][1] * MM, (X_M * MM, 0, Z["z"][0] * MM), "Z", (Z["z"][1] - Z["z"][0]) * MM, F.seg(48, q, 12), col, 0.5 * MM if hp else 0)
    o["Abrazadera"] = F.unir("Abrazadera", [banda, lazo])
    # precinto: placa colgada de la anilla
    pr = PRECINTO["placa"]
    cx, cz = (pr["x"][0] + pr["x"][1]) / 2, (pr["z"][0] + pr["z"][1]) / 2
    cont = F.perfil_rect((pr["x"][1] - pr["x"][0]) * MM, (pr["z"][1] - pr["z"][0]) * MM, 3.0 * MM, 4 if hp else 1)
    o["Precinto"] = F.prisma("Precinto", cont, (cx * MM, pr["y"][0] * MM, cz * MM), "Y", (pr["y"][1] - pr["y"][0]) * MM, col,
                             0.3 * MM if hp else 0, 1 if hp else 0)
    return o
