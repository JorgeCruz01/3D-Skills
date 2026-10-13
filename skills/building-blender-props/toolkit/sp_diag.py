"""Diagnostico: abre Painter y el proyecto del prop, y aplica la receta de un set op a op hasta dar con la que falla.

    python sp_diag.py <Prop> <indice de receta> [--abierto]"""
import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get("SP_PROPS_ROOT") or os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import sp  # noqa: E402

EXE = r"C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe"
sys.stdout.reconfigure(encoding="utf-8")
prop, k = sys.argv[1], int(sys.argv[2])
if "--abierto" not in sys.argv:
    subprocess.Popen([EXE])
    for _ in range(40):
        time.sleep(5)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "_herramientas", "sp.py"), "estado"], capture_output=True, text=True, encoding="utf8", errors="replace")
        if "painter" in (r.stdout or ""):
            break
    time.sleep(8)
    res = sp.llamar([{"tool": "sp_project_open", "args": {"path": sp.u(sp.rutas(prop)["spp"])}}], eco=False)
    print("abrir:", str(res[0][0])[:100], res[0][2])
r = sp._receta(prop)[k]
st = sp.llamar([{"tool": "sp_get_layer_stack", "args": {"texture_set": r.ts, "max_depth": 0}}], eco=False)[0][0]
print("capas que hay:", len(st["layers"]))
rec = r.json(borrar=[l["uid"] for l in st["layers"]])
print("claves:", list(rec.keys()) if isinstance(rec, dict) else type(rec), "ops:", len(rec["ops"]) if isinstance(rec, dict) else "?")
base = r.json()["ops"]


def prueba(n):
    st = sp.llamar([{"tool": "sp_get_layer_stack", "args": {"texture_set": r.ts, "max_depth": 0}}], eco=False)[0][0]
    uno = dict(rec)
    uno["ops"] = [{"op": "delete", "uid": l["uid"]} for l in st["layers"]] + base[:n]
    res = sp.llamar([{"tool": "sp_apply_recipe", "args": {"recipe": uno}}], eco=False)
    d, _, err = res[0] if res else (None, None, True)
    return (not err), d


lo, hi = 0, len(base)
ok, d = prueba(hi)
if ok:
    print("la receta entera pasa ahora")
else:
    while hi - lo > 1:
        m = (lo + hi) // 2
        ok, d = prueba(m)
        lo, hi = (m, hi) if ok else (lo, m)
    ok, d = prueba(hi)
    print("FALLA al anadir la op %d:" % (hi - 1), json.dumps(base[hi - 1], ensure_ascii=False)[:900])
    print("   ->", json.dumps(d, ensure_ascii=False)[:500])
    print("anterior:", json.dumps(base[hi - 2], ensure_ascii=False)[:400])
