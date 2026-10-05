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

Those two came first. The sixteen props of the earlier batch (all built on
`L.union_mecanizada`, 1-5 cast bodies each) were then converted the same day
with the constructions below; figures in "Sixteen conversions". None was
deformed, rigged or subdivided, so "clean" here means: every face a quad, no
face over 100:1, loops that follow the part's axes. It does not mean an
artist-placed edge flow.

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
- **It does not convert a boolean low poly of a machined casting.** Tried on a
  gate valve's three cast bodies (`L.union_mecanizada` result → `Q.retopo(o,
  tris // 2, vivos=30)` → `Q.ajustar` back onto the boolean mesh):

  | Body | Result |
  |---|---|
  | valve body, 3,880 tris | QuadriFlow refused it: "the mesh needs to be manifold" (6 open edges after the boolean clean-up). Left untouched |
  | bonnet, 1,292 tris | 583 quads, but 12 open edges, a torn neck and flange faces up to 6 mm off |
  | handwheel, 1,836 tris | 907 quads, watertight in appearance (6 open edges reported), 0.19 mm median off, rim loops clean |

  One usable out of three, and that one is a torus with spokes. A flanged,
  drilled, machined body is rebuilt with construction 5 instead.
- The result has no edges on the real seam planes. Do not bisect it: mark UV
  seams with `L.costura_por_lado(axis, coords)`, the border between faces on
  either side of each plane (a staircase along existing loops).

**5. Crossing solids — `Q.ensamblar`.** The replacement for
`L.union_mecanizada`, and what converted fourteen of the sixteen. A cast body
is the same list of solids the high poly fuses, each squared on its own
(`Q.cuadrar`), long faces split by ring (`Q.tramar`), and joined into one
object where they simply cross. No boolean, so no slivers and no n-gons; the
silhouette is the union's. What it changes:
- **Faces buried in another solid are deleted** (`Q.quitar_ocultas`: nine
  samples per face pushed 0.05 mm outward must fall inside another closed
  solid), and so are coplanar duplicate caps. Without it a lantern body went
  from 11.7k to 19.1k triangles; with it, 15.0k. The mesh is then **not
  watertight per part**: the open border sits inside the other solid. Say so.
- Two caps in the same plane (a column and its flange both starting at
  z = 166) read as a triangulated moire in the wireframe sheet until the
  duplicate was removed.
- The cuts of the boolean version do not exist here. Each one is a decision:

  | Cut | Without a boolean |
  |---|---|
  | bore, raised face, blind mouth of a turned part | put it in the revolution's profile (a valve's pipe, hubs, faces and bore are one revolution) |
  | pocket, recess or window on a flat face | `Q.bloque` (below) or `F.caja_lazos` + `Q.ventana` |
  | through hole in a plate | `F.anillo_radial` + `F.prisma_anillo`, or `"pasante": True` in `Q.bloque` |
  | step or notch in a box | stack boxes: a tool post with two slots is three boxes |
  | plane that trims several solids | clamp the vertices to it (a valve's machined top also flattens its two pipe flanges: left round, front silhouette went to 1.6 %) |
  | hole that only houses another part | leave it out, the parts cross |
  | shallow groove, knurl, vent, screw slot | normal map (costs fidelity, see below) |

**6. Machined block — `Q.bloque`.** A box whose six faces carry a grid
(`F.caja_rejilla`) with a loop on every pocket edge; each pocket is opened
with `Q.ventana`. Round pockets come out octagonal (four grid corners moved
onto the diagonal). `"pasante": True` sinks to the opposite face and deletes
floor and far faces, which coincide because the grid is the same on both. A
contactor (screw wells, cable mouths, window, side fins, rail slots) is five
blocks and a few boxes: 4,499 quads. Coordinates closer than `tol` (0.4 mm) to
an existing loop snap to it; two loops 0.1 mm apart leave a strip of 300:1
faces. It leaves many poles (20 % of vertices on that prop): every pocket
corner is one.

**7. Plate with a hole of any shape — `F.anillo_radial`.** One ray from the
hole's centre through every vertex of both outlines gives a paired
exterior/interior loop for `F.prisma_anillo`. All exterior vertices survive.
The exterior must be star-shaped from that centre: a flange sector closed by
its inner *arc* hides its own ends and the quads fold (32 triangles, 338:1);
closed by the chord it is clean. A revolver frame is two such rings (cylinder
window, trigger guard) and a lofted grip strap.

Other traps met on the way:
- **Odd outlines.** `Q.cuadrar` now splits the edge ring of the longest edge
  of an odd cap or odd pole fan (`_emparejar`), so both ends become even.
- **Toothed or scalloped caps** (a knurled plug, a dial) fold the Coons grid:
  the fallback is a quad ring to a smoothed inner loop, then the grid.
- **Triangular prisms** (gussets) cannot have quad caps: clip the tip 3-7 mm.
- **`Q.tramar` can run away.** A 0.5 mm strip between two corner arcs took one
  frame to 4.2 million faces and froze Blender for ten minutes. It now stops
  at 6x the face count; fix the strip (radius = half the depth), not the cap.
- **Rounded corners with one segment** are a chamfer whose chord sits r(1 -
  cos 45) inside the high poly: 6 mm on a 22 mm radius, over the bake
  extrusion, baked black. Keep the corner segments when lowering `q`.
- **Long strips kill UV occupancy** once `L.trocear` is gone (a plate edge
  2.5 m long and 16 mm high: 18 %). `L.costura_tiras(step)` adds seams across
  narrow faces only: 18 % -> 71 %.
- **A simulated-cloth style grid in disc mapping** (a helmet shell) has
  near-flat-angle quads on its diagonals; rings and meridians with the crown
  closed by a `Q.cuadrar` grid snapped to the high poly replaced it.
- **QuadriFlow also refused a material-selected patch** (wood grips cut out
  of a fused frame: open, ragged border). A prism of the grip outline with
  gridded caps, snapped with `Q.ajustar`, did it.

## Sixteen conversions

All sixteen: 0 triangles, 0 n-gons, no face over 100:1, 0 UV overlap, FBX
round trip verified.

| Prop | Tris before | Quads now | Silhouette, worst view | Fidelity before -> now |
|---|---|---|---|---|
| Lantern | 11,740 | 7,479 | 0.25 % | 1.82 -> 1.69 |
| Robot arm | 25,942 | 4,216 | 0.16 % | 0.97 -> 1.10 |
| Cine camera | 13,312 | 6,708 | 0.29 % | 1.93 -> **2.04** |
| Drone | 12,108 | 4,880 | 0.23 % | 1.20 -> 1.55 |
| Radial engine | 52,394 | 13,145 | 0.76 % | 5.61 -> **5.67** |
| Microscope | 15,504 | 5,966 | 0.20 % | 0.98 -> 1.02 |
| MIG welder | 14,926 | 4,990 | 0.23 % | 1.09 -> 0.82 |
| Generator | 39,262 | 13,366 | 0.27 % | 1.62 -> 1.82 |
| Pallet jack | 29,980 | 8,608 | 0.25 % | 0.42 -> 0.45 |
| Bench lathe | 37,246 | 12,001 | 0.94 % | 2.19 -> **2.35** |
| Contactor | 14,416 | 4,499 | 0.52 % | 2.66 -> **3.19** |
| Clamp meter | 8,994 | 3,621 | **1.11 %** | 1.63 -> **2.70** |
| Hammer drill | 24,206 | 4,560 | 0.48 % | 2.21 -> **3.41** |
| Gate valve | 11,706 | 7,279 | 0.43 % | 2.64 -> **4.09** |
| Revolver | 27,750 | 8,009 | 0.98 % | 2.80 -> **4.63** |
| Safety helmet | 11,132 | 4,652 | 0.63 % | 1.25 -> 1.76 |

Silhouette is the share of differing pixels. Bold = over the threshold
(silhouette 1 %, fidelity 2.0). Eight of sixteen fail fidelity now; five
failed before. The props that got worse are the ones whose grooves, vents,
knurls and screw slots were boolean geometry and are now normal map: the
fidelity render uses the clean material (no ORM occlusion), so a painted
groove does not shade itself. Multiplying the occlusion into the colour made
it worse (3.4 -> 5.8 on the drill), not better. Putting the fins and rail
slots of the contactor back as `Q.bloque` pockets took it from 4.41 to 3.19
and its silhouette from 1.9 % to 0.5 %. Thresholds were not moved. The causes
on the valve and the revolver were not separated by measurement.

Two measurement traps:
- A helmet's fidelity read 24: `_HP_unido_bake`, the joined high-poly copy
  the baker makes, had stayed in the scene and rendered over everything.
  After removing it and fixing the bake below: 1.76.
- Bake each texture set against its own parts when a thin transparent part
  sits in front of another (a visor 0.7 mm from its support: the support
  baked white), and give a 1 mm part an extrusion under its thickness.

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
