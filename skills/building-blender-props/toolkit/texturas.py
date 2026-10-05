"""Descarga y cache de materiales PBR CC0 de ambientCG y Poly Haven.

Corre dentro del Python de Blender (solo stdlib + bpy). Cada descarga se guarda
en `<cache>/<fuente>/<id>_<res>/` y se copia a la carpeta del prop, para que el
prop sea autocontenido y la red solo se use una vez por material.

La cache es, por orden: `texturas.CACHE` si se ha asignado, la variable de
entorno BLENDER_PROPS_CACHE, `<raiz de produccion>/_cache_texturas` si `prop`
tiene raiz, y en ultimo caso `_cache/` junto a este fichero.
"""
import json
import os
import shutil
import urllib.request
import zipfile

import bpy

CACHE = None
UA = {"User-Agent": "Mozilla/5.0 (blender-props; Blender)"}
OBLIGATORIOS = ("color", "normal", "roughness")


def _cache():
    if CACHE:
        return CACHE
    if os.environ.get("BLENDER_PROPS_CACHE"):
        return os.environ["BLENDER_PROPS_CACHE"]
    try:
        import prop
        if prop.RAIZ:
            return os.path.join(prop.RAIZ, "_cache_texturas")
    except ImportError:
        pass
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache")


def _bajar(url, destino):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)
    return os.path.getsize(destino)


def _clasificar(nombre):
    n = nombre.lower()
    base = os.path.splitext(n)[0]
    if "normaldx" in n or "nor_dx" in n:
        return None
    if "normalgl" in n or "nor_gl" in n:
        return "normal"
    if base.endswith("_color") or "_diff_" in n or base.endswith("_diffuse"):
        return "color"
    if "roughness" in n or "_rough_" in n:
        return "roughness"
    if "metalness" in n or "_metal_" in n:
        return "metallic"
    if "ambientocclusion" in n or "_ao_" in n:
        return "ao"
    if "displacement" in n or "_disp_" in n:
        return "displacement"
    if "opacity" in n:
        return "opacity"
    return None


def _ambientcg(id_, res, carpeta):
    zip_p = os.path.join(carpeta, "_src.zip")
    _bajar("https://ambientcg.com/get?file=%s_%s-JPG.zip" % (id_, res.upper()), zip_p)
    with zipfile.ZipFile(zip_p) as z:
        z.extractall(carpeta)
    os.remove(zip_p)


def _polyhaven(id_, res, carpeta):
    req = urllib.request.Request("https://api.polyhaven.com/files/" + id_, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        info = json.load(r)
    r_ = res.lower()
    for clave in ("Diffuse", "nor_gl", "Rough", "Metal", "AO", "Displacement"):
        if clave in info and r_ in info[clave] and "jpg" in info[clave][r_]:
            url = info[clave][r_]["jpg"]["url"]
            _bajar(url, os.path.join(carpeta, os.path.basename(url)))


def _medir(ruta):
    img = bpy.data.images.load(ruta, check_existing=False)
    tam = (img.size[0], img.size[1])
    bpy.data.images.remove(img)
    return tam


def descargar_pbr(fuente, id_, destino, res="2K"):
    """Devuelve {ok, mapas: {color, normal, roughness, ...}, tam, desde_cache}.
    `ok` es False si falta un mapa obligatorio o alguno mide 0x0."""
    carpeta = os.path.join(_cache(), fuente, "%s_%s" % (id_, res))
    desde_cache = os.path.isdir(carpeta) and bool(os.listdir(carpeta))
    if not desde_cache:
        os.makedirs(carpeta, exist_ok=True)
        try:
            {"ambientcg": _ambientcg, "polyhaven": _polyhaven}[fuente](id_, res, carpeta)
        except Exception as e:  # red caida, 404, zip corrupto
            shutil.rmtree(carpeta, ignore_errors=True)
            return {"ok": False, "error": "%s: %s" % (type(e).__name__, e), "id": id_}
    os.makedirs(destino, exist_ok=True)
    mapas, tam = {}, {}
    for f in sorted(os.listdir(carpeta)):
        k = _clasificar(f)
        if not k or k in mapas:
            continue
        dst = os.path.join(destino, f)
        if not os.path.exists(dst):
            shutil.copyfile(os.path.join(carpeta, f), dst)
        mapas[k] = dst
        tam[k] = _medir(dst)
    faltan = [k for k in OBLIGATORIOS if k not in mapas]
    ceros = [k for k, t in tam.items() if t[0] == 0 or t[1] == 0]
    return {"ok": not faltan and not ceros, "id": id_, "fuente": fuente, "mapas": mapas,
            "tam": tam, "faltan": faltan, "cero": ceros, "desde_cache": desde_cache}
