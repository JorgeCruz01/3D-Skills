"""Piezas definidas por UN contorno y una funcion de altura, en vez de por una
union de primitivas: una carcasa, el cuerpo de una guitarra, una tabla, una
tapa. Del mismo contorno salen el high poly (muestreo fino) y la low poly
(muestreo grueso), y la low poly nace ya en quads: un loft de secciones
x = cte cuyos lazos dan la vuelta a la pieza.

Condicion: el contorno debe ser "x-simple" (una recta x = cte lo corta en un
solo tramo). Una pieza con dos empunaduras o un cutaway lo cumple; una C no.

Unidades de entrada: las del contorno (milimetros en los props del lote); las
mallas salen multiplicadas por `escala` (0.001 por defecto: metros).
"""
import math

import numpy as np

import formas as F


class Contorno:
    """Contorno cerrado (M,2). `top(x)`, `bot(x)`: extremos del tramo en cada x.
    `dist(P)`: distancia de puntos (N,2) al contorno."""

    def __init__(self, poligono):
        self.P = np.asarray(poligono, float)
        self.x0, self.x1 = float(self.P[:, 0].min()), float(self.P[:, 0].max())
        self._A, self._B = self.P, np.roll(self.P, -1, 0)

    @classmethod
    def de_medio(cls, medio, n=10, vivos=()):
        """De la mitad derecha (x >= 0) de un contorno simetrico, suavizada con spline."""
        M = F.spline(np.asarray(medio, float), n=n, cerrada=False, vivos=vivos)
        return cls(np.concatenate([M, (M[1:-1] * (-1, 1))[::-1]]))

    def tramo(self, x):
        """(bot, top) del corte con la recta x = cte."""
        a, b = self._A, self._B
        m = ((a[:, 0] - x) * (b[:, 0] - x) <= 0) & (a[:, 0] != b[:, 0])
        if not m.any():
            k = int(np.argmin(np.abs(self.P[:, 0] - x)))
            return float(self.P[k, 1]), float(self.P[k, 1])
        t = (x - a[m, 0]) / (b[m, 0] - a[m, 0])
        y = a[m, 1] + t * (b[m, 1] - a[m, 1])
        return float(y.min()), float(y.max())

    def dist(self, P):
        P = np.asarray(P, float)
        AB = self._B - self._A
        L2 = (AB ** 2).sum(1) + 1e-18
        out = np.empty(len(P))
        for i in range(0, len(P), 3000):
            p = P[i:i + 3000, None, :]
            t = np.clip(((p - self._A) * AB).sum(2) / L2, 0, 1)
            out[i:i + 3000] = np.linalg.norm(p - (self._A + t[..., None] * AB), axis=2).min(1)
        return out

    def estaciones(self, nx, margen=0.02):
        """`nx` cotas x apretadas hacia los dos extremos (donde el tramo se cierra)."""
        c, h = (self.x0 + self.x1) / 2, (self.x1 - self.x0) / 2
        return c + h * np.sin(np.linspace(-math.pi / 2 + margen, math.pi / 2 - margen, nx))


class Borde:
    """Solo distancias, a un conjunto de segmentos sueltos: el borde REAL de una
    pieza hecha de varios trozos. Cada trozo se construye con su contorno, pero
    el canto se redondea segun la distancia a este borde, asi que la linea por
    la que dos trozos se tocan no se redondea."""

    def __init__(self, A, B):
        self._A, self._B = np.asarray(A, float), np.asarray(B, float)

    @classmethod
    def de(cls, *partes):
        """`partes`: (contorno, mascara de aristas que SI son borde) ..."""
        A = np.concatenate([c.P[m] for c, m in partes])
        B = np.concatenate([np.roll(c.P, -1, 0)[m] for c, m in partes])
        return cls(A, B)

    dist = None


Borde.dist = Contorno.dist


def canto(d, r, exp=2.0):
    """Perfil del canto: 0 en el borde, 1 a `r` del borde. exp = 2 da un cuarto de circulo."""
    t = np.minimum(d, r) / r
    return (1.0 - (1.0 - t) ** exp) ** (1.0 / exp)


def losa(nombre, cont, col, grosor, r, z0=0.0, xs=None, nx=300, n=60, exp=2.0, cara=None, dorso=None, escala=0.001, borde=None,
         girar=False, pared=0):
    """Losa de caras planas (o las que den `cara(x, y)` y `dorso(x, y)`, cotas z)
    y canto redondeado de radio `r` en las dos caras, con pared vertical entre
    ambos si `r` < grosor / 2. Cada seccion lleva `2 n + 2` puntos. `borde`: de
    donde se mide la distancia para el canto (por defecto, el propio contorno).
    `girar`: el contorno viene como (y, x), para piezas simples por filas."""
    xs = cont.estaciones(nx) if xs is None else xs
    th = np.linspace(0, math.pi, n + 1)
    secs = []
    for x in xs:
        yb, yt = cont.tramo(float(x))
        ys = (yt + yb) / 2 + (yt - yb) / 2 * np.cos(th)
        xx = np.full(n + 1, float(x))
        e = canto((borde or cont).dist(np.stack([xx, ys], -1)), r, exp)
        if borde is None:
            e[0] = e[-1] = 0.0
        zc = cara(xx, ys) if cara else np.full(n + 1, z0 + grosor)
        zd = dorso(xx, ys) if dorso else np.full(n + 1, float(z0))
        zt = zc - r * (1 - e)
        zb = zd + r * (1 - e)
        # `pared`: puntos intermedios en las dos paredes. Sin ellos la tapa de un extremo estrecho sale con
        # columnas de 0.6 x 38 mm (64:1) y partirlas arrastra un lazo por toda la pieza
        w1 = [(x, ys[-1], zt[-1] + (zb[-1] - zt[-1]) * j / (pared + 1)) for j in range(1, pared + 1)]
        w0 = [(x, ys[0], zb[0] + (zt[0] - zb[0]) * j / (pared + 1)) for j in range(1, pared + 1)]
        P = [(x, ys[k], zt[k]) for k in range(n + 1)] + w1 + [(x, ys[k], zb[k]) for k in range(n, -1, -1)] + w0
        P = np.array(P)
        if girar:                       # contorno dado como (y, x): se devuelve a (x, y) y se invierte el giro del lazo
            P = P[::-1, [1, 0, 2]]
        secs.append(P * escala)
    return F.loft(nombre, secs, col)


def placa(nombre, contorno, col, z0, grosor, n=None, bisel=0.0, s=2, escala=0.001):
    """Placa plana de contorno cualquiera (un golpeador, una chapa): prisma con
    las tapas en rejilla de quads. `n`: remuestrea el contorno a ese numero (par) de puntos."""
    import quads as Q
    C = np.asarray(contorno, float)
    if n:
        C = F.remuestrear(C, n, cerrada=True)
    o = F.prisma(nombre, C * escala, (0, 0, z0 * escala), "Z", grosor * escala, col, bisel=bisel * escala, s=s if bisel else 0,
                 por_normal=bool(bisel))
    Q.cuadrar(o)
    return o
