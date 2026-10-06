"""Cuerpos moldeados por inflado de un perfil: culatas, empunaduras, carcasas ergonomicas.

Un loft de secciones x = cte (`chapa.cuerpo_x`) redondea el techo y el suelo de cada seccion, pero deja vivos los
cantos de los extremos y los de cualquier agujero cortado despues: la pieza se lee como una tabla recortada (asi salio
la culata de la ballesta). Aqui el grosor en cada punto del perfil sale de su distancia al borde:

    medio grosor (x, z) = W (x, z) * canto (d / D)

con `d` la distancia al contorno (agujeros incluidos) y `D` el radio con el que el costado cae hacia el borde. Todos los
bordes, los de dentro tambien, quedan redondos con el mismo radio, y `W` puede cambiar en las dos direcciones (un
abultamiento para la palma, una carrillera mas estrecha que la caja). El resultado es una malla de dos hojas sobre una
rejilla: sirve para colar (`colada.colar`), no como malla final.

Unidades: milimetros de entrada; la malla sale en metros.
"""
import numpy as np

import formas as F

MM = F.MM


def dentro(P, X, Z):
    """Mascara par-impar de los puntos (X, Z) dentro del poligono `P`."""
    P = np.asarray(P, float)
    x, z = X.ravel(), Z.ravel()
    m = np.zeros(x.shape, bool)
    for (x0, z0), (x1, z1) in zip(P, np.roll(P, -1, axis=0)):
        if z0 == z1:
            continue
        c = (z0 > z) != (z1 > z)
        xi = x0 + (z[c] - z0) * (x1 - x0) / (z1 - z0)
        m[c] ^= x[c] < xi
    return m.reshape(X.shape)


def distancia(mask, paso, tope):
    """Distancia (mm) de cada nodo de dentro al nodo de fuera mas cercano, hasta `tope`. Fuerza bruta por desplazamientos."""
    r = int(np.ceil(tope / paso)) + 1
    fuera = np.pad(~mask, r, constant_values=True)
    d2 = np.full(mask.shape, float(r * r + 1))
    n, m = mask.shape
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            q = i * i + j * j
            if q > r * r or q == 0:
                continue
            s = fuera[r + i:r + i + n, r + j:r + j + m]
            np.minimum(d2, np.where(s, q, d2), out=d2)
    return np.where(mask, np.minimum(np.sqrt(d2) * paso - paso / 2, tope), 0.0)


def _difuminar(A, k):
    if k < 1:
        return A
    c = np.cumsum(np.pad(A, ((k + 1, k), (0, 0)), mode="edge"), axis=0)
    A = (c[2 * k + 1:] - c[:-2 * k - 1]) / (2 * k + 1)
    c = np.cumsum(np.pad(A, ((0, 0), (k + 1, k)), mode="edge"), axis=1)
    return (c[:, 2 * k + 1:] - c[:, :-2 * k - 1]) / (2 * k + 1)


def campo(partes, huecos=(), D=12.0, paso=0.5, exp=2.0, difuminado=8.0, extra=None, minimo=0.5, esbeltez=2.2, alisado=3.0):
    """Rejilla del perfil y medio grosor en cada nodo. `partes`: [(poligono (x, z), ancho)], `ancho` = medio ancho, un
    numero o una funcion de x; donde se pisan manda el mayor y la transicion se difumina `difuminado` mm. `huecos`:
    poligonos que se restan. `D`: un numero o una funcion (X, Z). `esbeltez`: tope del medio ancho en semianchos locales del perfil (un liston de 11 mm de alto no sale de 28 de ancho). `extra` (X, Z) -> mm que se suman al medio ancho."""
    todos = np.vstack([np.asarray(p, float) for p, _ in partes])
    x = np.arange(todos[:, 0].min() - paso, todos[:, 0].max() + 2 * paso, paso)
    z = np.arange(todos[:, 1].min() - paso, todos[:, 1].max() + 2 * paso, paso)
    X, Z = np.meshgrid(x, z, indexing="ij")
    mask = np.zeros(X.shape, bool)
    W = np.zeros(X.shape)
    for P, w in partes:
        m = dentro(P, X, Z)
        mask |= m
        W = np.where(m, np.maximum(W, w(X) if callable(w) else w), W)
    for P in huecos:
        mask &= ~dentro(P, X, Z)
    # fuera de las partes el ancho vale el del nodo de dentro mas proximo (si no, el difuminado lo hunde en los bordes)
    lleno = W > 0
    Wd, peso = _difuminar(W, int(difuminado / paso / 2)), _difuminar(lleno.astype(float), int(difuminado / paso / 2))
    W = np.where(peso > 1e-6, Wd / np.maximum(peso, 1e-6), W)
    if extra is not None:
        W = W + extra(X, Z)
    Dm = D(X, Z) if callable(D) else np.full(X.shape, float(D))
    d = distancia(mask, paso, float(Dm.max()))
    # un miembro mas estrecho que 2 D no llega nunca a d = D: su seccion quedaba con una arista en la linea media.
    # Se mide el semiancho local (maximo de d en un entorno de radio D) y el canto se reparte sobre el.
    k = max(int(round(2.0 / paso)), 1)
    ds = d[::k, ::k]
    r = int(np.ceil(float(Dm.max()) / (k * paso)))
    P = np.pad(ds, r)
    loc = ds.copy()
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            if i * i + j * j <= r * r:
                np.maximum(loc, P[r + i:r + i + ds.shape[0], r + j:r + j + ds.shape[1]], out=loc)
    loc = _difuminar(np.repeat(np.repeat(loc, k, axis=0), k, axis=1)[:d.shape[0], :d.shape[1]], k)
    loc = np.maximum(loc, paso)
    Dm = np.minimum(Dm, loc)
    W = np.minimum(W, esbeltez * loc)
    u = np.clip(d / Dm, 0.0, 1.0)
    t = np.where(mask, W * (1 - (1 - u) ** exp) ** (1.0 / exp), 0.0)
    ka = int(round(alisado / paso / 2))
    if ka >= 1:                                  # quita los escalones de la rejilla y las aristas del campo de distancias
        t = _difuminar(_difuminar(t, ka), ka)   # sin normalizar por la mascara: normalizado, el borde sube y el canto vuelve a ser una pared
    return x, z, mask, np.where(mask, np.maximum(t, minimo), 0.0)


def inflar(nombre, partes, col, huecos=(), D=12.0, paso=0.5, exp=2.0, difuminado=8.0, extra=None, y0=0.0, minimo=0.5, esbeltez=2.2, alisado=3.0):
    """Solido de dos hojas (y = y0 +- medio grosor) sobre la rejilla del perfil, cerrado por el canto."""
    x, z, mask, t = campo(partes, huecos, D, paso, exp, difuminado, extra, minimo, esbeltez, alisado)
    idx = -np.ones(mask.shape, int)
    idx[mask] = np.arange(mask.sum())
    n = int(mask.sum())
    I, J = np.nonzero(mask)
    V = np.concatenate([np.column_stack([x[I], y0 + t[I, J], z[J]]), np.column_stack([x[I], y0 - t[I, J], z[J]])]) * MM
    a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
    celda = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    a, b, c, d = a[celda], b[celda], c[celda], d[celda]
    caras = [np.column_stack([a, d, c, b]), np.column_stack([a, b, c, d]) + n]
    C = np.pad(celda, 1)
    # cantos: aristas de la rejilla con celda a un solo lado
    hi, hj = np.nonzero(C[1:-1, 1:] != C[1:-1, :-1])            # arista (i, j)-(i+1, j), entre las celdas (i, j-1) y (i, j)
    p, q = idx[hi, hj], idx[hi + 1, hj]
    caras.append(np.column_stack([p, q, q + n, p + n]))
    vi, vj = np.nonzero(C[1:, 1:-1] != C[:-1, 1:-1])            # arista (i, j)-(i, j+1), entre las celdas (i-1, j) y (i, j)
    p, q = idx[vi, vj], idx[vi, vj + 1]
    caras.append(np.column_stack([p, q, q + n, p + n]))
    caras = np.vstack(caras)
    usados = np.zeros(2 * n, bool)
    usados[caras.ravel()] = True                                 # nodos sueltos (sin celda completa): fuera
    mapa = np.cumsum(usados) - 1
    o = F._objeto(nombre, V[usados].tolist(), mapa[caras].tolist(), col)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o
