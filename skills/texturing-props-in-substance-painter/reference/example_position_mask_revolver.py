"""Mascara de la linea de arrastre del tambor (`ZN_Linea_Tambor`), del mapa de posicion.

    python mascaras_extra.py

El reten deja una linea fina y brillante alrededor del tambor, a la altura de las muescas: una banda de 0.5 mm en
y = 34 mm, solo en la piel del tambor (a mas de 20 mm de su eje). Sale de `Texturas/Bakes/POSICION.png`
(`substance.posicion`), asi que es exacta y no depende de las UV.
"""
import json
import os

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(AQUI, "Texturas", "Bakes")
Y_LINEA, ANCHO, EJE_Z, R_MIN = 34.0, 0.5, -14.9, 20.4      # mm


def leer(ruta):
    im = cv2.imdecode(np.fromfile(ruta, np.uint8), cv2.IMREAD_UNCHANGED)
    return im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)


caja = json.load(open(os.path.join(B, "POSICION.json")))
lo, hi = np.array(caja["min"], np.float32), np.array(caja["max"], np.float32)
pos = (leer(os.path.join(B, "POSICION.png"))[..., 2::-1] * (hi - lo) + lo) * 1000.0
radio = np.hypot(pos[..., 0], pos[..., 2] - EJE_Z)
tambor = leer(os.path.join(B, "Mascaras", "MK_Tambor.png"))
linea = np.clip(1 - np.abs(pos[..., 1] - Y_LINEA) / (ANCHO / 2), 0, 1) * (radio > R_MIN) * tambor
cv2.imencode(".png", np.clip(linea * 255 + 0.5, 0, 255).astype(np.uint8))[1].tofile(os.path.join(B, "Mascaras", "ZN_Linea_Tambor.png"))
print({"ZN_Linea_Tambor_pct": round(float(linea.mean()) * 100, 4)})
