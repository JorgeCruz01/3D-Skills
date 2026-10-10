"""Contorno UNICO y limpio del cuerpo, a partir de los cuatro trozos de `contornos.json`.

    python limpiar_contorno.py        (fuera de Blender: usa OpenCV)

Los trozos se leyeron por filas y dejaban dos defectos que solo se ven de cerca (2026-10-10): un escalon de 15 mm
entre el hombro y el mastil (el hombro acababa en x = -42.7 y no en el canto del mastil) y una aleta fina en el
extremo del hombro, que era el boton de correa leido como cuerpo. Aqui se rasteriza la union a 0.05 mm/px, se abre y
se cierra con un disco (quita aletas y muescas mas estrechas que su diametro) y se
escribe el contorno resultante en `contornos.json` como `cuerpo_limpio` = [(y, x) en mm].
"""
import json
import os

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
ESC = 20.0                 # px por mm
R_ABRIR, R_CERRAR = 7.0, 12.0   # abrir 7: quita el boton de correa, que el alfa de la foto daba como cuerpo (pestana de 10 mm)
X_MASTIL = 27.5            # semiancho del mastil en el talon, mm


def main():
    ruta = os.path.join(AQUI, "contornos.json")
    D = json.load(open(ruta, encoding="utf8"))
    T = [np.array(t["P"], float) for t in D["cuerpo"]["trozos"]]          # (y, x)
    todo = np.concatenate(T)
    lo = todo.min(0) - 40.0                     # mas que el radio de cierre: pegado al borde, el cierre lo toca
    tam = np.ceil((todo.max(0) + 40.0 - lo) * ESC).astype(int)
    a_px = lambda P: np.round((P - lo) * ESC).astype(np.int32)[:, ::-1]   # columnas = x, filas = y
    im = np.zeros((tam[0], tam[1]), np.uint8)
    for P in T:
        cv2.fillPoly(im, [a_px(P)], 255)
    antes = im.copy()
    disco = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * r * ESC) + 1,) * 2)
    im = cv2.morphologyEx(im, cv2.MORPH_OPEN, disco(R_ABRIR))
    im = cv2.morphologyEx(im, cv2.MORPH_CLOSE, disco(R_CERRAR))
    cs, _ = cv2.findContours(im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)              # (col, fila)
    # suavizado y remuestreo: 1 punto cada 0.5 mm, media movil de 2 mm
    k = int(2.0 * ESC) | 1
    pad = np.concatenate([c[-k:], c, c[:k]])
    nucleo = np.ones(k) / k
    s = np.stack([np.convolve(pad[:, i], nucleo, mode="same") for i in (0, 1)], 1)[k:-k]
    s = s[:: int(0.5 * ESC)]
    P = s[:, ::-1] / ESC + lo                                             # (y, x) en mm
    D["cuerpo_limpio"] = [[round(float(a), 4), round(float(b), 4)] for a, b in P]
    json.dump(D, open(ruta, "w", encoding="utf8"))
    inter, union = ((antes > 0) & (im > 0)).sum(), ((antes > 0) | (im > 0)).sum()
    quitado, puesto = ((antes > 0) & (im == 0)).sum() / ESC ** 2, ((antes == 0) & (im > 0)).sum() / ESC ** 2
    print({"puntos": len(P), "iou_con_los_trozos": round(inter / union, 5), "quitado_mm2": round(quitado, 1), "puesto_mm2": round(puesto, 1),
           "area_mm2": round((im > 0).sum() / ESC ** 2, 1), "caja_mm": [P.min(0).round(2).tolist(), P.max(0).round(2).tolist()],
           })
    v = cv2.cvtColor(antes // 3, cv2.COLOR_GRAY2BGR)
    v[(antes > 0) & (im == 0)] = (0, 0, 255)
    v[(antes == 0) & (im > 0)] = (255, 160, 0)
    cv2.imencode(".png", cv2.resize(v, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA))[1].tofile(os.path.join(AQUI, "Referencias", "contorno_limpio.png"))


if __name__ == "__main__":
    main()
