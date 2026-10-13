"""Con las mascaras ya en disco: (abre Painter y el proyecto si hace falta) importa TODAS las mascaras y los recursos,
rehace la receta, exporta cada set y cierra Painter. Comprueba que el BaseColor no sale vacio.

    python sp_ciclo.py <cfg.json> [--abierto] [--nuevo]"""
import glob
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
C = json.load(open(sys.argv[1], encoding="utf8"))
prop = C["prop"]
P = os.path.join(RAIZ, prop)


def py(*a):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "_herramientas", "sp.py"), *a], capture_output=True, text=True, encoding="utf8", errors="replace")
    return (r.stdout or "") + (r.stderr or "")


def gpu_ocupada(tope=40):
    """Un solo trabajo de GPU a la vez (Jorge, 2026-10-13): Painter a la vez que un render de Cycles satura la tarjeta
    y deja la maquina sin respuesta. Mira el uso de la mas cargada; `--forzar` se lo salta."""
    try:
        o = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
        return max(int(x) for x in o.split()) > tope
    except Exception:
        return False


if "--forzar" not in sys.argv and gpu_ocupada():
    sys.exit("GPU OCUPADA (hay un render u otro ciclo en marcha): no se abre Painter. Esperar a que termine.")
mk = sorted(glob.glob(os.path.join(P, "Texturas", "Bakes", "Mascaras", "*.png")))
if len(mk) < 4:
    sys.exit("NO HAY MASCARAS en %s: no se sigue" % os.path.join(P, "Texturas", "Bakes", "Mascaras"))
if "--abierto" not in sys.argv:
    subprocess.Popen([EXE])
    for _ in range(40):
        time.sleep(5)
        if "painter" in py("estado"):
            break
    time.sleep(8)
    if "--nuevo" in sys.argv:
        o = py("proyecto", prop, "LP_" + C["sets"][0], "--extrusion", str(C["extrusion"]), "--fondo", str(C["fondo"]), "--normales-malla")
        print("\n".join(l[:200] for l in o.splitlines() if "ERROR" in l or l.startswith("set:") or "AVISO" in l or "paro" in l))
    else:
        res = sp.llamar([{"tool": "sp_project_open", "args": {"path": sp.u(sp.rutas(prop)["spp"])}}], eco=False)
        print("abrir:", str(res[0][0])[:100], res[0][2])
rel = [os.path.relpath(m, P) for m in mk] + list(C.get("importar", []))
falta = [x for x in rel if not os.path.exists(os.path.join(P, x))]
if falta:
    subprocess.run(["taskkill", "/F", "/IM", "Adobe Substance 3D Painter.exe"], capture_output=True)
    sys.exit("FALTAN recursos por importar: %s" % falta)
o = py("importar", prop, *rel)
print("importados:", len(rel), "| errores:", o.lower().count("error"))
out = py("rehacer", prop, os.path.join(P, "vistas_sp.json"))
print("\n".join(l[:300] for l in out.splitlines() if "receta" in l or "ERROR" in l or "paro" in l))
if "NO valida" in out or "INVALID_RECIPE" in out:
    # sin esto el ciclo exportaba la pila ANTERIOR y terminaba en "ok": los mapas no cambiaban y nada lo decia
    subprocess.run(["taskkill", "/F", "/IM", "Adobe Substance 3D Painter.exe"], capture_output=True)
    sys.exit("RECETA NO VALIDA: no se exporta (los mapas en disco siguen siendo los anteriores)")
mal = []
for s in C["sets"]:
    o = py("exportar", prop, "LP_" + s)
    print("\n".join(l[:160] for l in o.splitlines() if "ERROR" in l or "fallida" in l))
    f = os.path.join(P, "Texturas", "TX_%s_BaseColor.png" % s)
    kb = os.path.getsize(f) // 1024 if os.path.exists(f) else 0
    print("TX_%s_BaseColor: %d KB" % (s, kb))
    if kb < 400:
        mal.append(s)
subprocess.run(["taskkill", "/F", "/IM", "Adobe Substance 3D Painter.exe"], capture_output=True)
print("cerrado", "| VACIOS: %s" % mal if mal else "| ok")
