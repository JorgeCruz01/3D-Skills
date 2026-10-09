# Build lessons, by phase

What sixteen props taught about HOW TO BUILD, each with the prop and the
number. Traps that are already written up in verifying-blender-props ("Traps
verified in production") are not repeated here; where one matters it is named
with "→ verifying".

## Dimensions (`construir_<prop>.py`)

- **Review the constants arithmetically before building.** Most first-build
  crossings were visible in the numbers. Welder: two feed rollers of radius 16
  and 11 with centres 25 mm apart overlap 2 mm. Radial engine: cylinders sank
  25 mm into the crankcase, magnetos sat in the path of the intake tubes, the
  stand flange stopped 6.5 mm short of the crankcase. Drone: propeller hub
  floating 3.8 mm above the motor shaft. Lathe: spindle flange 2 mm inside the
  chuck. All caught on paper. What the review missed cost a build: the same
  engine still had 28 crossing pairs on its first build (intake tubes starting
  where the crankcase is 150 mm in radius, not the 137 assumed).
- **Let a functional constraint size the part, not the envelope.** Radial
  engine: a 108 mm bore forces the barrel to ≥ 57 mm radius at the fin roots,
  70 mm with fins; seven of those do not fit round a crankcase under 161 mm
  radius. That is where the 165 mm crankcase and its flat seats came from.
- **Functional independent checks beat a published figure.** Turret rotated
  120° and 240° with 0 crossings (cine camera, three lenses of different
  length); four propellers swept 0–165° in 15° steps, 0 crossings in 12
  positions (drone); a standard S200 spool fits and the door closes, wire path
  in one plane x = −40.0 (welder); forks occupy 115–275 mm and enter a
  europallet's 72.5–300 mm openings (pallet truck); tailstock point at
  y = 0.00, z = 200.00 on the spindle axis (lathe). → verifying, "Independent
  check".
- **Name which dimensions are published and which are estimated**, in
  `Specs.md` before modelling and again in the README. Typical split: envelope
  and one or two functional figures published, everything else "by proportion
  in the photo".
- **A data sheet's W × D × H does not say which axis is which.** Cine camera:
  216 × 152 × 76 with no axes; the tall body was an assumption, declared.

- **When two parts must fit, write the fit as the independent check.** A blade
  did not enter its own sheath (1,236 crossing faces, up to 0.99 mm) with every
  geometry gate green: the spine and ricasso carry full thickness to their
  edge and sat under the ramp of the moulded front. Copy the part into its
  seated pose, run `pairwise_intersections` and `surface_distance`, delete the
  copy. Four passes to zero.
- **A prop that lies flat is posed, not placed.** Rotate about the short axis
  by bisection until the lowest point on each side of a cut touches the floor
  together, store the matrix on disk, and place the low poly with the stored
  matrix instead of posing it again.
- **A flat-lying prop needs its own light gain.** The rig is tuned for
  standing props; faces looking at the ceiling got 2.2x and brown leather
  rendered salmon. `estudio.GANANCIA = 0.9` before every render, sheet and
  fidelity measurement of that prop.

## Solids

- **Round in the plane the viewer sees.** `caja_blanda` rounds the four edges
  parallel to Z with `r` and the caps with `canto`. A clamp meter's display
  glass came out 3.7 mm thick instead of 0.7 because its corner rounding was
  applied in the wrong plane; a revolver latch was rounded as seen from above.
  Build the box in the plane where the radius belongs and rotate the mesh
  (`_caja_x` in `construir_revolver.py`). The bounding box gave it away, not a
  render.
- **A stepped part is one stepped outline extruded, not boxes unioned.** Lathe
  jaws made of three boxes with 0.1 mm of overlap: 12 faces at 186:1.
- **Split long profiles before revolving or sweeping.** A tailstock quill whose
  taper ran tip-to-base in one span: 64 faces at 184:1. Rollers with a
  0.56 × 70 mm bore face: 96 faces at 124:1; fixed by splitting the profile
  across its width. A 34 mm shaft with 0.6 mm facets was bisected every 2 mm
  (lantern). → verifying, "Long thin parts".
- **`prisma(bisel=...)` bevels toward the outline's centroid** unless
  `por_normal=True`. On a concave outline the default leaves a ridge (drill
  trigger, visible in the side still); a mitred bevel on a thin trigger gave
  faces at 328:1 (revolver). Use `por_normal=True` on anything elongated or
  concave, and keep the bevel under the local outline radius.
- **A soft-edged slab is a plain prism plus heavy smoothing.** Revolver stocks
  with a rounded edge made of inward-offset rings self-crossed at heel, toe and
  front lobe, and the remesh filled the bay under the lobe. Limiting the edge
  to the local radius and triangulating the caps did not fix it. The stock is
  now a flat prism remeshed at 0.5 mm with `suavizado=200`, then thickened
  toward the heel by moving vertices. The edge radius is whatever the remesh
  gives — the builder's comment expects about 5 mm, the README reports about
  3 mm and "less round than the photo".
- **Two wire rings that pass through the same points are offset, not unioned.**
  Lantern guard: 15 open edges from the boolean; the rings are 0.8 mm apart in
  height and joined as two shells with `F.unir`. → verifying, torus seam.

## High poly (`colada.colar`)

- **Voxel size follows the prop's size.** First builds with a handheld voxel
  on a large prop: robot arm 3.7 M faces at 0.6 mm fine voxel on an 800 mm
  robot → 1.85 M at 0.9; generator 6.8 M at 0.55 mm → 2.8 M at 0.9–1.2 (fins
  multiply surface); radial engine 4.8 M → 3.0 M at 1.1–1.35. Values that
  shipped (coarse / fine, mm): contactor 133 mm 0.45 / 0.22; clamp meter
  207 mm 0.5 / 0.28; lantern 265 mm 0.7 / 0.38; revolver 305 mm 0.5 / 0.3;
  microscope 486 mm 1.0 / 0.65; welder 485 mm 1.1 / 0.7; lathe bed 699 mm
  1.2 / 0.8; engine crankcase 930 mm 1.4 / 1.1. Fine voxel ≈ largest dimension
  / 700–1000.
- **`suavizado` sets the fillet: radius ≈ voxel × √passes.** Revolver frame,
  0.5 mm × √12 ≈ 1.7 mm ("with 3 the joints read as sharp"); drill housing,
  30 passes for ≈ 3 mm between motor, grip and foot; generator engine block,
  1.2 mm × √14 ≈ 4.5 mm casting fillets; tube cage, 8 passes ≈ 3.4 mm weld
  beads. Sheet metal and precise plastic stayed at 2–3.
- **Machined volumes go in `exactos=`**, unioned after the casting is smoothed,
  so generous fillets do not melt them: lathe bed ways, cross slide, compound
  and tool post (`EXACTOS = {"_bancada", "_transversal", "_charriot",
  "_torreta"}`), with `suavizado=16` on the casting around them.
- **Smoothing rounds the corners of every window.** A part fitted into a cast
  opening needs more clearance than its nominal gap: contactor contact carrier
  at 0.2 mm, 248 crossings; welder display glass 0.5 mm from the window edge,
  32 crossings. → verifying, "A flat recess cut into a curved housing".
- **Fine detail only at high `q`.** Vents, grilles, screw crowns and slots are
  cutters created under `if q > 0.5:` (or `> 0.9`); the same function serves
  the low poly without them.
- **Paint by cutter, not by hand.** `colada.pintar(obj, [(1, ("_panel",
  "_lcd"))])` gives the faces touched by those cutters material index 1;
  `colada.pintar_por(obj, 2, lambda c: c.z > 161.5 * MM)` paints by
  coordinates (clamp meter: fixed jaw in another plastic). A revolver's wood
  stocks are the same skin as the steel frame, painted by coordinates — and
  declared as such.
- **Flat text does not wrap.** Brand relief on a lantern fount of 62 mm radius
  came out uneven and was dropped; the brand sits on the flat filler cap.
- **Decals float a few hundredths of a millimetre.** Flat text 0.03–0.04 mm in
  front of its face (clamp meter, lantern). On a curved carrier that is not
  enough: on a drone's super-elliptic side the surface has moved 1.7 mm inward
  11 mm from the centre and 2 of 206 vertices went under; a cine camera's
  counter digits were 0.05 mm behind their face. → verifying, `decals_visible`.
- **First hero too clean.** Lantern enamel read as new plastic: darkened, and
  `M.pbr` gained `manchas` and `desconchado`. Lens barrels painted with wear
  0.9 came out brass → their own enamel at 0.2 (→ verifying, Pointiness).

## Low poly

- **Same solids, lower `q`, no decimation.** `q` that shipped: 0.4 (clamp
  meter), 0.5 (lantern), 0.8 (revolver — 0.5 faceted its curves), 0.9–1.0 on
  large props whose solids are already coarse (generator, radial engine, with
  per-part factors `0.6 * q`, `0.8 * q`).
- **`conservar` = cutters that change the silhouette or house a part.** The
  rest goes to the normal map. Lantern: only `_hueco_base`. Clamp meter:
  recesses plus grip slots, trigger ribs and dial scallops.
- **Under budget means silhouette detail is missing, not that triangles should
  be added.** Clamp meter first LP 2,424 tris with 50 mm triangles on the body
  → 8,994 after moving silhouette features into geometry and adding
  intermediate sections. Drill 4,182 → 12,044. Cost: the clamp meter's UV
  coverage fell from 73 % to 55.5 % (many small islands).
- **Do not pad to reach a tier.** Lathe 20,164 against 25–60k ("mostly prisms;
  not filled to comply"), drone 12,108, cine camera 13,312, welder 14,926
  against 15–30k: declared.
- **Slicing costs triangles.** Generator: 16,154 of 25,050 tris are cage and
  tank, sliced every 60 mm — finer than the silhouette needs. Pallet truck at
  29,980, the ceiling of its tier, for the same reason. Pick the largest step
  that passes 100:1.
- **Slice in the zero pose, then rotate.** Robot arm: `trocear` cuts with
  world-aligned planes and the links were already rotated; the wireframe shows
  irregular triangulation on arm and elbow.
- **Per-part `soldar`, tried against the gates.** Lantern body 0.3 mm → 2
  non-manifold edges, 0.1 clean; clamp meter housing 0.3 → 2 faces at 138:1,
  0.5 clean; contactor 0.6 closed 0.8 mm fins (10 non-manifold edges), 0.25
  clean; pallet truck chassis watertight only at 1.4. When no value works, the
  solids are wrong: a robot elbow fairing of 50 mm half-width was tangent to a
  50 mm forearm cylinder — 9 open edges at every setting. → verifying.
- **Solver per part.** `MANIFOLD` by default; `EXACT` where cutter caps are
  coplanar with the target (clamp meter dial: 49 open edges with MANIFOLD).
  The opposite also happened: an EXACT union left faces at 11,000,000:1 on a
  lantern burner and MANIFOLD plus edge collapse was clean.
- **Repetition.** Build one, `L.marcar([part], "Rep_<x>")` before joining,
  unwrap, then `L.replicar(lp, {"Rep_<x>": [matrices]})`. Radial engine: one
  cylinder of 4,742 tris with its own set, six replicas; 33,194 of 52,394
  tris use one texture set. Contactor: 9 power screws, 10 auxiliary screws and
  9 terminal clamps are three replicated parts. Mirrored parts that are
  genuinely handed keep their own UVs (drone: two propellers per rotation
  sense, built mirrored).

- **Low-poly rows go on the creases of the form** — a bevel line, the foot and
  crown of a ramp, the edge of a pocket — with the same guide curves the high
  poly uses. Rows spread evenly or by cosine put a chord across every crease.
- **Three ways a loft ships faces over 100:1** (knife and sheath, all caught by
  the geometry gate): cosine-spaced rows with many rows (first step 0.0024 mm
  beside 0.25 mm stations: 1,144 faces); a diagonal end cut read as a wedge of
  ever shorter sections (3,797 faces — shear the section coordinate so the cut
  is one whole section); and the leftover step `np.arange` leaves before the
  end coordinate (0.002 mm, 3568:1 — use `linspace` with a computed count).
- **A blade edge of zero thickness welds its two faces in patches** near the
  tip (195 open edges). Keep a few microns.
- **A pointed tip of a row-based surface**: bands squeezed towards the point
  leave a 232-vertex cap inside 0.06 mm (1741:1), and merging it to a point
  gives 236:1 fans. Blend the rows to an even spread as the section height
  drops, and let the thickness fall with the height.

## UV

- **One object per texture set until unwrapped; `juntar()` after.** Lantern:
  globe unwrapped with the body got a corner of an atlas that was all its own.
  Sets by material family and by density need: glass always separate.
- **Call `uv.desplegar` once per set**, with that set's objects.
- **Own seams go in `extra=`**: inner equator of wire rings (lantern
  `costura_aros`), slice planes (`L.costura_en_planos("X", L.PLANOS[name]["X"])`),
  orientation classes (`L.costura_por_orientacion((0, 0, 1), 0.5)`), combined
  with `L.cualquiera(...)`.
- **Orientation seams raise coverage and shred edges.** Cine camera body:
  30.9 % → 74.9 %, but 250 islands, and its smooth-area fidelity (1.33) is the
  worst of the batch. The refinement had not fired at all on a single 650 mm
  strip: read `info["refinado"]` after every unwrap.
- **Read what the refinement did.** Pallet truck: 763 and 579 seams added at
  threshold 0, coverage 46 % and 41 %.
- **What coverage to expect.** Of 30 texture sets, 5 reached the 65 % target,
  1 fell under the 40 % floor (a 660 × 600 mm base plate, 28.9 %). Wire and
  long strips pack badly (lantern 52.1 %); flange rings leave their centre
  empty (valve 51.5 %).
- **Density above twice the floor means the set is too big.** Clamp meter at
  13.9 px/mm against a floor of 5: a 2048² set would do. Declared, not changed.

- **A seam that does not close its island** leaves both sides a fraction of a
  texel apart and overlapping: two faces, 0.0002 UV, 3 cells at 2048 and none
  at 1024 (so it looked like packing margin, and a wider margin did not fix
  it). List the faces first; then weld UVs of the same vertex closer than
  0.0008.

## Bake

- **Joined-copy bake is the default** (`unir=True`). Reload the module to be
  sure you have it. → verifying.
- **Extrusion by size** (values that shipped): 1.2 mm contactor (133 mm);
  1.5 mm drone, cine camera; 2 mm lantern, clamp meter, drill; 2.5 mm
  microscope, welder, lathe; 3 mm valve, generator, robot arm, radial engine,
  pallet truck.
- **Bake target is the proxy** (`L.proxy_bake`), never the LP with replicas.
- **Glass.** `bake.material_final` rebuilds the node tree; pass
  `transmision=1.0, ior=1.5` (globe) or `1.58` (polycarbonate visor) for the
  glass set every time it is called, including on a rebake.
  `tanda.hornear_y_exportar` does not pass them — see `fictitious-brands.md`,
  step 4, for reading them back.
- **Fidelity depends on framing.** Pallet truck 0.42/255 "is favourable because
  of the framing: the part fills little of the frame". Compare props only at
  similar frame fill.
- **Over the threshold: report where, do not move it.** 5 of 16 props shipped
  above 2/255 (2.14, 2.64, 2.66, 2.80, 5.61), each with its smooth-area figure
  (0.72–0.93, and 2.50 on the finned engine) and the cause. → verifying.

- **Fidelity under 2/255 with black tears in the map.** A sheath front baked
  at 1.88/255 (pass) with black blotches along its stitch line: the low
  poly's chords cut across a moulded ramp (3.4 mm rise in 3.6 mm) and sat
  further from the high poly than the bake extrusion. Rows placed on the foot
  and the crown of the ramp: 1.44/255, no tears. Found by rendering the baked
  low poly close up; no gate measures it yet.
- **A boolean resets `material_index`.** Faces painted before cutting an
  eyelet came back all 0. Paint after the last cut.

## Stills and sheets

- **Four stills**: `01_hero`, a rear or opposite view, a front or side, and
  `04_detalle_<feature>` with `margen` −0.25 to −0.55 to crop in.
- **Orient the topology camera per prop.** Welder: the split came from the
  side without the door. `tanda.cerrar(..., hero=...)` uses the hero direction.
- **Wire thickness by size**: 0.3 mm (207 mm clamp meter), 0.5 mm typical
  handheld, 0.7–0.8 mm bench, 1.0–1.2 mm above a metre.
- **Transparent parts** go in `solo_alambre`; **a display stand** goes in
  `tambien` so both halves of the split show the same scene. The stand is not
  exported (helmet).
- **A shot into a cavity gets its own light.** The valve's bore shot ships with
  `relleno=((0.6, -0.15, 0.02), 1.2, 0.25)` in `entrega.still` (position, watts,
  size); its first version was overexposed and was redone after looking at it.
- **A view that needs the prop turned over may not be worth it.** Clamp meter:
  the base shot was dropped for a trigger-and-jaw detail.
- **GLB embeds the 4K maps**: 62 MB (valve), 91 MB (helmet). Say so.
