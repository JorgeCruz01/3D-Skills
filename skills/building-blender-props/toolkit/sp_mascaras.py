"""Parte los mapas de apoyo de `substance.py` en mascaras en gris para Substance 3D Painter.

    python sp_mascaras.py <carpeta del prop> [--halo Clase:radio_px ...]

Lee   Texturas/Bakes/ID_clases.png + .json, CAMPO_rayado.png, CAMPO_laminas.png
Escribe Texturas/Bakes/Mascaras/
    MK_<Clase>.png        una por clase de material
    HL_<Clase>.png        halo alrededor de la clase (cerco de verdin de un remache, cuero
                          oscurecido junto a la costura), sin la propia clase
    CP_Rayado_Largo.png, CP_Rayado_Ancho.png, CP_Manchas.png, CP_Junta.png, CP_Lamina.png
    _ID_previa.png        para mirar

Va fuera de Blender porque usa OpenCV. Imprime el porcentaje del mapa de cada clase: una clase
a 0 % es un material que la low poly no ve.
"""
import json
import os
import sys

import cv2
import numpy as np


def leer(ruta):
    im = cv2.imdecode(np.fromfile(ruta, np.uint8), cv2.IMREAD_UNCHANGED)
    return im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)


def escribir(ruta, gris):
    cv2.imencode(".png", np.clip(gris * 255.0 + 0.5, 0, 255).astype(np.uint8))[1].tofile(ruta)


def estirar(g, validos):
    lo, hi = np.percentile(g[validos], (1, 99))
    return np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1)


def main(carpeta, halos):
    B = os.path.join(carpeta, "Texturas", "Bakes")
    D = os.path.join(B, "Mascaras")
    os.makedirs(D, exist_ok=True)
    pal = json.load(open(os.path.join(B, "ID_clases.json"), encoding="utf8"))
    rgb = leer(os.path.join(B, "ID_clases.png"))[..., 2::-1]
    nombres = list(pal)
    d = ((rgb[:, :, None, :] - np.array([pal[n] for n in nombres], np.float32)[None, None]) ** 2).sum(-1)
    lab = d.argmin(-1)
    vacio = rgb.max(-1) < 0.2
    out, mk = {}, {}
    for i, n in enumerate(nombres):
        m = ((lab == i) & ~vacio).astype(np.float32)
        mk[n] = m
        escribir(os.path.join(D, "MK_%s.png" % n), cv2.GaussianBlur(m, (3, 3), 0))
        out[n] = round(float(m.mean()) * 100, 2)
    out["_vacio"] = round(float(vacio.mean()) * 100, 2)
    out["_dudoso"] = round(float(((np.sqrt(d.min(-1)) > 0.2) & ~vacio).mean()) * 100, 3)
    for n, radio in halos:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radio + 1, 2 * radio + 1))
        h = cv2.GaussianBlur(cv2.dilate(mk[n], k), (0, 0), radio * 0.6)
        escribir(os.path.join(D, "HL_%s.png" % n), np.clip(h * 1.6, 0, 1) * (1 - mk[n]))
    for fich, canales in (("CAMPO_rayado.png", ("CP_Rayado_Largo", "CP_Rayado_Ancho", "CP_Manchas")),
                          ("CAMPO_laminas.png", ("CP_Junta", "CP_Lamina"))):
        p = os.path.join(B, fich)
        if not os.path.exists(p):
            continue
        im = leer(p)[..., 2::-1]
        for c, n in enumerate(canales):
            g = im[..., c]
            escribir(os.path.join(D, n + ".png"), g if n == "CP_Junta" else estirar(g, ~vacio))
    prev = cv2.resize((rgb[..., ::-1] * 255).astype(np.uint8), (1024, 1024), interpolation=cv2.INTER_AREA)
    cv2.imencode(".png", prev)[1].tofile(os.path.join(D, "_ID_previa.png"))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    hs = []
    a = sys.argv[2:]
    while a:
        if a.pop(0) == "--halo":
            n, r = a.pop(0).split(":")
            hs.append((n, int(r)))
    main(sys.argv[1], hs)
