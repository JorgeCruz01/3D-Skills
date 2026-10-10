"""MK_Cuerda desde la propia low poly, y las demas clases del set del mastil sin lo que caiga bajo una cuerda.

    python mascara_cuerdas.py        (despues de `sp_mascaras.py`; fuera de Blender: usa OpenCV)

Las cuerdas pasan a 2-4 mm del diapason: horneadas con el resto del high poly, quedaban estampadas en la madera
(clase, normal y oclusion). Se hornea SIN ellas y su mascara sale de `Texturas/Bakes/LP_Cuerda.png`, el atributo de
cara `cosida` de la low poly (lo escribe `formas.COSTURA_BARRIDO` en cada barrido).
"""
import json
import os

import cv2
import numpy as np

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Texturas", "Bakes")
M = os.path.join(B, "Mascaras")
rd = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
c = rd(os.path.join(B, "LP_Cuerda.png"))
c = c[..., 0] if c.ndim == 3 else c
c = cv2.dilate((c > 127).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))      # islas de 2-4 px: margen contra el borde de otra clase
cv2.imencode(".png", c)[1].tofile(os.path.join(M, "MK_Cuerda.png"))
inv = 1.0 - c / 255.0
clases = [k for k in json.load(open(os.path.join(B, "ID_clases.json"))) if not k.startswith("C_")]
for k in clases:
    p = os.path.join(M, "MK_%s.png" % k)
    cv2.imencode(".png", (rd(p) * inv).astype(np.uint8))[1].tofile(p)
print("cuerda %.2f %%" % (c.mean() / 2.55), clases)
