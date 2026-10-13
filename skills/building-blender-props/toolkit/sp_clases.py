"""Lo que los mapas exportados dicen de cada clase de material, medido con las mascaras MK_.

    python sp_clases.py <Prop> <Set>:<letra> [<Set>:<letra> ...]

Por clase: color medio, contraste de luminancia (p95 / p5), rango de rugosidad (p5-p95) y metallic medio. Y tres
avisos, que son los que el ojo no separa en el visor de Painter y si se pagan en el render:

- METAL TURBIO: una clase metalica (metallic medio > 0,3) por debajo de 0,9. Mugre con `metallic: 0` a media opacidad.
- PLANO: contraste de luminancia < 1,35 y rango de rugosidad < 0,15 en una clase de mas del 5 % del atlas.
- GEMELAS: dos clases de mas del 10 % con la luminancia media a menos de un 25 % y la rugosidad mediana a menos de
  0,08: se leen como un solo material aunque sean plastico y piel.

Caso que lo origino (auriculares, 2026-10-13): carcasa #393837 y piel #252524 con rugosidad 0,44-0,64 y 0,47-0,58;
el cliente: «las texturas pueden mejorar aun mas». Ninguna puerta lo media.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get("SP_PROPS_ROOT") or os.path.dirname(AQUI)
N = 1024


def _lee(f, modo):
    return np.asarray(Image.open(f).convert(modo).resize((N, N), Image.BILINEAR), np.float32) / 255.0


def medir(prop, set_, letra):
    P = os.path.join(RAIZ, prop, "Texturas")
    bc = _lee(os.path.join(P, "TX_%s_BaseColor.png" % set_), "RGB")
    orm = _lee(os.path.join(P, "TX_%s_ORM.png" % set_), "RGB")
    lum = bc @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    out = {}
    for f in sorted(glob.glob(os.path.join(P, "Bakes", "Mascaras", "MK_%s_*.png" % letra))):
        m = _lee(f, "L") > 0.5
        m[1:-1, 1:-1] &= m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]      # sin el borde: ahi se mezcla la clase vecina
        if m.sum() < 200:
            continue
        L, R = lum[m], orm[..., 1][m]
        q = lambda a, p: float(np.percentile(a, p))
        out[os.path.basename(f)[5:-4]] = dict(
            pct=round(100.0 * float(m.mean()), 1), color="#%02X%02X%02X" % tuple((bc[m].mean(0) * 255).astype(int)),
            lum=round(float(L.mean()), 3), contraste=round(q(L, 95) / max(q(L, 5), 1e-3), 2), rug=(round(q(R, 5), 2), round(q(R, 95), 2)),
            rug_med=round(q(R, 50), 2), metal=round(float(orm[..., 2][m].mean()), 2))
    return out


def avisos(clases):
    av = []
    for n, c in clases.items():
        if 0.3 < c["metal"] < 0.9:
            av.append("METAL TURBIO %s: metallic %.2f" % (n, c["metal"]))
        if c["pct"] > 5 and c["contraste"] < 1.35 and c["rug"][1] - c["rug"][0] < 0.15:
            av.append("PLANO %s: contraste x%.2f, rugosidad %.2f-%.2f" % (n, c["contraste"], c["rug"][0], c["rug"][1]))
    g = [(n, c) for n, c in clases.items() if c["pct"] > 10 and c["metal"] < 0.3]
    for i, (a, ca) in enumerate(g):
        for b, cb in g[i + 1:]:
            if a + "_V" == b or b + "_V" == a:      # la misma madera con la veta girada
                continue
            if abs(ca["lum"] - cb["lum"]) / max(ca["lum"], cb["lum"], 1e-3) < 0.25 and abs(ca["rug_med"] - cb["rug_med"]) < 0.08:
                av.append("GEMELAS %s y %s: luminancia %.3f / %.3f, rugosidad %.2f / %.2f" % (a, b, ca["lum"], cb["lum"], ca["rug_med"], cb["rug_med"]))
    return av


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for par in sys.argv[2:]:
        s, letra = par.split(":")
        C = medir(sys.argv[1], s, letra)
        print("== %s / %s" % (sys.argv[1], s))
        for n, c in C.items():
            print("  %-12s %5.1f%%  %s  contraste x%.2f  rugosidad %.2f-%.2f  metal %.2f" % (n, c["pct"], c["color"], c["contraste"], c["rug"][0], c["rug"][1], c["metal"]))
        for a in avisos(C):
            print("  AVISO " + a)
