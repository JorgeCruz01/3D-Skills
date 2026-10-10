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
applying 118 layer operations 2.3 s; export 11 s; one look iteration, including
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
| 10b | Masters for the portfolio session | `entrega.maestros_1610(NOMBRE, hero, "render"\|"vistas"\|"split", lp=True)` | 3200×2000 PNGs in `Renders/Portafolio_16x10/` + a `manifest.json` with hashes, cameras and measured figures |
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
| `ZN_<zone>` | `substance.zonas(NOMBRE, LP, {"Mano": [((x, y, z), radius_m), ...]})`: spheres with a smooth falloff, baked from the low poly itself | what happens in ONE place: wood darkened and polished by the hand, finish eaten where the cheek rests, soot and a bright crown at the muzzle, brass rubs at the ejection port, knocks where the gun is set down. Multiply by a grunge |
| `BD_<class>` | `sp_mascaras.py --suavizar Class:Neighbour:sigma_px` | two classes on ONE part (checkering panel vs wood) are split by high-poly FACES, so the border bakes as a staircase. This rounds it (blur + threshold inside the union, both `MK_` rewritten) and writes the border band: the dark fillet a real checkering panel has, which also hides what is left of the staircase in the normal map |
| panel `MK_` / `BD_` / `PN_` | `substance.posicion(NOMBRE, LP)` (per-texel object position, 16 bit) + `Bakes/paneles.json` (`{"plano": [0, 2], "normal": 1, "paneles": {name: [[u, v] in metres]}}`) + `sp_paneles.py <prop> --clase X --vecina Y --filete 0.9 --cara 9` | a shape that sits ON a part (checkering panel, label, painted zone) drawn as a CURVE: exact border, fillet of real width in mm, inward gradient. Prefer this to splitting the part by high-poly faces + `--suavizar`: an eight-point polygon reads as a straight-sided patch whatever the texture (client: "they look very low poly"). Limit the high-poly relief with a vertex attribute: `M.relieve(..., atributo="picado", hundido=True)`. Side test in mm from the symmetry plane, not as a fraction of the bounding box (a bolt handle off-centres it and one side went missing) |
| any exact band or ring in model space | sample `POSICION.png` yourself (`reference/example_position_mask_revolver.py`, 20 lines) | a cylinder's 0.5 mm drag line at a given height: independent of the UVs, exact in millimetres |
| `CP_Relieve_Canto` / `_Hueco` | curvature of the Blender-baked normal (`NORMAL_blender.png`) | crests and valleys of shader relief: dirt in checkering, polish on knurl crests |

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

Full example: `reference/example_recipe_knife.py` (118 operations).

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
| 4K Cycles stills crawl after texturing (two stills not written after four minutes; they had taken 40–70 s each) | Painter keeps the 4096² project in video memory: 11.7 of 12.3 GB used with both open | `python sp.py llamar sp_project_close` before the final renders (freed 2.7 GB); the project is already saved by `exportar` |
| Grooves, knurling, a recoil pad's pattern gone from the normal map; curvature flat on those parts | that relief was never geometry: it is shader bump in the high-poly materials (`M.relieve`). Painter bakes geometry only | Blender: `substance.normal_hp(NOMBRE, LP, extrusion)` (15.8 s for 1.28 M faces); shell: `sp_mascaras.py` (now also writes `CP_Relieve_Canto` / `CP_Relieve_Hueco` from that normal), `sp.py normal <Prop> <Set>` to set it as the project's `Normal` mesh map. Check first: `BUMP` in a material's node types |
| The same curl-shaped mark every few centimetres along a barrel | `Metal Edge Wear` and `Dirt` project their internal grunge through the UVs | `Use_Triplanar: 1` on both (`Receta.gen` sets it by default). A triplanar grunge multiplied into a long scratch mask repeats too: break scratches up with `CP_Manchas` instead |
| `sp.py medir`: 25 % of metallic between 0.1 and 0.9 | dust, grease and rust fills with `metallic: 0` at partial opacity over metal | thin dirt layers carry colour and roughness only; 1.6 % after |
| Blender renders the old textures after `exportar` (and `im.reload()` reloads them happily) | a `.blend` moved from another folder keeps absolute image paths to the old one | `bake.material_final("LP_<set>", {map: path})` with the prop's own `Texturas/` paths before the first check render; look at `image.filepath` |
| Blued or parkerised steel reads as plastic | modelled as a dark non-metal | bluing is an oxide on steel: `metallic 1`, base colour around #15171C, roughness 0.36; the bare steel underneath only differs in value |
| Fill with `material="Wood Walnut"` → `QAction already deleted` | the name is a SMART material; `set_material_source` wants a base material, and the bridge's error handler then fails on its own undo lookup and hides the real message (`Expected a substance material`) | Any `QAction already deleted` from `sp_apply_recipe` means "one op raised". Reproduce the suspect op with `sp_exec_python` to read the real error. Base materials: `rs.search(q)` filtered by usage `BASE_MATERIAL` |
| Same error after changing a generator parameter | `grunge_scale: 3.3`: integer parameters reject floats | integers stay integers |
| Wood (or any image-filled layer) pure white in the captures | 3 s of quiet is not enough when fills carry bitmaps | `sp.py rehacer` now waits 8 s of quiet; if a capture is white, capture again before changing anything |
| Diagonal grain relief fighting the grain painted in Painter | the high poly's own wood material has a scanned normal map, and `normal_hp` baked it in | `substance.normal_hp(..., sin_grano=("M_Nogal", ...))` mutes texture normals and keeps the carved relief |
| Lines look diagonal in a 3/4 orthographic preview | they were not: a pure side view showed them along the axis | check direction claims in an axis-aligned view before hunting a cause |
| A straight-edged pale band across a stock | `Grunge Wipe Dusty` has straight wipe borders | localise finish changes with `CP_Manchas`, not wipe grunges |
| `sp.py exportar` → `Errno 22` copying the normal | Blender had the 16-bit map open while rendering | `exportar` retries for 24 s |
| A black wedge at the heel of a stock; pointed mitres at the forend tip | the low poly had 5–6 sections across an end where the high poly rolls over (`Q.desvio` max 3.4 mm, above the bake extrusion — reported and shipped anyway), and the slab's edge rounding follows distance-to-outline, which mitres at every sharp corner | round the OUTLINE first (morphological opening), give the low poly ~14 sections per rolled end, and treat any `desvio` max above the extrusion as a defect to look at, not a figure to note |
| A flat part inside a deep pocket bakes with a saw-tooth border | bake rays land on either side of a wall perpendicular to the surface | draw the part as a panel: `sp_paneles.py --clase X --vecina A,B --aplanar 0.2` gives the exact mask, a shadow-gap band (`BD_`) and a flat normal inside |
| Cycles stills three times slower (100 s vs 34 s) with the Painter PROJECT already closed | Painter keeps the video memory while the application is open (8.8 of 12 GB) | quit the application before final renders; relaunching takes 40 s |
| A thin rod or wire comes out stripped bare | to `Metal Edge Wear` a 5 mm part is all edge | give the coating back after the generator: `r.mapa(group, "MK_<class>", fusion="LinearDodge", opac=0.7)` |
| A deep pocket fills with a flat beige or brown slab | the `Dirt` generator saturates where occlusion is total | corner dust and rust at opacity ≤ 0.2 with a low `dirt_level` on props with pockets |
| White torn patches along a thin rim (trigger guard) in the textured low poly | the low-poly surface there was crumpled, the bake cage missed the high poly | fix the MESH (`vivos` on the remesh), not the bake distance. Render the low poly alone in grey before blaming a map |
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
6. **Use zones.** A generator spreads wear by curvature and occlusion, the same
   over the whole part. What makes a used object credible is what only happens
   in one spot. On a shotgun: five `ZN_` masks (hand, cheek, muzzle, ejection
   port, resting points) carried more than any grunge.
7. **Scanned wood, not stretched noise.** Grain made from anisotropic noise
   read as synthetic. A CC0 wood scan as the fill's base colour, roughness and
   normal, in triplanar (`proy={"mode": "Triplanar", "scale": 3}`) so the grain
   runs along the prop, then a Multiply tint. Import it first:
   `sp.py importar <Prop> Texturas/Fuente/<id>/<file>.jpg`. Keep the scan's
   normal at ~0.15 opacity: at 1.0 an oiled stock reads as barn wood.
8. **A scratch grunge dense enough to read as texture is too dense**: at
   Histogram Scan 0.16 fine scratches hid the grain; at 0.05 they are scratches.

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

## The recipe survives a new mesh

The low poly of the knife was rebuilt after the look was approved (5,648 →
11,624 triangles, new UVs). Nothing in `texturizar_sp.py` changed: re-run steps
1–5 and 7–8 and the same look lands on the new layout, because every mask is
re-baked from the high poly and every noise is triplanar or object-space.
That is the test of a recipe: **nothing in it may depend on where an island
sits.**

## UVs worth texturing

The automatic unwrap (seams at 50° plus a safety net that keeps cutting
self-overlapping islands) gave the knife 128 islands at 61.6 % coverage. Seams
written per piece type gave 93 islands at 75.0 %, with zero overlap. Three rules, all in that prop's `construir_lp.py`
(copy in `reference/example_uv_seams_knife.py`):

| Rule | Why | Measured |
|---|---|---|
| **Seams by what the piece is**, not by angle. Carry a face attribute with the piece index through the join. Slab: broad faces vs rim. Tube: around each cap and one line along the underside. Folded band: broad faces vs edges, and where the band turns over | an angle threshold cuts a moulded ramp off its panel and leaves a pommel in one piece | 128 → 65 islands before the safety net, 7 overlapping faces left |
| **No strip longer than ~130 mm.** Cut rim and edge strips at intervals along the piece | the longest island sets the scale of the whole atlas: one 420 mm edge strip of the sheath back was holding everything else at 61 % | 57.4 → 74.0 % coverage (hidden islands already reduced) |
| **Hidden islands at 0.55 scale**, then repack. Hidden = over 70 % of the island's area casts a ray along its normal into the same mesh within 9 mm | faces pressed against another part, or looking into a cavity, do not need the density of the hero faces | 18 of 93 islands, 273 of 1,090 cm². Alone it LOWERED coverage (61.0 → 57.4 %): the packer could not grow past the long strip. It pays only after rule 2 |

Pick the tube's lengthwise seam as the vertex column *nearest* to straight
down, not the one at exactly 0°: on a 40-sided pommel no column sat at 0°, the
skin got no seam and unwrapped as a figure eight.

A long gun (`reference/example_uv_seams_shotgun.py`; 8,060 → 20,202 tris, automatic
unwrap → 104 islands at 77.2 %, 0 overlap, 6.37 px/mm) added:

- A cap behind a 45° chamfer never reaches the angle threshold: barrel and
  magazine tube unwrapped as a hexagon with a fan at each end. Put the cap seam
  by normal (`|n·axis| > 0.7`).
- A tube's lengthwise seam faces the part that covers it (barrel: down, toward
  the magazine; magazine: up).
- A symmetric part splits on its symmetry plane (stock: comb and belly lines).
- A skin longer than the atlas is cut where another part crosses it.
- A bore is a hidden island no short ray detects (opposite wall 18 mm away):
  declare it with `tambien=` of `uv.encoger_ocultas`, keeping the 45 mm seen
  from the muzzle. `uv.encoger_ocultas` and `uv.soldar_uv` now live in `uv.py`.

A sheet-metal gun (`reference/example_uv_seams_smg.py`): **sheet metal is developable, so each body is ONE island**,
opened along a single line on the face the other body covers. "Flat side vs rounded edge" plus strip cuts gave 311
islands; this gave 173 at 65.8 %. A swept rod (700 mm of 5 mm wire) gets its seam along one generatrix and a ring
every 110 mm, marked on the loose part where vertices are still ring-ordered (an edge attribute survives the join).

A cast part (revolver frame with its grips, hammer, trigger; `reference/example_remesh_cast_parts_revolver.py`;
16,018 → 36,598 tris, 65.2 %, 11.98 px/mm, 0 overlap) is not built, it is **remeshed from the high poly**: a cage of
crossed prisms gives hard edges the normal map cannot round. What that cost:

- QuadriFlow answers `mesh needs to be manifold` on a manifold mesh when edges are shorter than 1e-4 units. Scale the
  copy ×100 around the remesh (`quads.retopo(..., escala=100.0)`).
- **Pass `vivos=28` (degrees).** Without it the loops cross the rims of a trigger guard and its joint with the grip
  comes out crumpled; it only shows in a grey close-up of the low poly ALONE, the textured render hides it behind
  the normal map until the bake tears there.
- Relax after snapping (smooth all vertices 0.5, snap to the high poly again, three times): QuadriFlow leaves wavy
  loops wherever they follow no edge.
- A straight tube must stay BUILT. Remeshed, a barrel ripples along its length.
- No loops means no seam lines: cut by face orientation (side `|n.x| > 0.78` vs rim, rim by ±Y/±Z), and add the
  `"aislar"` refinement steps of `uv.desplegar` instead of lowering the safety-net threshold to 0 (that gave 801
  islands; `"aislar"` gave ~190). Island borders come out jagged: say so in the README.
- Do NOT run `uv.soldar_uv` on a remeshed mesh: it left two overlapping faces.
- Replicated parts (five of six cartridges) overlap the first on purpose: measure overlap on a copy without them.

`uv_density` deviation no longer reads as a defect once hidden islands are
scaled on purpose: report the density of the visible islands and say which
ones were reduced.

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
