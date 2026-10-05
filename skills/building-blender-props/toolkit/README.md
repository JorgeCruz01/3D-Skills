# toolkit

The shared modules that built sixteen props in Blender 5.2 through MCP. Code and
identifiers are Spanish; units are metres; +Z up, the prop's front faces −Y.
Function-by-function reference: `../reference/toolkit-api.md`.

## Loading it inside Blender

Three directories go on `sys.path`: the gate functions of the sibling skill,
this folder, and the folder of the prop being built (its `construir_*.py`).
Run this at the start of a session **and every time you switch prop**:

```python
import sys, importlib
SKILLS = r"<...>/3D-Skills/skills"            # repo checkout or installed plugin
RAIZ   = r"<production root>"                 # one folder per prop lives here
NOMBRE = "Farol_Queroseno"

# every prop has modules called construir_hp / construir_lp: drop the previous prop's
sys.path[:] = [p for p in sys.path if not (p.startswith(RAIZ) and p != RAIZ)]
for m in [m for m in sys.modules if m.startswith("construir_")]:
    del sys.modules[m]
for p in (RAIZ + "/" + NOMBRE, SKILLS + "/building-blender-props/toolkit", SKILLS + "/verifying-blender-props"):
    if p not in sys.path:
        sys.path.insert(0, p)
importlib.invalidate_caches()

import verifications, formas, lowpoly, colada, uv, bake, materiales, texturas, prop
import estudio, exportar, laminas, puertas, entrega, tanda
for m in (verifications, formas, lowpoly, colada, uv, bake, materiales, texturas, prop,
          estudio, exportar, laminas, puertas, entrega, tanda):      # dependencies first
    importlib.reload(m)
prop.configurar(RAIZ)        # after the reload: reloading `prop` resets RAIZ
```

Why the reload is not optional: Blender keeps modules across calls and across
`.blend` files. A welder was baked with a `bake` module loaded before the
joined-copy default existed: 823 s instead of about 50.

Reloading clears module state. `colada._HUELLAS` (cutter footprints used by
`colada.pintar`) and `lowpoly.PLANOS` (slice planes recorded by `trocear`) only
exist in the session that ran `colar` / `trocear`; reload, then build, then
paint.

## Dependency order

```
formas                      bpy, bmesh, numpy
├─ colada                   formas
├─ lowpoly                  formas
├─ tela                     formas (cloth skins, straps, zippers: see building-blender-soft-goods)
└─ quads                    formas (all-quad low poly: see reference/quad-topology.md)
uv · bake · materiales · exportar · laminas · estudio · prop      standalone
texturas                    prop (optional, for the cache location)
puertas                     verifications
entrega                     estudio, exportar, laminas, prop, puertas, verifications
tanda                       bake, entrega, estudio, lowpoly, prop, puertas, verifications
reexportar                  entrega, prop
pdf_a_referencia            system Python + PyMuPDF, not Blender
```

`verifications` is `skills/verifying-blender-props/verifications.py`.

## What the toolkit assumes about the scene

`prop.crear` copies a studio template (`<root>/_Estudio_Base.blend`, or the path
given to `prop.configurar(raiz, base)` / `BLENDER_PROPS_TEMPLATE`). The template
is **not shipped here** (the one used in production embeds paths to another
project). It must contain:

| Datablock | Names | Used by |
|---|---|---|
| Collections | `Model Collection` (high poly), `LP Collection` | everything |
| Area lights | `Area.001` … `Area.004`, placed for a prop `estudio.REF_ALTO` = 0.51 m tall | `estudio.escalar_luces` |
| Cameras | `CAM_Beauty`, `CAM_Detalle`, `CAM_Topo` | `estudio`, `entrega`, `tanda` |
| Backdrop | `Backdrop_360` (closed cyclorama, n-gon floor) | `laminas`, `estudio.vistas_previas`, silhouette gates |
| Render | Cycles, a world that resolves on disk | all renders |

The builders add a `Rotulos` collection (decals) as a child of
`Model Collection`; `tanda.hornear_y_exportar` reads it by that name.

Different names or rig size: reassign `estudio.LUCES`, `estudio.CAMARAS`,
`estudio.REF_ALTO`, `estudio.GANANCIA` after import.

## Configuration

| What | How |
|---|---|
| Production root | `prop.configurar(raiz)` or env `BLENDER_PROPS_ROOT` |
| Studio template | second argument of `prop.configurar`, or env `BLENDER_PROPS_TEMPLATE` |
| PBR download cache | `texturas.CACHE = path`, or env `BLENDER_PROPS_CACHE`; default `<root>/_cache_texturas` |
| `.webp` conversion | `ffmpeg` on `PATH` (`laminas.a_webp`) |

There is no PIL in Blender's Python: images are read and composed with
`bpy.data.images` + numpy (`laminas._leer`, `laminas._escribir`).
