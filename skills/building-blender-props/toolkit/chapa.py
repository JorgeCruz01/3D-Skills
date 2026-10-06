"""Cuerpos de perfil con seccion propia: cajones de chapa, armazones, culatas.

Una `piel.losa` es un contorno con el canto redondo: sirve para una tabla y se
lee pobre en un arma o en una carcasa (asi salio el primer subfusil). Aqui el
contorno de perfil (x, z) solo da el suelo y el techo en cada x; la seccion
(costados planos, hombros con su radio arriba y abajo, ancho que cambia a lo
largo) se da aparte. Del mismo contorno salen el high poly (estaciones finas,
para colar y cortar con `colada.colar`) y la low poly (pocas estaciones, sin
cortes), que nace en quads.

Unidades: milimetros de entrada; las mallas salen en metros.
"""
import math

import numpy as np

import formas as F
import piel

MM = F.MM


def seccion(w, zb, zt, R, rb, n, nb, lado=1, techo=2):
    """Seccion (y, z): costados planos a +-w, hombros de radio `R` arriba y `rb` abajo. Numero de puntos fijo
    y par: 2 (n + 1) + 2 (nb + 1) + 2 lado + 2 techo."""
    h = max(zt - zb, 0.02)
    zt = zb + h
    w = max(w, 0.02)
    R, rb = min(R, 0.45 * h, 0.9 * w), min(rb, 0.45 * h, 0.9 * w)
    P = [(w - rb + rb * math.cos(a), zb + rb + rb * math.sin(a)) for a in np.linspace(-math.pi / 2, 0, nb + 1)]
    P += [(w, zb + rb + (h - rb - R) * k / (lado + 1)) for k in range(1, lado + 1)]
    P += [(w - R + R * math.cos(a), zt - R + R * math.sin(a)) for a in np.linspace(0, math.pi / 2, n + 1)]
    P += [((w - R) * (1 - 2 * k / (techo + 1)), zt) for k in range(1, techo + 1)]
    P += [(-y, z) for y, z in P[:nb + 1 + lado + n + 1][::-1]]
    P += [(-(w - rb) * (1 - 2 * k / (techo + 1)), zb) for k in range(1, techo + 1)]
    return np.array(P)


def _f(v, x):
    return v(x) if callable(v) else v


def cuerpo_x(nombre, cont, col, w, R, rb, xs, n, nb, lado=1, techo=2, rx=0.0, dz=0.0, zb=None, y0=0.0):
    """Loft de secciones x = cte sobre un contorno de perfil (`piel.Contorno`). `w`, `R`, `rb` pueden ser funciones
    de x. `rx`: los dos extremos se cierran con ese radio en planta. `dz`: resalte (la seccion crece `dz` en ancho
    y techo; para nervios y tapas). `zb`: suelo fijo en vez del del contorno. `y0`: centro de la seccion."""
    secs = []
    for x in xs:
        b, t = cont.tramo(float(x))
        d = min(x - cont.x0, cont.x1 - x)
        e = dz(x) if callable(dz) else dz
        mete = rx * (1 - float(piel.canto(np.array([max(d, 0.0)]), rx)[0])) if rx > 0 else 0.0
        S = seccion(_f(w, x) + e - mete, b if zb is None else zb, t + e, _f(R, x) + e, _f(rb, x), n, nb, lado, techo)
        secs.append(np.column_stack([np.full(len(S), float(x)), S[:, 0] + y0, S[:, 1]]) * MM)
    return F.loft(nombre, secs, col)


def estaciones(cont, fino, paso=0.6, extra=(), tramo_lp=22.0, minimo_lp=1.6):
    """Cotas x: cada `paso` en el high poly; en la low poly, los vertices del contorno y una cada `tramo_lp`.
    Un extremo en punta (el contorno acaba en un vertice) daria una tapa sin area: se entra 0.6 mm."""
    a, b = cont.x0, cont.x1
    if fino:
        xs = np.concatenate([np.arange(a, b, paso), [b], cont.P[:, 0], a + np.array([0.05, 0.15, 0.3]), b - np.array([0.05, 0.15, 0.3])])
        return np.unique(np.round(xs, 3))
    xs = sorted(set(np.round(np.concatenate([cont.P[:, 0], [a, b], list(extra)]), 3)))
    out = [xs[0]]
    for x in xs[1:]:
        if x - out[-1] < minimo_lp and x != xs[-1]:
            continue
        k = int(math.ceil((x - out[-1]) / tramo_lp))
        out += [out[-1] + (x - out[-1]) * j / k for j in range(1, k + 1)]
    alto = lambda x: cont.tramo(float(x))[1] - cont.tramo(float(x))[0]
    if alto(out[0]) < 0.5:
        out[0] += 0.6
    if alto(out[-1]) < 0.5:
        out[-1] -= 0.6
    return np.array(out)


def prisma_y(nombre, P, y0, y1, col, tramos=1, bisel=0.0, s=0):
    """Prisma de un contorno (x, z) entre dos cotas de Y: placas, palancas y cortadores pasantes."""
    return F.prisma(nombre, np.asarray(P, float) * (-1, 1) * MM, (0, y0 * MM, 0), "Y", (y1 - y0) * MM, col, tramos=tramos, bisel=bisel * MM, s=s,
                    por_normal=bool(bisel))


def prisma_z(nombre, P, z0, z1, col, tramos=1, bisel=0.0, s=0):
    """Prisma de un contorno en planta (x, y) entre dos cotas de Z."""
    return F.prisma(nombre, np.asarray(P, float) * MM, (0, 0, z0 * MM), "Z", (z1 - z0) * MM, col, tramos=tramos, bisel=bisel * MM, s=s,
                    por_normal=bool(bisel))


def linea(p0, p1, paso=0.5, r=1.0):
    """Puntos de un tramo recto, apretados en las puntas (para `surco`)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    s = np.unique(np.concatenate([np.linspace(0, min(r, L / 2), 7), np.arange(r, L - r, paso), L - np.linspace(0, min(r, L / 2), 7)]))
    return p0 + (p1 - p0) * (s / L)[:, None]


def surco(nombre, eje, r, col, n=16):
    """Cortador de un surco: circulos horizontales (x, y) a lo largo de `eje` (K, 3), con las puntas redondeadas.
    El eje debe subir o bajar (no vale para un surco horizontal)."""
    E = np.asarray(eje, float)
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(E, axis=0), axis=1))])
    secs = []
    for i in range(len(E)):
        d = min(L[i], L[-1] - L[i])
        rr = max(r * math.sqrt(max(1 - (1 - min(d, r) / r) ** 2, 0.0)), 0.04)
        secs.append(np.column_stack([E[i, 0] + rr * np.cos(a), E[i, 1] + rr * np.sin(a), np.full(n, E[i, 2])]) * MM)
    return F.loft(nombre, secs, col)


def anillos(r, alto, k, fino=True):
    """Perfil (r, h) de un boton torneado con `k` surcos concentricos en la cara."""
    if not fino:
        return [(0, 0), (r, 0), (r, alto * 0.8), (r * 0.86, alto), (0, alto)]
    P = [(0, 0), (r, 0), (r, alto * 0.72), (r * 0.9, alto * 0.95)]
    paso = r * 0.86 / (k + 0.6)
    for i in range(k):
        ro = r * 0.86 - i * paso
        P += [(ro, alto * 0.95 + i * alto * 0.035), (ro - paso * 0.45, alto * 0.95 + i * alto * 0.035), (ro - paso * 0.6, alto * 0.78 + i * alto * 0.035),
              (ro - paso * 0.85, alto * 0.78 + i * alto * 0.035)]
    P += [(paso * 0.5, alto * 1.08), (0, alto * 1.08)]
    return P


def moleteado(nombre, r, eje, a, b, centro, col, dientes=40, fondo=0.5, n_por=4):
    """Anillo moleteado: prisma de contorno dentado (estrias rectas) entre las cotas a y b de `eje`."""
    t = np.linspace(0, 2 * math.pi, dientes * n_por, endpoint=False)
    rr = r - fondo * (0.5 - 0.5 * np.cos(t * dientes)) ** 0.6
    C = np.column_stack([rr * np.cos(t), rr * np.sin(t)]) * MM
    o = {"X": (a * MM, centro[0] * MM, centro[1] * MM), "Y": (centro[0] * MM, a * MM, centro[1] * MM), "Z": (centro[0] * MM, centro[1] * MM, a * MM)}[eje]
    return F.prisma(nombre, C, o, eje, (b - a) * MM, col, suave=True)
