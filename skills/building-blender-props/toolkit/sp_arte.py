"""Deja en Texturas/Bakes/Mascaras el arte horneado por `prep.arte` / `prep.trenza` y limpia las clases ajenas.

    python sp_arte.py <Prop> [--propias K=Acero,Cobre S=Laca,Cuerno ...] [--partir AR_K_Hoja=AR_K_Hamon,AR_K_Shinogi,AR_K_Kissaki ...]

Va DESPUES de `sp_mascaras_sets.py`, que vacia esa carpeta.
- Todo Texturas/Bakes/AR_*.png pasa a Mascaras en gris (canal rojo). `--partir` reparte uno de tres canales (R, G, B)
  en tres mascaras con los nombres dados.
- `--propias`: clases que SI son de cada set. Donde una pieza apoya en otra de otro set, el horneado de clases ve el
  material de la de encima; esos texeles pasan a la clase propia mas cercana y las MK_ ajenas quedan a cero.
Nacio en la katana (prop 11)."""
import os
import sys

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get("SP_PROPS_ROOT") or os.path.dirname(AQUI)


def leer(p):
    im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
    return im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)


def escribir(p, g):
    cv2.imencode(".png", np.clip(g * 255.0 + 0.5, 0, 255).astype(np.uint8))[1].tofile(p)
    return round(float((g > 0.02).mean()) * 100, 2)


def limpiar(D, letra, propias):
    fich = sorted(f for f in os.listdir(D) if f.startswith("MK_%s_" % letra))
    nom = [f[len("MK_%s_" % letra):-4] for f in fich]
    M = np.stack([leer(os.path.join(D, f)) for f in fich])
    es = np.array([n in propias for n in nom])
    if not es.any() or es.all():
        return 0.0
    ajena = M[~es].sum(0) > 0.3
    lab = M[es].argmax(0)
    solido = (M[es].sum(0) > 0.5) & ~ajena
    _, idx = cv2.distanceTransformWithLabels((~solido).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(solido)
    tabla = np.zeros(idx.max() + 1, np.int32)
    tabla[idx[ys, xs]] = lab[ys, xs]
    cerca = tabla[idx]
    k = 0
    for i, f in enumerate(fich):
        if es[i]:
            g = np.where(ajena, (cerca == k).astype(np.float32), M[i])
            k += 1
        else:
            g = np.zeros_like(M[i])
        escribir(os.path.join(D, f), g)
    return round(100.0 * float(ajena.mean()), 3)


if __name__ == "__main__":
    a = sys.argv[1:]
    B = os.path.join(RAIZ, a[0], "Texturas", "Bakes")
    D = os.path.join(B, "Mascaras")
    os.makedirs(D, exist_ok=True)
    propias, partir, modo = {}, {}, None
    for x in a[1:]:
        if x in ("--propias", "--partir"):
            modo = x
        elif modo == "--propias":
            k, v = x.split("=")
            propias[k] = v.split(",")
        elif modo == "--partir":
            k, v = x.split("=")
            partir[k] = v.split(",")
    out = {}
    for f in sorted(os.listdir(B)):
        if not (f.startswith("AR_") and f.endswith(".png")):
            continue
        g = leer(os.path.join(B, f))
        n = f[:-4]
        if n in partir:
            for nombre, canal in zip(partir[n], (2, 1, 0)):          # OpenCV lee BGR
                out[nombre] = escribir(os.path.join(D, nombre + ".png"), g[..., canal])
        else:
            out[n] = escribir(os.path.join(D, f), g[..., 2] if g.ndim == 3 else g)
    out["ajenas_pct"] = {l: limpiar(D, l, p) for l, p in propias.items()}
    print(out)
