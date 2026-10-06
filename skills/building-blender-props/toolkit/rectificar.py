"""Endereza una foto en escorzo sobre un plano del mundo.

Con una camara ya ajustada a la foto (`camara_foto`, formato resuelto: f, R, C,
tam), cada punto de un plano del mundo cae en un pixel conocido. Recorriendo
el plano en una rejilla regular y muestreando la foto sale una imagen
ORTOGRAFICA de ese plano, en milimetros: un "perfil" o una "planta" que la
foto no tiene, con su rejilla rotulada.

Solo es fiel para lo que de verdad esta en ese plano. Lo que queda delante o
detras sale desplazado (paralaje): cada rasgo se lee en la lamina del plano en
que se supone que esta. Va sin Blender (numpy + OpenCV).
"""
import json

import cv2
import numpy as np


def camara(ruta):
    c = json.load(open(ruta))
    return c["f"], np.array(c["R"], float), np.array(c["C"], float), c["tam"]


def lamina(foto, cam, eje, valor, u, v, salida, px_mm=4.0, paso=10, rotulo=50, fondo=(40, 40, 46)):
    """`eje`, `valor`: el plano (0, 1 o 2 = X, Y, Z cte). `u`, `v`: (eje, minimo, maximo) de los otros dos; `u` va
    en horizontal y `v` en vertical, creciendo hacia arriba. Rejilla cada `paso` mm, rotulada cada `rotulo`."""
    f, R, C, (W, H) = cam
    im = cv2.imread(foto, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:                                    # recorte sobre transparente: se pone sobre un fondo
        a = im[..., 3:4].astype(float) / 255
        im = (im[..., :3] * a + np.array(fondo) * (1 - a)).astype(np.uint8)
    nu, nv = int((u[2] - u[1]) * px_mm), int((v[2] - v[1]) * px_mm)
    U, V = np.meshgrid(u[1] + np.arange(nu) / px_mm, v[2] - np.arange(nv) / px_mm)
    X = np.zeros((nv, nu, 3))
    X[..., eje], X[..., u[0]], X[..., v[0]] = valor, U, V
    P = (X - C) @ R.T
    mx = (W / 2 + f * P[..., 0] / P[..., 2]).astype(np.float32)
    my = (H / 2 + f * P[..., 1] / P[..., 2]).astype(np.float32)
    out = cv2.remap(im, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=fondo)
    for k in range(int(np.ceil(u[1] / paso) * paso), int(u[2]) + 1, paso):
        c = int((k - u[1]) * px_mm)
        cv2.line(out, (c, 0), (c, nv), (0, 255, 255) if k % rotulo == 0 else (0, 110, 110), 1)
        if k % rotulo == 0:
            cv2.putText(out, str(k), (c + 3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 255), 1)
            cv2.putText(out, str(k), (c + 3, nv - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 255), 1)
    for k in range(int(np.ceil(v[1] / paso) * paso), int(v[2]) + 1, paso):
        r = int((v[2] - k) * px_mm)
        cv2.line(out, (0, r), (nu, r), (0, 255, 255) if k % rotulo == 0 else (0, 110, 110), 1)
        if k % rotulo == 0:
            cv2.putText(out, str(k), (3, r - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 255), 1)
            cv2.putText(out, str(k), (nu - 40, r - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 255), 1)
    cv2.imwrite(salida, out)
    return salida
