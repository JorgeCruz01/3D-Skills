"""Parte los mapas de apoyo de `substance.py` en mascaras en gris para Substance 3D Painter.

    python sp_mascaras.py <carpeta del prop> [--halo Clase:radio_px ...] [--suavizar Clase:Vecina:sigma_px ...]

Lee   Texturas/Bakes/ID_clases.png + .json, CAMPO_rayado.png, CAMPO_laminas.png
Escribe Texturas/Bakes/Mascaras/
    MK_<Clase>.png        una por clase de material
    HL_<Clase>.png        halo alrededor de la clase (cerco de verdin de un remache, cuero
                          oscurecido junto a la costura), sin la propia clase
    BD_<Clase>.png        con --suavizar: la frontera en escalera entre Clase y Vecina se redondea (las dos MK_ se
                          reescriben) y BD_ es la cenefa de ese borde (el filete que rodea un panel de picado)
    CP_Rayado_Largo.png, CP_Rayado_Ancho.png, CP_Manchas.png, CP_Junta.png, CP_Lamina.png
    CP_Relieve_Canto.png, CP_Relieve_Hueco.png   si existe NORMAL_blender.png: cantos y huecos del relieve de material
    ZN_<Zona>.png         una por ZONA_<Zona>.png: zonas de uso (mano, mejilla, boca de fuego) de `substance.zonas`
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


def main(carpeta, halos, suaves=()):
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
    for a_, b_, sig in suaves:
        # La frontera entre dos clases que comparten pieza (picado / madera) viene de las CARAS del high poly y sale en
        # escalera. Se redondea desenfocando y umbralizando dentro de la union, y se saca la cenefa del borde.
        union = np.clip(mk[a_] + mk[b_], 0, 1)
        sm = ((cv2.GaussianBlur(mk[a_], (0, 0), sig) > 0.5) & (union > 0.5)).astype(np.float32)
        mk[a_], mk[b_] = sm, union - sm
        for n in (a_, b_):
            escribir(os.path.join(D, "MK_%s.png" % n), cv2.GaussianBlur(mk[n], (3, 3), 0))
            out[n] = round(float(mk[n].mean()) * 100, 2)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(sig * 0.45) + 1,) * 2)
        borde = (cv2.dilate(sm, k) - cv2.erode(sm, k)) * union
        escribir(os.path.join(D, "BD_%s.png" % a_), cv2.GaussianBlur(borde, (0, 0), 1.5))
    out["_vacio"] = round(float(vacio.mean()) * 100, 2)
    out["_dudoso"] = round(float(((np.sqrt(d.min(-1)) > 0.2) & ~vacio).mean()) * 100, 3)
    for n, radio in halos:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radio + 1, 2 * radio + 1))
        h = cv2.GaussianBlur(cv2.dilate(mk[n], k), (0, 0), radio * 0.6)
        escribir(os.path.join(D, "HL_%s.png" % n), np.clip(h * 1.6, 0, 1) * (1 - mk[n]))
    for fich in sorted(f for f in os.listdir(B) if f.startswith("CAMPO_") and f.endswith(".png")):
        base, _, suf = fich[6:-4].partition("_")            # CAMPO_rayado_Veta.png -> rayado, _Veta
        suf = "_" + suf if suf else ""
        canales = {"rayado": ("CP_Rayado_Largo", "CP_Rayado_Ancho", "CP_Manchas"), "laminas": ("CP_Junta", "CP_Lamina")}.get(base)
        if not canales:
            continue
        im = leer(os.path.join(B, fich))[..., 2::-1]
        for c, n in enumerate(canales):
            g = im[..., c]
            escribir(os.path.join(D, n + suf + ".png"), g if n == "CP_Junta" else estirar(g, ~vacio))
    for fich in sorted(f for f in os.listdir(B) if f.startswith("ZONA_") and f.endswith(".png")):      # zonas de uso (`substance.zonas`)
        escribir(os.path.join(D, "ZN_" + fich[5:]), leer(os.path.join(B, fich))[..., 0])
        out.setdefault("_zonas", []).append("ZN_" + fich[5:-4])
    pn = os.path.join(B, "NORMAL_blender.png")
    if os.path.exists(pn):
        # Curvatura sacada de la normal horneada en Blender: es la unica que ve el relieve de MATERIAL del high poly
        # (surcos, moleteado). La curvatura de Painter sale de la geometria y ahi esas piezas son lisas.
        n = leer(pn)[..., 2::-1] * 2 - 1
        nx, ny = cv2.GaussianBlur(n[..., 0], (0, 0), 1.2), cv2.GaussianBlur(n[..., 1], (0, 0), 1.2)
        curv = cv2.Sobel(nx, cv2.CV_32F, 1, 0, ksize=3) - cv2.Sobel(ny, cv2.CV_32F, 0, 1, ksize=3)     # v crece hacia arriba
        dentro = cv2.erode((~vacio).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        frente = n[..., 2] > 0.2                                    # fuera las caras ocultas (normal hacia dentro)
        curv = np.where(dentro & frente, curv, 0)
        k = 1.0 / max(float(np.percentile(np.abs(curv[dentro & frente]), 99.5)), 1e-6)
        escribir(os.path.join(D, "CP_Relieve_Canto.png"), cv2.GaussianBlur(np.clip(curv * k, 0, 1), (0, 0), 1.0))
        escribir(os.path.join(D, "CP_Relieve_Hueco.png"), cv2.GaussianBlur(np.clip(-curv * k, 0, 1), (0, 0), 1.0))
        out["_relieve"] = "CP_Relieve_Canto, CP_Relieve_Hueco"
    prev = cv2.resize((rgb[..., ::-1] * 255).astype(np.uint8), (1024, 1024), interpolation=cv2.INTER_AREA)
    cv2.imencode(".png", prev)[1].tofile(os.path.join(D, "_ID_previa.png"))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    hs, sv = [], []
    a = sys.argv[2:]
    while a:
        op = a.pop(0)
        if op == "--halo":
            n, r = a.pop(0).split(":")
            hs.append((n, int(r)))
        elif op == "--suavizar":                 # --suavizar Clase:Vecina:sigma_px
            n, v, r = a.pop(0).split(":")
            sv.append((n, v, float(r)))
    main(sys.argv[1], hs, sv)
