---
name: building-blender-props
description: Use when asked to produce a game-ready 3D prop in Blender through MCP or bpy scripts — starting a new prop from references, writing its parametric builder, or taking it through high poly, low poly, UV, bake, export and delivery renders; also when rebranding or re-exporting a finished prop.
---

# Building Blender props

## The principle

**A prop is three Python files and a folder of evidence.** The model is never
edited by hand: dimensions live in a builder, the high poly and the low poly
are both generated from it, and every phase closes on numbers that go into the
prop's README. Sixteen props were produced this way in Blender 5.2 through MCP;
every figure below was measured on one of them.

**REQUIRED SUB-SKILL:** blender-props:verifying-blender-props. It owns the
gates, their thresholds and the traps. This skill says what to build and which
tool to call; it does not restate a gate.

Does not apply to: organic sculpts, rigged or animated deliverables, blockouts.
The pipeline ships a static mesh. Fabric, webbing and padding follow the same
phases with a different high poly: blender-props:building-blender-soft-goods.

## What a finished prop is

```
<Prop_Name>/
├─ <Prop_Name>.blend          one scene: high poly, low poly, studio
├─ construir_<prop>.py        dimensions and solids (no scene state)
├─ construir_hp.py            high poly, materials, decals
├─ construir_lp.py            low poly, replicas, own UV seams
├─ README.md                  measured figures, deviations, defects found, sources
├─ Referencias/               Specs.md, Fuentes.md, ref_*.jpg, data sheet
├─ Texturas/                  TX_<Set>_{BaseColor,Normal,ORM}.png at 4096², uv.png, maps.png
│  ├─ Fuente/                 CC0 PBR bases used, by id
│  └─ Bakes/                  AO, RM, bake_log.json
├─ Renders/Stills/            4 stills of the HIGH poly + 05_arcilla_ao.png, 3840×2160
├─ Renders/Topologia/         split.png, split_render.png, wireframe.png
├─ Renders/Portafolio/        render, split, wireframe, uv, maps, clay .webp + asset.json
└─ Exportados/                <Prop_Name>_LP.fbx, .glb
```

Conventions: 1 unit = 1 m, scales applied, +Z up, front faces −Y. Object names
in Spanish without accents. High poly in `Model Collection`, decals in its child
collection `Rotulos`, low poly in `LP Collection` as ONE object
`<Prop_Name>_LP`, **all quads**, with one material `LP_<Set>` per texture set. Normal map
16-bit OpenGL; ORM = AO, Roughness, Metallic.

## Budgets

| Tier | LP triangles | Sets (4096²) | HP faces |
|---|---|---|---|
| Medium (handheld) | 8–20k | 1 | ≥ 100k |
| Medium-high | 15–30k | 1–2 | ≥ 200k |
| High (25+ parts, repetition) | 25–60k | 2–3 | ≥ 400k |

| Largest dimension | Texel-density floor |
|---|---|
| < 400 mm | 5 px/mm |
| 400 mm – 1.2 m | 2.5 px/mm |
| > 1.2 m | 1 px/mm |

Open another set when the floor is not met, and always for glass. Atlas
coverage: target 65 %, floor 40 % (the gate). Measured: 5 of 30 sets reached
65 %, 1 fell under 40 %. Report the number; never trade density for coverage.

## Session setup

Put the toolkit on `sys.path`, reload it, and set the production root —
snippet and scene requirements in `toolkit/README.md`. Reload on every prop
switch: all props share the module names `construir_hp` / `construir_lp`, and a
stale `bake` module cost 823 s on one prop.

Limits of driving one Blender over MCP (120 s background, ~5 min connection,
open-then-operate, one instance): `reference/mcp-session-limits.md`. Read it
before the first long call.

## Phase order

Binding. Touching a phase invalidates everything after it.

| # | Phase | Call | Closes on |
|---|---|---|---|
| 1 | References, `Specs.md` | `prop.crear(nombre)`; photos + sources; `pdf_a_referencia.py` | scale-fixing dimension and independent check both written down; shape-feature list written |
| 2 | Parametric builder | write `construir_<prop>.py` | constants reviewed arithmetically for overlaps |
| 3 | High poly | `construir_hp.materiales_<prop>()`, `construir_hp.construir()` | `puertas.geometria`, `puertas.ensamblaje`, `decals_visible` |
| 4 | Independent check | `F.volumen_cm3`, rays, a rotated copy | the figure from `Specs.md`, **before** any low poly |
| 5 | Render audit | `estudio.vistas_previas(col, carpeta)` | feature list walked against the reference photo |
| 6 | Low poly, all quads | `antes = puertas.huella(HP)`; `construir_lp.construir()` | `Q.censo` (0 tris, 0 n-gons), `Q.desvio`, `tanda.malla`, `puertas.huella_intacta` |
| 7 | UV | `uv.desplegar(names_of_one_set, extra=...)` per set | `tanda.medir_uv`, `puertas.piso_densidad` |
| 8 | Replicas, join | `construir_lp.replicar()`, `construir_lp.juntar()` | triangle count, material slots, 1 UV layer |
| 9 | Bake + export | `tanda.hornear_y_exportar(...)` | `_ultimo.json`: textures on disk, silhouette ×3, fidelity, FBX round-trip |
| 10 | Stills | `entrega.still(...)`, one per call; `entrega.arcilla(...)` | file exists, `encuadre` true; clay still matches the hero |
| 11 | Sheets, package | `tanda.cerrar(...)` | `split` (same camera) true, 5 `.webp`, `.blend` on disk |
| 12 | README, `asset.json` | write | every figure measured; every miss declared |

Signatures and return values of every function: `reference/toolkit-api.md`.

## Phase rules

### 1 · References

- Download 2–3 photos into `Referencias/` **before** writing the builder, and
  record them in `Fuentes.md`. Dimensions are not a reference: a revolver built
  from figures alone was rejected three times. Tracing an outline over a
  millimetre grid into `*_FOTO` point lists: `reference/reference-tracing.md`.
- `Specs.md` has: a table of dimensions with source and type (published /
  standard / **estimated**); "what fixes the scale"; "what verifies it,
  independently"; the numbered shape-feature list; the tolerance, declared
  before modelling (a valve's mass check was set at ±25 % up front and came in
  at +11 %).
- Brand: invent one per prop and web-search it with its product category
  first — `reference/fictitious-brands.md`. "NORTEK" was real; sixteen props
  were relabelled and rebaked.

### 2 · Builder

One module, `construir_<prop>.py`, with **constants in millimetres** at the top
and three kinds of function, all taking `(q, col=COL)`:

| Function | Returns | Rule |
|---|---|---|
| `solidos_<body>(q, col)` | list of objects | volumes of ONE cast body; names start with `_`; they must cross frankly — never tangent, never coplanar caps |
| `cortes_<body>(q, col)` | list of cutters | fine cutters only under `if q > 0.5:`; cutter names are the keys used later for painting and for `CORTES_LP` |
| `piezas_exactas(q, col)` | `{name: object}` | parts kept exact |

Cast or exact?

| Make it with | When | Measured case |
|---|---|---|
| `colada.colar` (cast → cut → fine remesh) | housings, castings, welded or soldered bodies, injected plastic: volumes that meet with a fillet. One skin per rigid body | lantern body: fount, tubes, chimney, hood in one skin |
| exact solids (`F.revolucion`, `F.prisma`, `F.cil`, `F.barrido`, `F.tubo`) | turned parts, glass, wire, fasteners, knurled caps, shafts: crisp edges and clean topology at any `q` | lantern globe, burner, cap, guard, handle |
| `exactos=` of `colar` | machined volumes on a casting that must stay crisp | lathe ways and slides, casting at `suavizado=16` |
| flat prism + `F.fundir` with heavy smoothing | soft-edged slabs with a traced outline | revolver stocks, after offset rings self-crossed |
| `inflado.inflar` (profile inflated by distance to its edge), then cast | moulded stocks, grips, ergonomic housings with holes: every edge rolls, inner ones too, and the width varies in both directions | crossbow stock, after section lofts with prism-cut holes read as a cut-out board |

Outlines drawn with a dozen points go through `F.spline`; visible boxes are
`F.caja_blanda`; bevels on concave or elongated outlines use
`prisma(por_normal=True)`. Review the constants for overlaps before the first
build — most first-build crossings were visible in the numbers.

### 3 · High poly

- Clear the collection yourself (`_vaciar`), then build. Never look objects up
  by name to reuse them.
- Fine voxel ≈ largest dimension / 700–1000 (0.22 mm on a 133 mm contactor,
  0.38 on a 265 mm lantern, 0.9 on an 800 mm robot). A handheld voxel on a
  large prop gave 3.7 M, 4.8 M and 6.8 M faces on three first builds.
- Fillet radius ≈ `voxel × √suavizado`: 2–3 passes for sheet metal and crisp
  plastic, 12–30 for castings and ergonomic housings (drill: 30 passes ≈ 3 mm).
- A part fitted into a cast window needs more than its nominal gap: smoothing
  rounds the window's corners (248 crossings at 0.2 mm on a contactor).
- Materials: `texturas.descargar_pbr` into `Texturas/Fuente/<id>/`, then
  `M.pbr(...)`. Assign per cast body with `colada.pintar` (by cutter) and
  `colada.pintar_por` (by coordinates), in the same session as `colar`.
- Decals: flat text (`F.texto(..., relieve=0.0, ...)`) 0.03–0.04 mm in front of
  its face, in the `Rotulos` child collection, built by one function
  `_rotulos(col)`. One of them reads "MARCA FICTICIA". `solidos()` returns the
  direct children of `Model Collection`, so it excludes the decals; the bake
  adds them back.
- `F.sombrear(o, 40)` on every exact part; `colar` does it for cast ones.

### 6 · Low poly

**The low poly is 100 % quads** — no triangles, no n-gons — and is built without
booleans or decimation. Constructions, measured cases and costs:
`reference/quad-topology.md`. Read it before writing `construir_lp.py`.

| Part | Build it as | Then |
|---|---|---|
| turned, extruded, swept, boxed | the same `formas` call as the high poly, lower `q` | `Q.cuadrar` |
| carved or cast body with an axis | a loft / prism cage with points on the curvature | `Q.ajustar(cage, [hp_part])`, `Q.cuadrar` |
| plate or ring with a through hole | `F.prisma_anillo(exterior, interior, ...)` | — |
| lofted body with a window or pocket | sections and stations on the window's edges | `Q.ventana`, `Q.cuadrar` |
| skin with no generating solids | `T.diezmar(…, 60000)` → `Q.retopo(skin, quads)` | `Q.ajustar` |

- Holes that only house another part are left out and the parts **cross**.
  Slots, channels and rounded window ends go to the normal map. Declare both.
- Close the phase on `Q.censo` (`tris == 0`, `ngonos == 0`, watertight) and
  `Q.desvio(lp, hp, tope=<extrusion in mm>)`; look at `Q.lamina`.
- `Q.cuadrar` needs even boundaries: `F.seg` rounds to even; resample hand
  outlines with `F.remuestrear`. Read `sin_resolver`.
- A low poly far under its tier may be missing silhouette features (clamp
  meter 2,424 → 8,994 tris after moving grip slots and ribs into geometry) —
  check the silhouette gate, not the count. Do not pad to reach a tier: the
  quad shotgun shipped at 8,060 against 15–30k.
- Long parts get rings from `tramos=` on the prism or from the loft's stations,
  not from `L.trocear` (plane cuts split quads).
- Repeated parts: build one, `L.marcar([part], "Rep_<x>")` **before** joining,
  and replicate after unwrapping. A radial engine carries 33,194 of its 52,394
  triangles on one cylinder's texture.
- One **object per texture set** until unwrapped; `juntar()` joins them after.
- `L.union_mecanizada`, `L.limpiar`, `L.trocear` and `L.cortar_en` are the
  first batch's path. They triangulate. Sixteen props still ship that way.

### 7–8 · UV

- `uv.desplegar([objects of one set], extra=<predicate>)`, once per set. The
  default refinement splits self-overlapping islands by dominant normal axis
  before falling back to angle thresholds (40.8 % → 66.0 % on a revolver).
  Read `info["refinado"]`: seams added at threshold 0 mean an island needed a
  seam you can name.
- Own seams via `extra=`: `construir_lp.costura_<x>` for ring equators,
  `L.costura_por_orientacion(ref, 0.5)` for rounded sheet metal,
  `L.costura_en_planos(axis, L.PLANOS[name][axis])` for sliced long parts,
  combined with `L.cualquiera(...)`.
- A remeshed skin has no edges on its seam planes: `L.costura_por_lado(axis,
  coords)` marks the border between the faces on either side instead of
  cutting the mesh.
- Measure (`tanda.medir_uv`, `puertas.piso_densidad`) **before** `replicar()`:
  replicas overlap their original by design.

### 9 · Bake and export

```python
tanda.hornear_y_exportar(NOMBRE, L.NOMBRE, H.solidos(), ("Farol", "Globo"), hero=(0.45, -1.0, 0.3), extrusion=0.002)
```

- It bakes from a temporary **joined copy** of the high poly plus decals onto a
  proxy of the low poly without replicas, at 4096², 8 samples, AO 24 at half
  resolution; builds the `LP_<set>` materials; measures silhouette from three
  views and fidelity from `hero`; exports FBX + GLB and round-trips the FBX.
  Joined, bakes took 29–78 s; unjoined, 287–1,036 s.
- The call outlives the MCP timeout. Read `<prop>/_ultimo.json` and
  `Texturas/Bakes/bake_log.json`; do not re-send it.
- `extrusion` by size: 1.2 mm (133 mm prop), 2 mm handheld, 2.5 mm bench,
  3 mm above ~700 mm.
- The bake hides every other render-visible object (studio backdrop, floor)
  for all passes, and `tanda` hides the original low poly while baking against
  its proxy: the AO pass counts whatever it can see. Check the result with
  `occlusion_map_stats` (verifying-blender-props). Sixteen props shipped an
  occlusion channel at 0.21–0.54 on open faces before this was in the tool;
  `bake.hornear(..., solo_ao=True)` rebakes only that channel and recomposes
  the ORM (6–15 s per prop).
- A `.glb` embeds its maps. After any map changes on disk, re-export
  (`reexportar`), or the GLB ships the old texture.
- **Glass does not survive.** `bake.material_final` rebuilds the node tree
  opaque. For a glass set call it again with `transmision=1.0, ior=1.5` (1.58
  for polycarbonate) and re-run `entrega.exportar_y_verificar`. On any rebake,
  read transmission and IOR off the old material first.
- Fidelity over 2/255: report the total, the smooth-area figure and where it
  concentrates. Do not move the threshold (5 of 16 props shipped over it).

### 10–11 · Stills and sheets

- Four stills of the high poly, one MCP call each:
  `entrega.still(NOMBRE, "01_hero.png", (0.45, -1.0, 0.3))`, a rear, a front or
  side, and `04_detalle_<feature>.png` with `margen=-0.25` … `-0.55`.
- A fifth, mandatory: `entrega.arcilla(NOMBRE, hero)` writes
  `05_arcilla_ao.png`, the high poly in grey clay with ambient occlusion under
  the hero's camera and lights; its `.webp` goes in the package as `clay.webp`.
  Render it small during phase 3 too: a form that does not hold in clay is not
  ready for a low poly. Standard and traps: `reference/clay-ao-still.md`.
- `tanda.cerrar(NOMBRE, L.NOMBRE, sets, hero, esperados, grosor)` renders the
  split with ONE camera pointed like the hero, the wireframe, `uv.png`,
  `maps.png`, converts the five `.webp`, saves and checks the file on disk.
  `grosor` (wire thickness): 0.3–0.5 mm handheld, 0.7–0.8 bench, 1.0–1.2 above
  a metre. Glass parts go wire-only (`solo_alambre` of
  `entrega.laminas_tecnicas`).

### 12 · README and asset.json

README sections, in order: what the prop is · folder tree · **Especificación**
(model vs published, the independent check in bold, brand declared fictitious)
· **Malla** · **UV y texturas** (gate, threshold, measured — per set) ·
**Exportación** · **Dónde se apartó del plan** · **Defectos que encontraron las
mediciones** · **Fuentes de las cotas**.

"Dónde se apartó del plan" lists every one of these that applies, with its
number:

- a threshold or target missed (fidelity, coverage, density, triangle tier),
  the measured value, and that the threshold was not moved;
- dimensions that are estimated rather than published, and which;
- features of the real object left out, and why (collided, not silhouette);
- simplifications a buyer would trip on: solid interior, opaque lenses, static
  mesh with no rig, blind holes;
- no reference photo, if so;
- a model figure that differs from the published one (tank 22.2 L against 24),
  with the label on the prop stating what the model measures.

"Defectos" is numbered: what was wrong, the number that exposed it, what
changed. Include what was caught reviewing the constants before building.

`asset.json` has an `es` and an `en` block with `id`, `name`, `software`,
`tris`, `pieces`, `textureSets`, `textureResolution`, `mapsPerSet`, the five
image URLs plus `clayUrl`, `note` (one measured sentence) and `usedIn`.

## Skeleton

Condensed from `Farol_Queroseno` (a 265 mm kerosene lantern: one cast body,
seven exact parts, two sets).

```python
# construir_farol.py — dimensions and solids only
"""Farol de queroseno de tiro frio. Marca ficticia LUMBREK.
Ejes: Z = arriba, frente en -Y. Unidades: metros; cotas en milimetros.
Envolvente publicada: 265 mm de alto, 150 de ancho, base de 133 de diametro."""
import formas as F
MM, COL = F.MM, "Model Collection"

DEPOSITO = [(0, 0), (66.5, 0), (66.5, 3.5), ..., (25, 62), (0, 62)]      # (r, z), closed outline
# Con el fondo a 20 mm la capacidad medida era de 414 ml frente a los 296-340 publicados
HUECO_BASE = [(0, -5), (61, -5), (61, 9), (59, 28), (0, 28)]
COLUMNA = (27.0, 166.0, 200.0)                                            # r, z0, z1

def _rz(perfil): return [(r * MM, z * MM) for r, z in perfil]

def solidos_cuerpo(q, col=COL):                 # ONE skin: fount, column, chamber, tubes, lugs
    n = F.seg(128, q, 24)
    s = [F.revolucion("_deposito", _rz(DEPOSITO), n, (0, 0, 0), "Z", col),
         F.cil("_columna", COLUMNA[0] * MM, "Z", COLUMNA[1] * MM, COLUMNA[2] * MM, n, col)]
    for lado in (1, -1):
        s.append(F.barrido("_tubo", camino_tubo(lado, q), F.perfil_circ(8.0 * MM, F.seg(40, q, 10)), (0, 1, 0), col))
    return s

def cortes_cuerpo(q, col=COL):
    c = [F.revolucion("_hueco_base", _rz(HUECO_BASE), F.seg(128, q, 24), (0, 0, 0), "Z", col)]
    if q > 0.5:                                  # vents: high poly only, they go to the maps
        c += F.circular(F.cil("_respiradero", 2.2 * MM, "X", 20 * MM, 32 * MM, 20, col, (0, 183 * MM)), 10, "Z")
    return c

def piezas_exactas(q, col=COL):                 # {name: object}; segment counts from F.seg(n, q, min)
    return {"Tapon": ..., "Quemador": ..., "Globo": F.revolucion("Globo", _rz(perfil_globo(q)), F.seg(128, q, 24), (0, 0, 0), "Z", col),
            "Protector": F.unir("Protector", aros), "Asa": ...}
```

```python
# construir_hp.py
import os, bpy, colada, construir_farol as CF, formas as F, materiales as M, prop, texturas
COL, NOMBRE = "Model Collection", "Farol_Queroseno"
VOXEL, FINO = 0.7e-3, 0.38e-3
FUENTES = {"pintura": ("ambientcg", "Metal049A"), "acero": ("ambientcg", "Metal032")}

def materiales_farol():                         # download, then one M.pbr per material; returns {"ok": ...}
    dst = prop.rutas(NOMBRE)["texturas_fuente"]
    T = {k: texturas.descargar_pbr(f, i, os.path.join(dst, i)) for k, (f, i) in FUENTES.items()}
    M.pbr("M_Esmalte", {k: v for k, v in T["pintura"]["mapas"].items() if k != "color"}, tinte=(0.0, 0.085, 0.10),
          tam_m=0.08, rough=(0.26, 0.6), metal=0.0, suciedad=0.55, desgaste=0.6, manchas=0.7, desconchado=0.85)
    M.pbr("M_Vidrio", {}, tinte=(0.93, 0.96, 0.95), rough=(0.03, 0.0), metal=0.0, suciedad=0.0, transmision=1.0, ior=1.5)

def _rotulos(col):                              # decals: own child collection, flat text, ink material
    rot = bpy.data.collections.get("Rotulos") or bpy.data.collections.new("Rotulos")
    if rot.name not in [c.name for c in bpy.data.collections[col].children]:
        bpy.data.collections[col].children.link(rot)
    z = (3.3 + 6.0 + 0.04) * F.MM              # top face of the filler cap + 0.04 mm
    for nombre, txt, alto, y in (("Marca", "LUMBREK", 3.0, 1.2), ("Ficticia", "MARCA FICTICIA", 1.1, -2.6)):
        t = F.texto("Rotulo_" + nombre, txt, alto * F.MM, 0.0, rot.name, (0, y * F.MM, z), "+Z")
        t.data.materials.append(bpy.data.materials["M_Tinta_Negra"])
    return len(rot.objects)

def construir(solver="MANIFOLD"):
    _vaciar(bpy.data.collections[COL])          # delete every object and orphan mesh; never reuse by name
    colada.colar("Cuerpo", CF.solidos_cuerpo(1.0), CF.cortes_cuerpo(1.0), (), VOXEL, FINO, suavizado=3, solver=solver)
    for o in CF.piezas_exactas(1.0).values():
        F.sombrear(o, 40)
    n = _rotulos(COL); asignar()                # asignar(): MATERIALES = {"Cuerpo": "M_Esmalte", "Globo": "M_Vidrio", ...}
    return {"objetos": ..., "rotulos": n, "caras": ...}

def solidos(): return [o.name for o in bpy.data.collections[COL].objects]
```

```python
# construir_lp.py — all quads, no booleans
import bpy, construir_escopeta as CE, formas as F, quads as Q
COL, NOMBRE = "LP Collection", "Escopeta_Corredera_LP"

def culata():                                   # cage: loft of rounded-rectangle sections, last ones tilted onto the joint plane
    return F.loft("Culata_LP", secciones, COL)

def cajon():                                    # loft whose stations fall on the window; pockets sunk, not cut
    o = F.loft("Cajon_LP", secciones, COL)
    Q.ventana(o, lambda c, n: ..., lambda co: (-9e-3, co.y, co.z))
    return o

def construir(q=0.4):
    _vaciar()
    partes = {"Culata": culata(), "Cajon": cajon(), "Guardamonte": F.prisma_anillo(...)}
    Q.ajustar(partes["Culata"], [bpy.data.objects["Culata"]])            # snap the cage to the high poly
    partes.update(CE.piezas_exactas(q, COL))                             # same builders, lower q
    pend = {n: c for n, o in partes.items() if (c := Q.cuadrar(o))["tris"] or c["ngonos"]}
    ...                                         # material LP_Escopeta on every part
    lp = F.unir(NOMBRE, list(partes.values())); F.sombrear(lp, 50)
    return {"censo": Q.censo(lp), "pendientes": pend, "desvio": Q.desvio(lp, hp_objects)}
```

Two texture sets: keep one object per set until both are unwrapped, then a
`juntar()` that calls `F.unir`. Own seams are edge predicates passed to
`uv.desplegar(extra=...)`.

## Checklist — build a new prop

1. Bootstrap the session; `prop.crear(NOMBRE)` (own MCP call).
2. Photos, data sheet, `Fuentes.md`, `Specs.md` with both dimensions, tolerance and feature list.
3. Invent the brand; web-search it and the model designation.
4. Write `construir_<prop>.py`; review the constants for overlaps and tangencies.
5. Write `construir_hp.py`; materials; `construir()`; geometry, assembly and decal gates.
6. Independent check. Fix the builder, rebuild, re-gate.
7. `estudio.vistas_previas`; compare with the photo; walk the feature list. Save.
8. `puertas.huella` → write and run `construir_lp.py` (all quads) → `huella_intacta`, `Q.censo`, `Q.desvio`, `tanda.malla`; look at `Q.lamina`.
9. `uv.desplegar` per set → `tanda.medir_uv`, density floor → `replicar()` → `juntar()`.
10. `tanda.hornear_y_exportar`; read `_ultimo.json`; glass materials; save.
11. Stills, one per call; look at each.
12. `tanda.cerrar`; README; `asset.json`; show the hero and the split to the user.

## Reference

| File | Read when |
|---|---|
| `toolkit/README.md` | first call of a session; setting up a studio template |
| `reference/toolkit-api.md` | before calling any toolkit function |
| `reference/quad-topology.md` | before writing `construir_lp.py`; when a face will not become a quad |
| `reference/reference-tracing.md` | the prop is a recognisable object |
| `reference/reference-likeness.md` | **before the low poly**, on every recognisable object: silhouette against the reference and side-by-side comparison |
| `reference/fictitious-brands.md` | naming a prop; changing a brand on a finished one |
| `reference/mcp-session-limits.md` | before a bake, a render batch, or switching `.blend` |
| `reference/build-lessons.md` | a phase gate fails, or before writing the builder of a prop larger or more repetitive than the last |
| blender-props:building-blender-soft-goods | any part of the prop is fabric, webbing, leather or padding |
| blender-props:texturing-props-in-substance-painter | final textures: after the low poly is unwrapped (phase 8), instead of phase 9's material bake; also to retexture a delivered prop |
