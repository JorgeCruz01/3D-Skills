"""Andamiaje de un prop: carpetas, .blend propio y guardado seguro.

La raiz de produccion (la carpeta que contiene una carpeta por prop) no esta
fijada en el codigo: se toma de la variable de entorno BLENDER_PROPS_ROOT o se
fija con `configurar(raiz)` una vez por sesion. La plantilla de estudio es
`<raiz>/_Estudio_Base.blend` salvo que se indique otra (BLENDER_PROPS_TEMPLATE o
el segundo argumento de `configurar`)."""
import os
import shutil
import bpy

RAIZ = os.environ.get("BLENDER_PROPS_ROOT", "")
BASE = os.environ.get("BLENDER_PROPS_TEMPLATE", "")
CARPETAS = (
    "Referencias", "Texturas", os.path.join("Texturas", "Fuente"), os.path.join("Texturas", "Bakes"),
    "Renders", os.path.join("Renders", "Stills"), os.path.join("Renders", "Topologia"),
    os.path.join("Renders", "Portafolio"), "Exportados",
)


def configurar(raiz, base=None):
    """Fija la raiz de produccion y, si se da, la plantilla de estudio."""
    global RAIZ, BASE
    RAIZ = os.path.abspath(raiz)
    if base:
        BASE = os.path.abspath(base)
    return {"raiz": RAIZ, "base": plantilla(), "base_existe": os.path.exists(plantilla())}


def plantilla():
    return BASE or os.path.join(RAIZ, "_Estudio_Base.blend")


def rutas(nombre):
    if not RAIZ:
        raise RuntimeError("prop.RAIZ sin definir: llamar a prop.configurar(raiz) o definir BLENDER_PROPS_ROOT")
    raiz = os.path.join(RAIZ, nombre)
    r = {"raiz": raiz, "blend": os.path.join(raiz, nombre + ".blend")}
    for c in CARPETAS:
        r[c.replace(os.sep, "_").lower()] = os.path.join(raiz, c)
    return r


def crear(nombre):
    """Crea el arbol del prop y su .blend desde la plantilla, y lo abre.
    No pisa un .blend existente: si ya esta, solo lo abre."""
    r = rutas(nombre)
    for c in CARPETAS:
        os.makedirs(os.path.join(r["raiz"], c), exist_ok=True)
    nuevo = not os.path.exists(r["blend"])
    if nuevo:
        if not os.path.exists(plantilla()):
            return {"ok": False, "error": "no existe la plantilla de estudio", "plantilla": plantilla()}
        shutil.copyfile(plantilla(), r["blend"])
    if os.path.normcase(bpy.data.filepath) != os.path.normcase(r["blend"]):
        if bpy.data.is_dirty and bpy.data.filepath:
            return {"ok": False, "error": "la sesion abierta tiene cambios sin guardar",
                    "abierto": bpy.data.filepath}
        bpy.ops.wm.open_mainfile(filepath=r["blend"])
    # una plantilla heredada de otro prop puede traer shift de lente en una camara:
    # con el, dos camaras del mismo prop no encuadran igual (el primer split del casco no casaba)
    for cam in bpy.data.cameras:
        cam.shift_x = cam.shift_y = 0.0
    return {"ok": True, "nuevo": nuevo, **r}


def guardar(nombre):
    """Guarda solo si la sesion abierta ES el .blend de ese prop."""
    esperado = rutas(nombre)["blend"]
    if os.path.normcase(bpy.data.filepath) != os.path.normcase(esperado):
        return {"ok": False, "error": "la sesion no es el .blend de este prop",
                "abierto": bpy.data.filepath, "esperado": esperado}
    bpy.ops.wm.save_mainfile()
    return {"ok": True, "bytes": os.path.getsize(esperado), "objetos": len(bpy.data.objects)}
