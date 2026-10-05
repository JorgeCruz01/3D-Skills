# All-quad low poly

The low poly ships as **100 % quads**: no triangles, no n-gons. Measured on two
props rebuilt this way (a pump shotgun, 18 parts; a tactical backpack, 14 parts
plus a simulated cloth skin):

| | Before (booleans / decimation, triangulated) | After (quads) |
|---|---|---|
| Shotgun | 16,088 tris | 4,030 quads = 8,060 tris, 160 poles |
| Shotgun silhouette / fidelity | 0.01 % / 0.87 | 0.13 % / 1.27 (both under threshold) |
| Backpack | 22,668 tris | 9,349 quads = 18,698 tris; cloth skin 5,091 quads, 30 poles |
| Backpack silhouette | 0.36–0.47 % | 0.41–0.73 % |

Two props is the whole evidence. Neither was deformed, rigged or subdivided, so
"clean" here means: every face a quad, watertight, no face over 100:1, loops
that follow the part's axes. It does not mean an artist-placed edge flow.

## Where triangles came from

| Source | Why | Replace with |
|---|---|---|
| `L.limpiar` | it triangulates everything on purpose (boolean n-gons) | `Q.cuadrar` |
| `L.union_mecanizada` | a boolean leaves n-gons and slivers | build the body without a boolean (below) |
| `T.diezmar`, a Decimate modifier | edge collapse | `Q.retopo` + `Q.ajustar`, or a native cage |
| `L.trocear`, `L.cortar_en` | plane bisection splits quads | `tramos=` on the prism; `L.costura_por_lado` for UV seams |
| caps of `F.prisma` / `F.loft` / `F.barrido` | one n-gon per end | `Q.cuadrar` (Coons grid) |
| poles of `F.revolucion` | a triangle fan on the axis | `Q.cuadrar` (grid, domed toward the old pole) |

## The four constructions

**1. Native quads + `Q.cuadrar`.** Every `formas` primitive is quads on its
sides. `Q.cuadrar(ob)` replaces each cap n-gon and each pole fan by a grid
(transfinite / Coons patch) without moving a boundary vertex; it tries every
corner placement and keeps the one whose worst quad is best, and refuses a grid
that folds. It needs an **even** boundary: `F.seg` now rounds to even above 4,
and a hand-made outline must have an even point count (`F.remuestrear(C, n,
cerrada=True)`). Read `sin_resolver` in its return: `("polo impar", 19)` was
three parts on the first run.

**2. A cage fitted to the high poly — `Q.ajustar`.** For carved or cast bodies
(a wooden stock, a rubber pad, a housing): build a loft or prism with roughly
the right dimensions and snap every vertex to the nearest point of the high
poly. The topology is yours, the shape is the high poly's.
- Put the section's points **where the curvature is**. An oval of 20 evenly
  spaced points on a stock with 8 mm edge radii left two points per edge; the
  chord sank more than the bake extrusion below the high poly and the whole
  belly baked black. A rounded rectangle with 4 points per corner fixed it.
- The cage must not extend past where the high poly is cut: a pad outline that
  ran 15 mm beyond the high poly's cut plane was flattened against it
  (`max_mm` 13.6 in the return value — read it).
- Tilt the last sections onto an inclined end plane instead of cutting: the cap
  is then that plane.
- Near-vertical features need a section every 4–6 mm (a pistol grip's front).

**3. Holes without booleans.**
- Through hole in a plate or ring-shaped part: `F.prisma_anillo(exterior,
  interior, ...)`, two paired loops with the same point count; caps are a quad
  strip. (A trigger guard: 108 quads.)
- Pocket or window in a lofted body: make the loft's sections and stations fall
  on the window's edges, then `Q.ventana(ob, dentro, fondo)` deletes those
  quads and sinks their border. Rounded ends: move the four corner vertices to
  the 45° point of the arc; the normal map carries the rest.
- A hole that only houses another part: **leave it out and let the parts
  cross.** A tube through a forend, a barrel into a receiver face. It is what
  removes the boolean; declare it in the README.

**4. Auto-retopology — `Q.retopo` (QuadriFlow).** For skins with no generating
solids (simulated cloth). Decimate the high-poly skin to ~60k triangles first
(QuadriFlow on 300k faces takes minutes), remesh to the target quad count, then
`Q.ajustar` to the full high poly. 13 s for 5,091 quads. On a box-like backpack
the field aligned with the body and the pockets by itself.
- On a carved stock with a tight concave grip it left crumpled faces; the
  native cage (2) was cleaner. Try (2) first when the part has an axis.
- `vivos=<degrees>` preserves sharp edges; untested on machined parts.
- The result has no edges on the real seam planes. Do not bisect it: mark UV
  seams with `L.costura_por_lado(axis, coords)`, the border between faces on
  either side of each plane (a staircase along existing loops).

## Gates added

| Gate | Pass |
|---|---|
| `Q.censo(lp)` | `tris == 0`, `ngonos == 0`, `aristas_no_estancas == 0`; report `polos` |
| `Q.desvio(lp, hp_objects, tope=<extrusion mm>)` | every sample over `tope` explained (hidden face, pocket floor). Chords over the bake extrusion bake black |
| `Q.lamina([lp], path, desde, centro=, radio=)` | look at it. A Workbench render of the real edges in 1 s; the viewport screenshot came back black |
| silhouette, fidelity, `puertas.geometria` | unchanged |

`uv_overlap` had a false positive on all-quad meshes (13–33 cells with no
overlap): it rasterized each quad as two triangles with an inclusive test, so a
45° diagonal through cell centres counted twice. It now builds one mask per
face. Proof it was the gate and not the mesh: the toolkit's strict per-face
`uv.caras_solapadas` listed zero faces on the same UVs.

## What this costs

- Silhouette and fidelity get slightly worse than a boolean low poly (table
  above), because rounded window ends, slots and channels move to the normal
  map. Both stayed under threshold on both props.
- The triangle count roughly halves. Do not pad to re-enter a tier.
- FBX keeps the quads. GLB is triangles by format. The normal map is baked
  against Blender's triangulation of those quads; an engine that triangulates a
  non-planar quad the other way will shade it slightly differently. Not
  measured.
