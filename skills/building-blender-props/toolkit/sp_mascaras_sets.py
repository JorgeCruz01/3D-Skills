"""Mascaras de un prop de varios sets, con el prefijo del set:

    python sp_mascaras_sets.py <Prop> <sufijo> [<sufijo> ...]

Tras `substance.por_set` (ID_clases_<sufijo>.png/.json en Texturas/Bakes): corre `sp_mascaras.py` una vez por set y
renombra sus MK_<clase>.png a MK_<sufijo>_<clase>.png, para que dos sets puedan tener clases del mismo nombre."""
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get("SP_PROPS_ROOT") or os.path.dirname(AQUI)

if __name__ == "__main__":
    prop, sufs = sys.argv[1], sys.argv[2:]
    B = os.path.join(RAIZ, prop, "Texturas", "Bakes")
    D = os.path.join(B, "Mascaras")
    shutil.rmtree(D, ignore_errors=True)
    for s in sufs:
        for e in (".png", ".json"):
            shutil.copyfile(os.path.join(B, "ID_clases_%s%s" % (s, e)), os.path.join(B, "ID_clases" + e))
        r = subprocess.run([sys.executable, os.path.join(AQUI, "sp_mascaras.py"), prop], capture_output=True, text=True, encoding="utf8")
        print(s, " ".join(r.stdout.split())[:500])
        for f in os.listdir(D):
            if f.startswith("MK_") and not any(f.startswith("MK_%s_" % x) for x in sufs):
                os.replace(os.path.join(D, f), os.path.join(D, "MK_%s_%s" % (s, f[3:])))
    for e in (".png", ".json"):
        os.remove(os.path.join(B, "ID_clases" + e))
    print(len([f for f in os.listdir(D) if f.startswith("MK_")]), "mascaras de clase")
