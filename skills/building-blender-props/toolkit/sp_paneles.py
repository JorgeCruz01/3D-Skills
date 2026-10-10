"""Mascaras EXACTAS de paneles dibujados como curvas en coordenadas del modelo (un picado, una etiqueta, una zona
pintada), a partir del mapa de posicion de `substance.posicion`.

    python sp_paneles.py <carpeta del prop> --clase Nogal_Picado --vecina Nogal [--filete 0.9] [--cara 9]

Lee   Texturas/Bakes/POSICION.png + .json  (posicion de cada texel, normalizada a la caja de la malla)
      Texturas/Bakes/paneles.json           {"plano": [0, 2], "normal": 1, "paneles": {nombre: [[u, v], ...] en metros}}
Escribe en Texturas/Bakes/Mascaras/
      MK_<clase>.png    dentro de algun panel (y se resta de MK_<vecina>.png)
      BD_<clase>.png    filete del borde: banda de `--filete` mm de ancho REAL, centrada en el contorno
      PN_<clase>.png    distancia hacia dentro del panel, 0 en el borde y 1 a 6 mm: para degradar desde el borde

Por que existe: partir una pieza en clases por las CARAS del high poly deja la frontera en escalera, y suavizarla
despues (`sp_mascaras.py --suavizar`) redondea esquinas pero no cura un contorno hecho de rectas. Aqui el contorno es
la curva misma, muestreada por texel, y las distancias van en milimetros del modelo, no en pixeles de UV.
`--cara`: el panel solo vale en los costados: texeles a mas de esos milimetros del plano de simetria (coordenada 0
del eje `normal`); 0 lo desactiva.
"""
import json
import os
import sys

import cv2
import numpy as np

ESC = 20.0          # px por mm del lienzo donde se dibujan los paneles


def leer(ruta):
    im = cv2.imdecode(np.fromfile(ruta, np.uint8), cv2.IMREAD_UNCHANGED)
    return im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)


def escribir(ruta, gris):
    cv2.imencode(".png", np.clip(gris * 255.0 + 0.5, 0, 255).astype(np.uint8))[1].tofile(ruta)


def main(carpeta, clase, vecina, filete, cara):
    B = os.path.join(carpeta, "Texturas", "Bakes")
    D = os.path.join(B, "Mascaras")
    caja = json.load(open(os.path.join(B, "POSICION.json")))
    lo, hi = np.array(caja["min"], np.float32), np.array(caja["max"], np.float32)
    pos = leer(os.path.join(B, "POSICION.png"))[..., 2::-1] * (hi - lo) + lo           # metros, (H, W, 3)
    J = json.load(open(os.path.join(B, "paneles.json")))
    iu, iv = J["plano"]
    u, v = pos[..., iu] * 1000.0, pos[..., iv] * 1000.0                                 # mm
    dist = np.full(u.shape, -1e3, np.float32)                                           # distancia con signo al borde, mm
    for nombre, poli in J["paneles"].items():
        P = np.array(poli, np.float32) * 1000.0
        o = P.min(0) - 12.0
        tam = np.ceil((P.max(0) - o + 12.0) * ESC).astype(int)
        lienzo = np.zeros((tam[1], tam[0]), np.uint8)
        cv2.fillPoly(lienzo, [np.round((P - o) * ESC).astype(np.int32)], 255)
        d = (cv2.distanceTransform(lienzo, cv2.DIST_L2, 5) - cv2.distanceTransform(255 - lienzo, cv2.DIST_L2, 5)) / ESC
        mx, my = (u - o[0]) * ESC, (v - o[1]) * ESC
        dentro = (mx >= 0) & (my >= 0) & (mx < tam[0] - 1) & (my < tam[1] - 1)
        s = cv2.remap(d.astype(np.float32), mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderValue=-1e3)
        dist = np.maximum(dist, np.where(dentro, s, -1e3))
    lado = np.ones(u.shape, np.float32)
    if cara > 0:
        # en milimetros desde el plano de simetria (coordenada 0), no en fraccion de la caja: la caja de un fusil la
        # descentra la palanca del cerrojo y el costado derecho se quedaba fuera
        lado = np.clip((np.abs(pos[..., J["normal"]]) * 1000.0 - cara) / 1.5, 0, 1)
    union = np.zeros(u.shape, np.float32)
    for n in (clase, vecina):
        f = os.path.join(D, "MK_%s.png" % n)
        if os.path.exists(f):
            union = np.maximum(union, leer(f))
    panel = np.clip(dist / 0.15 + 0.5, 0, 1) * lado * union                              # borde de 0.15 mm
    escribir(os.path.join(D, "MK_%s.png" % clase), panel)
    escribir(os.path.join(D, "MK_%s.png" % vecina), union * (1 - panel))
    escribir(os.path.join(D, "BD_%s.png" % clase), np.clip(1 - np.abs(dist) / (filete / 2), 0, 1) ** 0.7 * lado * union)
    escribir(os.path.join(D, "PN_%s.png" % clase), np.clip(dist / 6.0, 0, 1) * lado * union)
    print(json.dumps({clase: round(float(panel.mean()) * 100, 2), vecina: round(float((union * (1 - panel)).mean()) * 100, 2),
                      "paneles": list(J["paneles"])}))


if __name__ == "__main__":
    a = sys.argv[2:]
    op = {"--filete": "0.9", "--cara": "9"}
    while a:
        k = a.pop(0)
        op[k] = a.pop(0)
    main(sys.argv[1], op["--clase"], op["--vecina"], float(op["--filete"]), float(op["--cara"]))
