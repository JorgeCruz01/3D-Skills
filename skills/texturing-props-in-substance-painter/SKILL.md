---
name: texturing-props-in-substance-painter
description: Use when a Blender prop built with building-blender-props needs its final textures - after the low poly is unwrapped and before stills - or when an already delivered prop is being retextured. Drives Adobe Substance 3D Painter through the sp-mcp server from a terminal, with Blender supplying the masks Painter cannot derive from a one-object low poly.
---

# Texturing props in Substance 3D Painter

## The principle

**Blender owns everything that needs the object; Painter owns the layering.**
The low poly is one object with one material per set, so Painter cannot tell a
blade from its leather sheath, and its noises know nothing about which way a
knife points. Blender bakes that knowledge into masks — material classes,
object-space fields, halos — and Painter stacks fills, generators and filters
on top of them, from a script, in one undo step.

The whole look is **a Python file per prop** (`texturizar_sp.py`). Nothing is
clicked. Running it twice gives the same layer stack, so the `.spp` is
disposable.

Measured on the first prop (a combat knife with a leather sheath, 5,648
triangles, one 4096² set): project + bake from a 787k-face high poly 11 s;
applying 124 layer operations 2.3 s; export 11 s; one look iteration, including
a 1080p Cycles check in Blender, under two minutes. About ten applications of
the script took it from a flat first pass to the delivered maps. It is one prop: where a number
appears below, it is that prop's.

**REQUIRED SUB-SKILLS:** blender-props:building-blender-props (phases, folder
layout, toolkit) and blender-props:verifying-blender-props (gates). This skill
replaces phase 9's material bake and changes what phases 10–11 render.

## What is installed where

| Piece | Where | Check |
|---|---|---|
| Painter 12.1 | the only tested version | `python sp.py estado` → `painter`, `project_open` |
| sp-mcp repo | sibling folder `SubstancePainter-MCP` (or `SP_MCP_REPO`) | `scripts\install_plugin.ps1` once, then start Painter |
| Bridge | inside Painter, `127.0.0.1:27190` | the port opens ~4 s after Painter starts |
| Runner | `toolkit/sp.py`, plain Python + `uv` | no Claude Code restart needed: it starts the MCP server itself over stdio |

`scripts\install_claude.ps1` registers the MCP for future sessions but **fails
on Windows PowerShell 5.1 at step 1** (stderr of `claude mcp get` under
`$ErrorActionPreference = Stop`). Do its three steps by hand, or skip it: the
runner does not need the registration.

Painter must be open, **not minimised, session unlocked** — otherwise
screenshots fail with `SESSION_LOCKED` (maps and export still work).

## The flow

Phases 1–8 of building-blender-props are unchanged. Then:

| # | Step | Call | Closes on |
|---|---|---|---|
| 1 | Low-poly FBX (already exported by the build) and the high poly beside it | Blender: `substance.exportar_hp(NOMBRE)` | `<Prop>_HP.fbx` on disk, same axes and scale as the LP |
| 2 | Material-class map from the high poly's materials | Blender: `substance.clases(NOMBRE, LP, extrusion, por_objeto={...})` | class list returned; every expected class present |
| 3 | Object-space fields along the prop's long axis | Blender: `substance.eje_principal([...])`, `substance.campos(NOMBRE, LP, eje, centro, paso=...)` | two PNGs in `Texturas/Bakes/` |
| 4 | Split into grey masks, halos | shell: `python sp_mascaras.py <prop dir> --halo Laton:16 --halo Hilo:9` | printed % per class — **0 % means the low poly never sees that material** |
| 5 | Painter project, bake, import masks | shell: `python sp.py proyecto <Prop> <Set>` | `mesh maps: [AO, Curvature, ID, Normal, Position, Thickness, WorldSpaceNormal]` |
| 6 | Write `<Prop>/texturizar_sp.py` | `sp_receta.Receta` | — |
| 7 | Apply, look, adjust | `python sp.py rehacer <Prop> vistas.json`, read the images | the reference photo, side by side |
| 8 | Export and install | `python sp.py exportar <Prop> <Set>` | `TX_<Set>_{BaseColor,Normal,ORM}.png` in `Texturas/` |
| 9 | Judge under the studio light | Blender: reload images, `entrega.still(..., res=(1920,1080), samples=96, lp=True)` | compare with the reference, then loop to 7 |
| 10 | Deliverables | `entrega.still(..., lp=True)` ×4, `entrega.exportar_y_verificar`, `tanda.cerrar(..., lp=True)` | stills, GLB (it embeds the maps), split with the textured low poly |
| 11 | After the user approves | delete `<Prop>.spp`, `Texturas/Bakes/SP_export/`, `_sp_mcp/`, `<Prop>_HP.fbx` | only the exported maps, the masks and the script stay |

Steps 2–3 leave nothing in the scene and do not save the `.blend`.

**The `.spp` never goes to git.** A project is 225 MB with one 4096² set and grows
with every set; it would break the repo's save flow. `.gitignore`: `*.spp`, `*.spp.*`, `*.assbin`, `**/_sp_mcp/`,
`**/SP_export/`, `**/Exportados/*_HP.fbx`. What makes it disposable is that
masks + script rebuild it in under a minute.

## What Blender bakes for Painter

| Mask | From | Use |
|---|---|---|
| `MK_<class>` | each high-poly material is a class; `por_objeto` lifts a whole object into its own class | group masks — the replacement for Painter's geometry masks, which need separate mesh names |
| `HL_<class>` | dilate + blur of a class, minus the class | verdigris ring on leather around a brass rivet, darkened leather beside a stitch line |
| `CP_Rayado_Largo` / `_Ancho` | anisotropic noise in object space, stretched along / across the long axis | scratches that follow how the object is used; grind lines across a bevel |
| `CP_Manchas` | large soft noise in object space | localising any effect so it is not uniform |
| `CP_Junta`, `CP_Lamina` | stripes at a pitch along the axis; one random value per stripe | stacked washers, planks, laminated parts: per-piece tone |

Why not Painter's own tools for these: a triplanar grunge has no direction, and
a UV-projected one changes direction on every island (128 islands on this
prop). A field baked from world position is seamless and aimed.

Material classes cost nothing to add: letters raised on a leather panel share
the panel's material, so they were invisible to the mask until
`por_objeto={"Estampado": "Letras"}` gave them their own — that is what made
them legible.

## Writing the recipe

```python
from sp_receta import Receta, tri

def construir():
    r = Receta("LP_Cuchillo", "knife")
    A = r.grupo("Acero", clases=("Recubrimiento", "Acero_Filo"))            # mask = MK_ + MK_
    r.capa("Acero base", A, {"baseColor": "#B5B6B9", "roughness": 0.32, "metallic": 1})
    R = r.grupo("Recubrimiento", dentro=A, clases=("Recubrimiento",))
    r.gen(R, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.42, "Grunge_Amount": 0.8}, fusion="Multiply")
    r.capa("Fosfato", R, {"baseColor": "#1F2023", "roughness": 0.54, "metallic": 0})
    f = r.capa("Aranazos", A, {"baseColor": "#A9AAAD", "roughness": 0.36, "metallic": 1}, opac=0.85)
    r.mapa(f, "CP_Rayado_Largo"); r.escaneo(f, 0.09, 0.9)                    # threshold = amount
    r.grunge(f, "Grunge Dirt", 2.0, fusion="Multiply")                        # break it up
    return r
```

Full example: `reference/example_recipe_knife.py` (124 operations).

- Layers stack in call order, later on top. A group's mask clips its children.
- **Under-layer first**: bare metal at the bottom, the coating in a group whose
  mask is the class × an inverted edge-wear generator. Everything in that group
  chips together.
- One material class = one group. Variation, wear and dirt go inside it.
- Every effect gets a mask that localises it. An unmasked grunge over a whole
  class is the "procedural look".

## Traps, each one cost a pass

| Symptom | Cause | Do |
|---|---|---|
| Whole model flat grey, base colour 0.906 everywhere, no error | `disable_channels` on a freshly created fill reassigns its active channels and **resets every source to default** | Never disable. A fill only affects the channels that received a source |
| Screenshot shows the previous state (or bare grey) right after applying | the engine had not finished; `sp_wait_idle` returns with the default 750 ms of quiet | `quiet_ms: 3000` before capturing or exporting (`sp.py` does) |
| `sp_undo` → `Internal C++ object (QAction) already deleted` | bug in the bridge on 12.1 | Do not undo. `sp.py rehacer` deletes the top-level layers and reapplies the script |
| A coating vanished from the whole blade after "reducing" a scratch mask | **Histogram Scan `Position`: higher = MORE white.** 0.09 leaves loose threads, 0.70 covers nearly everything | Start low. Capture before exporting |
| Brown film over all the metal | a rust grunge used as a fill mask with no threshold | Rust and dirt go through the `Dirt` generator (cavities) at `dirt_level` ≤ 0.15, or through a scan |
| Stamped letters, a fuller, a bevel stop reading | dirt and dust layers averaged the values and raised roughness everywhere | Keep the global dust at opacity ≤ 0.10; give the feature its own class and its own tone |
| Leather grain on a stacked-washer handle | one "leather" treatment reused on a part that shows edge grain | Ask what the surface physically is. Washers got per-stripe tone + joint lines instead |
| Exported normal looks inverted in Blender | the default project is DirectX | `sp.py proyecto` creates it in OpenGL. Take the normal from the *Blender (Principled BSDF)* preset at 16 bit |
| No ORM in the Blender preset | it exports roughness and metallic separately | Take ORM and base colour from *Unreal Engine (Packed)*; `sp.py exportar` does both and renames |
| Masks changed after the project was created | importing again under the same name was not tested | Recreate the project (`sp.py proyecto`): 20 s, and the script rebuilds the layers |
| Bake params rejected | names differ from the UI | common: `MaxHeight`, `MaxDepth` (relative to the scene diagonal: 0.007 of 0.36 m = 2.5 mm), `SubSampling`. An unknown key returns the valid list |
| `AO` 0 on a few percent of the map | faces pressed against another part (sheath layers) | Expected; check they are hidden faces before changing anything |

## Getting past "procedural"

The first pass already beat the Blender materials and still read as a filter.
What moved it, in order of effect:

1. **Open the reference photo and name what is different**, out loud, before
   touching a value. Here: the real leather was warmer, more saturated and
   glossier; the real blade was clean black with wear only at the edge. The
   first pass was the opposite — grey-brown, matte, dirty everywhere.
2. **Roughness range, not roughness value.** Median 0.68 with a 0.53–0.78 band
   looked dusty. Median 0.56 with 0.41–0.68 and fills down to 0.24 where a hand
   or oil polishes gave the highlights that describe the form.
3. **Wear that has a cause.** Lengthwise threads on the blade (the sheath draws
   them), polish on the handle's swell, light scuff on the sheath's proud edges,
   verdigris only around brass, dark burnish only beside stitches.
4. **Dirt is the last 10 %.** Global dust at 0.25 opacity greyed the whole
   prop; at 0.10 it reads as dust.
5. **Judge in the render that ships.** Painter's viewport flattered a blade
   that under the studio light showed no fuller. Every iteration ends in a
   1080p Cycles frame of the low poly (15–60 s).

`sp.py medir <Set>` prints base colour, roughness and metallic statistics;
metallic non-binary under ~5 % is the edge-wear transition and is fine.

## What changes downstream

- **Stills and the split show the textured low poly** (`lp=True`), not the high
  poly: the high poly no longer carries the material being delivered. The clay
  still stays on the high poly.
- **`bake_fidelity` no longer applies to colour.** It compared the high poly's
  Blender material against the baked low poly. Use it, if at all, with a neutral
  material on both to check the normal. The judge of colour is the reference
  photo.
- **The GLB embeds the maps**: re-export after every `sp.py exportar`.
- README: say the textures were authored in Substance 3D Painter, list the
  mask set, and keep `texturizar_sp.py` in the prop folder. `asset.json`
  `software` gains `"Substance 3D Painter"`.

## Retexturing a delivered prop

Needs the `.blend` with the high poly, its materials and the final low poly.
The UVs are not touched, so nothing upstream is invalidated. Steps 1–11 as
above. The Blender-baked maps go to `Texturas/Bakes/Blender_v1/` until the user
has compared both.

Worth it where the material tells a story: wood, blued or parkerised steel,
leather, rubber, fabric, painted castings that chip. Low return on clean
moulded plastic and lab equipment — a product-clean surface is mostly its
roughness variation and fingerprints, one short recipe.

## What this does not do

Hand-painted strokes (a specific scratch at a specific place), projection of a
decal onto a curved face inside Painter (bake it in Blender to UV space and
import it as a mask), anything on a UDIM layout, more than one set per project
in one call (untested), Painter versions other than 12.1 (untested).

## Checklist

1. Reference photo open. Three sentences on how the real surfaces differ from a
   new one.
2. `exportar_hp` → `clases` → `campos` → `sp_mascaras.py`; read the percentages.
3. `sp.py proyecto`; seven mesh maps listed.
4. Recipe: one group per class, under-layer first, every effect masked.
5. `sp.py rehacer` with views; look at every image.
6. `sp.py exportar`; 1080p Cycles frame of the low poly; reference beside it.
7. Loop 4–6. Stop when the difference from the reference is a choice.
8. Stills, GLB, sheets with `lp=True`; README; `.spp` stays out of git.
9. On approval: delete the Painter project and its exports.
