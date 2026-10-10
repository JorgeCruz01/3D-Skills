---
name: building-blender-soft-goods
description: Use when a Blender prop built through MCP or bpy scripts is made of fabric, webbing, leather or padding — backpacks, pouches, vests, straps, bags, holsters, upholstery — or when a hard-surface prop needs a sewn strap, a zipper or a padded part; before choosing between cloth simulation, sculpting and modelling by hand.
---

# Building soft goods in Blender

## The principle

**Fabric is simulated, never drawn; what is sewn onto it is traced, never
placed.** A bag is one closed skin inflated by the cloth solver. Every strap,
zipper and piping run is then projected onto the simulated skin, so nothing
has to be positioned by coordinates on a surface nobody knows in advance.

Everything below was measured on one prop, a 29-litre assault backpack (942k
faces high poly, 22.7k triangles low poly). It is one data point: where a
number is given, it is that prop's.

**REQUIRED SUB-SKILLS:** blender-props:building-blender-props (folder layout,
phases, bake, delivery) and blender-props:verifying-blender-props (gates).
This skill only covers what changes when the material is soft. The code is
`tela.py` in the toolkit of building-blender-props.

## The flow

| # | Step | Call | Closes on |
|---|---|---|---|
| 1 | Pattern: simple solids for each compartment and pad, crossing frankly | `F.prisma`, `F.caja_blanda` | arithmetic review |
| 2 | One skin: fuse, triangulate with random diagonals | `F.fundir(nombre, solidos, 8 mm, suavizado=2)` | closed, ~10k vertices |
| 3 | Vertex groups: pinned, and shrink weight | `T.grupo(ob, "fijo", f)`, `T.grupo(ob, "encoge", f)` | counts > 0 |
| 4 | Inflate | `T.simular(ob, "cordura", presion, frames, fijo, encoge, encogido=(holgura, frunce))` | seconds per frame reported |
| 5 | Measure the skin | `T.medir(ob, area_inicial)` | `caras_cruzadas == 0`, volume against the spec, bounding box against the spec |
| 6 | Finish: smooth, subdivide ×2, shader weave | `T.alisar`, Subsurf, `M.relieve(mat, "tejido"…)` | — |
| 7 | Sewn-on parts, in order: piping → zippers → straps → harness | `T.cincha`, `T.trazar`, `T.cinta`, `T.cajitas`, `T.asentar` | sewn-pair assembly gate (below) |
| 8 | Low poly, all quads: remesh the skin, fit it to the high poly, rebuild sewn parts coarse | `T.diezmar(…, 60000)` → `Q.retopo` → `Q.ajustar`; same builders with `q < 0.5` + `Q.cuadrar` | `Q.censo`, `tanda.malla`, silhouette |
| 9 | UV with seams on the cut planes | `uv.desplegar(names, extra=L.costura_en_planos(...))` | overlap 0, coverage, density |

## Simulation rules

- **Simulate coarse, subdivide after.** Solver time is not linear in vertex
  count: 8,250 vertices took 0.25 s per frame; 40,436 took about 25 s per
  frame — roughly 15 minutes for 35 frames (not timed exactly: the MCP
  connection timed out twice before it finished). Mesh
  the pattern at 8 mm, simulate 40 frames (12 s), then Subsurf. A 4 mm skin
  also wrinkles at the scale of its own edges and reads as crumpled paper.
- **Triangulate the pattern with random diagonals.** A quad grid only folds
  along its two directions; folds come out stair-stepped.
- **One closed skin, not several bags.** Pockets fused into the body and
  pinned along their perimeter give a seam that is a row of fixed vertices,
  not an intersection between two inflated meshes. It also makes the volume
  measurable.
- **Pin what is rigid on the real object**: back pads, a flat bottom, a
  velcro panel, the perimeter where a pocket is sewn to the body. Pinning the
  whole back panel left the top square; pinning only the pads let it round.
- **Slack makes folds; shrink makes cinches.** `encogido=(min, max)` is
  interpolated by the weight of the `encoge` group. Negative = the fabric
  grows (slack), positive = it gathers.

| Setting | Result on a 300 × 160 × 460 mm bag |
|---|---|
| no slack, no shrink | a clean sack: dihedral p95 14.5°, 0 self-crossing faces |
| slack −8 % everywhere | broad soft folds: p95 34°, 11 self-crossing faces |
| slack −10 %, seams shrunk +12 % | crushed paper: p95 81°, 69 self-crossing faces, volume −19 % |
| shipped (full pack): slack −4.5 %, cinch +3 %, faces under webbing at 0 | mean dihedral 5.0°, 0 self-crossing |

- **A face that carries sewn webbing gets no slack** (weight 0.6 between
  −4.5 % and +3 %). Shrinking each webbing row instead crumpled the pocket
  face and every row laid on it came out twisted.
- **Fabric type barely matters at this resolution.** Cordura and thin nylon
  stiffness presets gave the same folds at 8 mm (dihedral mean 7.42 vs 7.51).
  Change slack and pressure, not stiffness.
- **Pressure adds size.** Pressure 25 added about 17 mm per side and pushed
  the unpinned bottom 25 mm through the floor. Measure the bounding box after
  simulating and shrink the pattern; do not trust pattern dimensions.
- **The independent check is enclosed volume** against the capacity of the
  product class. The first skin that met all three dimensions held 27.1 L
  against a 28–40 L window declared beforehand; the body was raised 27 mm.

## Tracing what is sewn on

`T.trazar(surface, guide, …)` projects a rough 3D polyline onto the skin and
tensions it; `T.cincha` adds the ribbon. Pick the projection by what the part
does:

| Part | Projection | Why |
|---|---|---|
| A row stitched across one face (PALS webbing) | `rayo=(direction)` — fixed ray | nearest-point slides on a bulged face: horizontal rows came out wavy |
| A run around one bulge (zipper, piping) | `hacia=(centre of that bulge)` | nearest-point jumps to the neighbouring pocket in the gap between two |
| A strap wrapping a corner | default nearest-point | no single direction sees the whole path |

- **With a ray, offset against the ray, not along the surface normal.**
  Offsetting by the normal moved a row 4 mm sideways over 40 tension passes.
- **Keep the ray origin close** (`retroceso`). Backing off 80 mm from a guide
  near a pocket put the origin inside the pocket above it.
- **A ribbon is as wide as the surface is curved.** Traced on its centre
  line, a 25 mm strap digs in at both edges (2,497 crossing faces on the
  compression straps). `T.cincha` lifts it over its full width (`apoyar`); a stitched row
  conforms across its width instead, lofted between parallel tracks — a rigid
  strip resting on the highest point floated millimetres off a bulged pocket
  and the bake left black holes under it.
- **Later parts trace over earlier ones.** Compression straps are traced on
  `T.arbol_de([skin, piping, zipper tape, zipper teeth])`, so they pass over
  the zipper instead of through it. Order: piping, zippers, straps.
- **Seat rigid parts with rays, not with normals.** `T.asentar(ob, tree, n)`
  lifts a buckle or pull tab until no vertex is under the surface. A
  nearest-point normal on zipper teeth points sideways.
- **Repeated small solids go in one mesh**: `T.cajitas` builds zipper teeth
  and bar-tack stitches as boxes along a path.
- Thin ribbons are built square-edged. Rounding a 1.2 mm strap by 0.3 mm
  left end caps with 0.2 mm edges beside 25 mm ones (106:1).

## The assembly gate changes

Sewn goods cross on purpose: piping sits in the fabric, a strap enters its
buckle, a shoulder pad is sewn into the back. `pairwise_intersections` on the
backpack reported 29 crossing pairs; 17 were sewing and 12 were defects.

Write the allowed pairs down in the builder (`COSIDOS` in `construir_hp.py`)
and fail on anything else. Do not skip the gate and do not raise a margin:
the 12 real ones were straps inside the fabric, buckles sunk into it, a strap
pierced by zipper teeth and a patch crossing its panel.

## Low poly and UV

- **The low poly of a simulated skin is an automatic quad remesh fitted to the
  high poly**, not a rebuild (there are no solids to regenerate) and not a
  decimation (triangles). `T.diezmar(name, hp_skin, 60000, col)` to make it
  light, `Q.retopo(skin, 5200)` (QuadriFlow, 13 s), `Q.ajustar(skin, [hp_skin])`.
  Measured: 5,091 quads, 30 poles, 0.84 mm maximum snap, loops aligned with the
  body and the pocket faces without any guidance. Nobody placed a loop by hand
  and it was never deformed.
- **Sewn-on parts are already quads**: `T.cinta`, `F.barrido`, `F.loft`,
  `F.caja_blanda`. Replace `L.limpiar` with `Q.cuadrar` for their caps. 14
  parts, nothing left unresolved.
- **An organic skin unwraps as one island.** It has no sharp edges. Splitting
  it by face class leaves a zigzag border and hundreds of one-face islands (965
  islands, coverage 39 % on a triangulated skin). On a quad skin, mark the
  seams as the border between the faces on either side of each real seam plane:
  `L.costura_por_lado("Y", coords)`, combined with `L.cualquiera`. 459 islands,
  coverage 52.0 % (the plane-cut triangle version gave 424 and 52.7 %). Do not
  bisect the mesh: it splits quads.
- **Hide the original low poly while baking against its proxy.** A decimated
  skin weaves in and out of the high poly and occludes it in blotches.

- **A hero low poly wants three times the first budget.** The 5,091-quad skin kept folds and pocket edges in the
  normal map; at 15,831 quads (QuadriFlow, 20 poles, 0.67 mm snap) silhouette error fell from 0.43 / 0.41 / 0.73 %
  to 0.10 / 0.05 / 0.56 %. Give the builders a middle setting between "high" and "low" (a module flag the low-poly
  builder switches on): strap pads with 20 sections instead of 3, piping in 6 sides, webbing sampled every 9.5 mm.
- A raised patch and the zipper teeth strip are geometry, not bake.

## What this flow does not do

Worn, empty or draped fabric (it produces a new, stuffed bag); anything that
opens; garments on a body; leather creases from use. Those need sculpting or
a draping simulation with gravity and colliders, which have not been run
through this pipeline. Sewn panels with sewing springs were not tried either.
Say which of these the prop would need and that it is untested, rather than
stretching this flow over it.

## Checklist

1. Reference photos first; note where the real fabric folds and where it is taut.
2. Declare dimensions, tolerance and the capacity window in `Specs.md`.
3. Pattern → fuse at 8 mm → random triangulation → groups → simulate → `T.medir`.
4. Bounding box and volume against the spec. Fix the pattern, not the numbers.
5. Sewn-on parts in order; build one row and render it before building forty.
6. Geometry gate; assembly gate with the sewn-pair list; decal visibility.
7. Low poly in quads: remesh, fit, coarse sewn parts with gridded caps; census and silhouette gates.
8. Unwrap with seam predicates; bake; read the fidelity difference image before changing anything.

## Making the fabric read

A first backpack came back as "the textures do not stand out". Three changes,
all in the high-poly materials (so both the stills and the bake get them):

| Problem measured in the render | Change |
|---|---|
| cloth and webbing at nearly the same value | webbing and piping dark, thread light: the sewn pattern draws itself |
| weave only in the normal map, gone under frontal light | `M.relieve(..., tinte=0.55)`: the valleys also darken the base colour; pitch 2 mm at 3 px/mm |
| one tone over the whole pack | `M.pbr(..., polvo=, altura_polvo=(0, 0.14), sol=)`: layers that depend on position, not only on cavity and edge |

First attempt overshot: dust up to 200 mm plus edge wear at 0.5–0.6 washed the
whole pack pale, and thin webbing reads as "all edge" to a pointiness mask.
Wear on webbing ≤ 0.2. One prop; the user's verdict on the result is pending.
