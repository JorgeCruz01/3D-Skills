---
name: verifying-blender-props
description: Use when modeling, retopologizing, unwrapping, baking, texturing, rendering or animating a 3D prop in Blender through MCP or bpy scripts — before any bake, before any render batch, and before calling the work done.
---

# Verifying Blender props

## The principle

**Looking is not verifying.** A check that does not return a number against a
threshold is not a check. It is an impression.

This counts double when working through MCP or scripts, where there is no
viewport to orbit. But it holds with a GUI in front of you too: in production,
**every** defect that reached the client had already passed a visual inspection
that waved it through.

## When this applies

- Any phase of a Blender prop driven via `execute_blender_code` or `bpy`
- Before baking: bad geometry gets baked into the texture
- Before a render batch: 250 frames of a defect are 250 wasted frames
- Before calling anything finished

Does not apply to: quick blockouts, proofs of concept, throwaway exercises.

## The rule

**Every phase closes with measurements that return numbers, not with a render
you look at.**

Renders are for judging **aesthetics** — composition, light, how the material
reads. They are not for detecting defects. Measurements are.

## Verification gates by phase

Use `verifications.py` (next to this file). Every function returns a dict.

| Phase | Function | Criterion |
|---|---|---|
| High poly | `manifold(part)` | `boundary == 0`, `nonmanifold == 0`, `scale == [1,1,1]` |
| High poly | `dimensions(part, expected_mm)` | within declared tolerance, **measured against a reference distinct from the one that fixed the scale** (see "No circular verification" below) |
| High poly | `degenerate_faces(part)` | nothing above 100:1 aspect ratio |
| Shape-only module | render isolated from 3+ views + an explicit feature checklist (see "The shape gate" below) | every listed feature marked present with the image it is visible in, **plus** a final gestalt question against the reference that overrides all of the above |
| Machined detail | `axis_clearance(...)` | **positive**: a hole must still be a hole after modifiers |
| Assembly | `axis_clearance` / `profile_clearance` | positive between every pair of parts that touch |
| Assembly | `pairwise_intersections(collection)` | `clean == True` **and** `unverified_parts == []` **and** `disagreement == False` — bulk, catches crossing, full containment, and (with `margin>0`) near-misses as `mode: "near"`. `mode` is a hint, not a classification: treat `clean`/`overlaps` as the facts. A non-empty `unverified_parts` means containment was not checked for that part at all; `disagreement == True` means some probe's 3 consensus rays did not agree, so a "not contained" for that pair is not fully trusted — fix and re-run before trusting `clean`. **`open_meshes` must be `{}`**: parity is UNDEFINED on an open surface, not merely unreliable, because rays leave through the hole and change the crossing count. Measured on an avatar hand cut at the wrist (636 boundary edges): a nail comfortably outside the finger disagreed on 418 of 418 vertices — every one. Against a temp hole-filled copy, 0. Fix with a **temporary** copy plus `bmesh.ops.holes_fill`, never the original. Time it on a subset before the full assembly |
| Machined detail | through-hole ray test, **one ray per hole from each side it opens on**, plus a ray along the hole axis that must cross the whole part | every ray passes; a ray offset past the hole's half-width is blocked. Real case: six vent slots cut by boolean in a hard hat. The three on +X were holes; the three on −X came out as bars ADDED to the shell. The ray test fired from +X only and read a hit on the far wall as "passed through" — six green slots, three of them solid |
| Any | mesh bounding box (from `mesh.vertices`) against the expected envelope | within tolerance, per axis and per sign. **Measure the mesh, not the function that generated it.** Same case: dimensions were read off the generator's arrays, so the three bars — sticking out to −130 mm on a part that ends at −120.5 — were invisible to the dimension gate too. A render found them |
| Assembly | `surface_distance(a, b)` when `pairwise_intersections` returns `disagreement: True` | `vertices_behind == 0` and `min_mm` equal to the designed gap. Settles whether the disagreement is a grazing ray or a contained part, with a measurement that does not use rays |
| Machined parts | `shading(part)` | `sharp_edges > 0` if the part has hard edges |
| Fitted parts | `seating_gap(cover, base)` | `seated == True`. A part whose job is to sit ON a surface — press-on nail, decal shell, hub cap, trim panel, badge — fails in TWO directions, and every other clearance gate here only asks whether the gap is positive. **Floating is a positive gap.** Measured: a nail hovering 0.945 mm min / 1.558 mm median above the surface it was glued to passed `pairwise_intersections` clean and every positive-clearance check. The ceiling applies to the LOW percentile, not the minimum: a fitted part only contacts over part of its area. `seated is None` means inconclusive — check `contact_pct` and whether `base` was over-scoped |
| Retopo | `silhouette_hp_vs_lp(...)` | `differing_px_pct < 1`. **Subdivision is not automatically a valid HP.** Catmull-Clark contracts, and on a thin shell with a sharp tip it contracts a lot: measured 7.1–8.3 % silhouette deviation between a nail and its own Subsurf, seven times the threshold. Baking normals from that would have injected error rather than removed it. If the LP already IS the design surface — analytic, no high-frequency detail above it — say so and ship a neutral normal map instead of a fake bake |
| UV | `uv_overlap(set)` | `overlapping_cells == 0`, `degenerate_uv_faces ≈ 0`, **and** `coverage_pct >= 40` — zero overlap and 0 % density deviation say nothing about how much of the atlas is actually used; a set measured clean on both was still only 5.79 % of the atlas. Run on one representative per **UV-sharing group**, not per object and not merely per datablock. Deduping by `obj.data.name` handles linked duplicates, but it is not sufficient: parts can hold *distinct* datablocks that deliberately share the same UV space — mirrored halves pointing at one atlas, tiled modules, a left and right hand meant to use a single texture. Measured on a 10-nail set where every object had its own datablock and the mirrored pairs shared UVs by design: one hand alone reported **348** overlapping cells with `max_layers` 48, all of them a deliberate shared patch; the full ten reported **446,564** with `max_layers` 96. Nothing was wrong. Decide which parts are meant to share, run the gate on one of each, and write down why |
| UV | `uv_density(set)` | `deviation_pct < 1` within each set, on unique mesh datablocks (see row above — same linked-duplicate trap applies) |
| Bake | `bake_fidelity(col_hp, col_lp, camera, out_dir)` | `mean_diff_255 < 2`. Renders HP and baked LP from the same camera and lights |
| Bake | `texture_files(dir, expect)` right after the bake | `ok == True`: every map on disk, none 0×0, expected resolution. A bake image exists in the session before it exists as a file |
| Export | `fbx_roundtrip(path, expect_tris, …)` | `ok == True`: re-imported triangle count, UV layers, material names and dimensions match what was meant to ship |
| Save / reload | re-open the file (or `wm.read_homefile` + reload) and check that every datablock the pipeline depends on still exists | targeted datablocks present after a real save-and-reload, not just in the session that created them — Blender purges unused-user datablocks on save. Anything intentionally reserved for later (e.g. a material created empty, to be filled next session) needs `use_fake_user = True`. This is also the gate that catches work done outside a build script: hardware rebuilt from a script lost the UV a manual `smart_project` had given it, and nothing else noticed |
| File hand-off | `datablocks_on_disk(path, expect_objects=…)` before copying, linking or handing over any `.blend` | `ok == True`. **Measuring the session is not measuring the file.** Every other function here inspects `bpy.data`, which is the open session; an unsaved session and its file on disk are different objects and nothing warns you. Measured: a client `.blend` was inspected through `bpy.data` (21,966 verts, all correct) and the FILE copied — the file was 140,543 bytes and contained **no objects at all**. The mesh existed only in the unsaved session and reached disk later, after the copy was made. The working file was born empty |
| Any | before trusting a `deviation_mm` / `within_tolerance` result, confirm the expected value did not come from the same measurement used to build or scale the piece | a check against its own source data is not a check (see "No circular verification" below) |
| Assembly / animation | before any render batch, resolve every external file the scene references (HDRIs, image textures) and confirm the path exists on disk | zero missing paths. `framing_check` proves the object fits in frame, not that the scene is lit — a broken HDRI path paints the world magenta and is invisible to every geometry check in this table |
| Animation | `framing_check(...)` | `all_inside == True`. `all_inside is None` (with `no_geometry_evaluated: True`) means nothing was checked — treat it the same as a failure, never as a pass. **Run it under the exact render settings of the batch it protects** — the projection depends on the scene's resolution/aspect at call time. Measured in production: the gate ran while the scene still held a portrait plate resolution (1200×1560), passed a camera whose framing did not fit the batch's 1920×1080 landscape, and 180 frames rendered with the subject cropped. Set the batch resolution first, and confirm the first frame with a cheap test render — the render is the truth the gate approximates |
| Turntable | `turntable_loop(cam, 1, N+1)` | error `< 1e-6` and uniform step |
| Backdrop | `backdrop_coverage(...)` | `frames_with_world_AT_EDGES == none` |
| Backdrop | `degenerate_faces(backdrop)` + `shading(backdrop)` before the first still batch | nothing above 100:1 and no broken smooth normals. The backdrop is geometry too: a lathe-spun cyclorama whose floor closes into a merged center pole renders a disk of radial shading artifacts around the pole — invisible in the viewport, present in every still. `backdrop_coverage` cannot see it (it only counts world pixels); caught in production only by eyeballing a finished 256-sample batch that was about to ship. Build the floor as an n-gon disk, or gate the backdrop mesh like any part |
| Render | `render_cost(...)` | measure and **report** before launching the batch |
| Delivery renders | side-by-side against the best previously delivered prop in the repo (its hero still, its topology plate), with an explicit checklist written first: which mesh renders (HP, not the game LP), visible contact shadows, backdrop gradient/reflection, editorial layout and labels on topology plates | every item matched or consciously improved. Real case: a set shipped stills of the game LP (visible part seams, hard edges), flat shadowless lighting, and unlabeled topology dumps — while one folder away the repo held a delivered prop with studio lighting, HP renders and labeled plates. Every geometry gate was green; nothing compared the delivery against the standard the client already owned. The prior prop's .blend is also the fastest lighting reference: open it and copy the rig |

## The shape gate

A module whose entire deliverable **is its shape** — a cabin shell, a helmet,
a cowling, anything where the geometry is not a mechanism with clearances or
a UV target but literally the thing the client is buying — needs its own
gate, because every other gate in this skill can pass on a shape that is
simply wrong.

Real case: a cabin shell passed manifold, dimensions within ±10 mm, no
degenerate faces, correct shading, no self-intersections, and survived a
save-and-reload — six green checks — and it was a box. A cube cut to the
same overall dimensions would have passed every one of those six checks too.
None of them look at what the surface *does* between the corners.

The gate: render the module isolated (no assembly around it, backdrop off or
neutral) from at least three views that actually show its defining curvature
— not just front/side/top if the shape reads on a diagonal. Then walk an
**explicit list of the shape's defining features**, written down before you
render, not improvised while looking at the render. For each feature, record
present/absent and which of the rendered images shows it. Close with **one
gestalt question**: "does the silhouette read as the reference at a glance,
independent of the feature list" — and that question **overrides** every
per-feature answer above it, because a shape can tick every feature on the
list (a bump exists, a taper exists) and still read as generically wrong in
proportion or flow, the way a box with a token bump-and-taper would.

**The reference the gestalt answers to must be an image file in the repo**
(client-provided when there is a client, sourced and saved to `Referencias/`
otherwise) — never a mental picture of the object category. Real case: a
construction-tool set passed every numeric gate and its own gestalt
("reads as a shovel at a glance" — it did), and the client rejected the
delivery outright: their expected product was a different model, different
colors, different proportions. The gestalt had been answered against the
modeler's memory of "a shovel", which can only ever confirm the category,
not the design. If no reference image exists in the repo when the shape
gate runs, the gate is not runnable — collecting the image is the first
step of the gate, not an optional extra. A spec-sheet's dimensions are not
a substitute: two tools with identical published cotas can look nothing
alike.

## No circular verification

A check that measures against the same data used to build or scale the
thing being verified is not a check — it will always agree with itself.

Real case: a blueprint reference was cropped using the tip-to-tip span of its
own dimension-line arrow as the pixel-to-mm scale factor. Verifying the
resulting model's dimension against that same arrow's cropped span came back
0.000 mm of deviation. The real error, measured against an independent
dimension on the same blueprint, was 6.5 %. The zero was not a clean result;
it was the scale factor measuring itself.

The rule: whatever fixed the scale, orientation, or crop of a reference
cannot also be the thing you verify the model against. Pick a second,
independent dimension, landmark, or source for the check.

## Five measurements the eye cannot make

These have no visual equivalent. If you do not run them, you do not know.

1. **Clearance between parts.** A tube can pass 1 mm through the wall of its
   fitting and look perfect from every angle. Always measure on the **high
   poly**: the low poly tessellates coarser and misses the worst sample, so it
   can report positive clearance while the high poly intersects.
   `profile_clearance` only works for a **solid of revolution** — it takes a
   `(radius, z)` profile and measures distance to the Z axis. In a sheet-metal
   assembly (a vehicle body, a frame of ~60 modules) that returns numbers with
   no meaning; use `pairwise_intersections` instead. Its `margin` produces a
   third `mode`, `"near"`, via a real point-to-surface distance query
   (`BVHTree.find_nearest`) — **never** `BVHTree`'s own `epsilon` parameter,
   which the BVH is always built with at `0.0` regardless of `margin`: it
   was measured to have zero effect on separated geometry at any size, and
   worse, passing `margin` as epsilon was measured to break the containment
   ray cast outright (it pads the surface enough that the ray's step-off
   re-hits it, exhausting the 64-hit cap and falsely raising `cap_reached`
   on ordinary, separated parts). `margin` never reaches the containment
   check either: a fully separate pair is never reported "contained" no
   matter how large `margin` is. And the containment check itself uses
   **several probe points**
   (face centers nudged inward, plus the centroid), not the centroid alone:
   a channel section, a tube, a rim or an angled bracket has its centroid in
   the empty space it wraps around, not in its material, so a single-probe
   check misses exactly the non-convex parts a chassis is made of. Every
   probe is **self-validated** before use — kept only if it lands inside its
   OWN part's material — because "nudge inward along the face normal"
   silently nudges outward on any face whose normal got flipped (a common
   side effect of joining several sub-parts into one mesh). An un-validated
   probe like that drifts into empty space and can land inside a
   neighbouring part it never touched: measured on a real chassis, a U-clamp
   correctly wrapping a bar with real clearance — not touching it — was
   reported "contained" purely because one of its own probes had drifted
   into the air gap. When every candidate probe for a part fails
   self-validation, that part is listed in `unverified_parts` instead of
   being silently treated as clean. Every pair is also rejected first by an
   **exact bounding-box test**, expanded by `margin`: if two parts' AABBs
   don't overlap on some axis, no ray is ever cast for that pair — an AABB
   always contains its solid, so this can never hide a real defect, only
   skip pairs it is mathematically certain about. Measured in production:
   three pairs with AABB gaps from tens of centimetres to metres were
   reported "contained" before this filter existed. And the containment
   ray cast itself is a **3-direction unanimous consensus**, not one ray: a
   single ray along a fixed diagonal that grazes a cylinder tangentially
   (systematic on axles, tubes, bolts — not random) registers one hit where
   it should register zero or two, flipping parity and calling an exterior
   point interior.

2. **UV overlap.** A closed ring is topologically a torus and needs **two** cuts
   to unwrap. With only one, the unwrap collapses: zero-area faces and stacked
   layers, and no other check will reveal it.

3. **LP silhouette against HP.** Render both with `film_transparent` and compare
   the alpha channel. *Hide the backdrop first*, or alpha comes back opaque
   across the whole frame and the comparison reports 0 % for the wrong reason.

4. **Backdrop coverage during a turntable.** Set the world to magenta and count
   pixels. Magenta at the **edges** means the backdrop does not cover. Magenta in
   the **centre over the object** means reflection or transmission, which is
   correct. Looking at the image cannot tell these apart: the rim of a backlit
   cyclorama looks exactly like a hole and is not one.

5. **Feature diameter after modifiers.** A Bevel that is wide relative to the
   smallest feature eats the mouth of a hole, and subdivision shrinks it further.
   Rule: bevel width must be **less than one third of the radius of the smallest
   feature it crosses**. And even then, measure it.

## Rationalizations

| Excuse | Reality |
|---|---|
| "I already looked at several renders and it reads fine" | Your eye calibrates to the model. At hour six you see what you expect to see. |
| "That check requires setting something up instead of just looking" | Exactly. That is why it finds what looking does not. |
| "It's a simple prop, this is overkill" | None of these defects depend on complexity. |
| "I'll verify if a problem shows up" | A problem that shows up already reached the client. |
| "The client is expecting delivery in two hours" | Measurements take seconds. Re-rendering takes hours. |
| "I'll orbit it with a matcap and see it" | Through MCP there is no orbit. And with a GUI you would not see it either. |
| "The manifold count came back clean" | Perfect manifold coexists with 2000:1 slivers and closed holes. |
| "I already fixed it and it looks better" | Better is not a threshold. Measure again. |
| "It passed every check" | Only because none of the checks were looking at what the piece needed to be. |
| "It's a known false positive" | A false positive with no measured cause is a plausible diagnosis, not a diagnosis. Three times on this prop the real cause was something else, and worse. |
| "The deviation came back 0.000" | A perfect zero on a hand-taken measurement is suspicious, not reassuring. It usually means it was measured against itself. |
| "It didn't fit without reopening a closed dimension" | If a part doesn't fit where you put it, check first whether it's in the right place. A leaf spring that doesn't fit between the dual rear wheels doesn't go there — it goes under the frame rail. |
| "It's just the backdrop, not part of the prop" | The backdrop is in every delivered pixel. A cyclorama with a degenerate pole fan shipped its radial artifacts into a full still batch while every gate on the actual prop was green. |
| "I know what this object looks like" | You know what the category looks like. The client expects one specific design, and a delivery got rejected whole because the gestalt was answered from memory instead of against a reference image saved in the repo. |
| "The spec sheet is my reference" | Cotas constrain size, not shape. Two tools with identical published dimensions can look nothing alike; the gestalt needs a photo, not a table. |
| "The scene has lights, that's enough" | Lit is not delivered-quality. The repo's best prior prop defines the delivery bar; a render that never stood next to it shipped flat, shadowless and on the wrong mesh. |
| "I already measured the scene, the file is the scene" | It is not. `bpy.data` is the open session. A client file measured that way — 21,966 verts, everything correct — was 140,543 bytes on disk and held **zero objects**; the mesh was unsaved. The copy made from it was empty. Use `datablocks_on_disk` before any hand-off. |
| "The gap is positive, so it fits" | Floating is a positive gap. A press-on nail hovering 1.5 mm above the surface it is glued to passes every clearance gate in this file. A part that must SIT on something needs a ceiling as well as a floor — `seating_gap`. |
| "I'll just write the check inline, it's faster than loading the skill" | Then you will write it worse. A hand-rolled UV overlap test that rasterized each face's bounding BOX instead of the polygon reported 559,508 overlapping cells; the `uv_overlap` already in this file rasterizes barycentrically and reported 30, all of them deliberate. Twenty minutes chasing a defect that did not exist. |
| "The gate is wrong, not the mesh" | Then prove it before touching the gate. `uv_overlap` reported 18 / 150 / 270 cells at grid 1024 / 2048 / 4096; linear growth looked like cell centres landing on shared edges, so the gate's inside test was "fixed" to be strict. The counts did not move by one. Listing which faces covered the overlapping cells found the real cause in a minute: quads with a near-straight interior angle, concave in UV, overlapping their neighbours. The edit to the gate was reverted. Locate the offending faces first. |
| "The average face normal gives me the outward direction" | Only if the mesh's winding is consistent, and production meshes are not. Measured on one hand: the thumb nail's normals were inverted (coherence 0.84 pointing the wrong way) while the finger nails' normals nearly cancelled when averaged (coherence 0.038 — noise). Orientation needs a **geometric** test and a second, independent one to confirm it. |

## Red flags — stop and measure

- You are about to bake without having measured the geometry
- You are about to launch more than 10 frames without having timed one
- You are about to run `pairwise_intersections` on the full assembly
  (~60 modules is ~1,770 pairs) without having timed it on a subset first
- You are describing a defect with adjectives ("weird", "dirty", "off")
- You changed geometry after unwrapping or after baking
- Your only evidence that something works is a render you looked at
- You accepted a cause without measuring it

## The order is binding

```
geometry → UV → bake → render
```

Touching geometry invalidates everything to its right. Rebuild a mesh and its
UVs are gone; if the atlas is shared, **you drag every part of the set with it**.
Plan for that before you touch, not after.

## Diagnose before fixing

A visible defect almost never has the cause it appears to have. Measure **where**
it is before touching anything:

- Backdrop appearing to end → turned out to be the cyclorama's rim, not a hole:
  0.19 % of world visible, against what looked like half the frame.
- Part falling 626 mm too far → not Bézier overshoot, but the object's origin
  sitting at the world origin.
- Hole closing up → not subdivision, but the Bevel width.

Three iterations lost to attacking the symptom. Locate it numerically first.

## Traps verified in production

Things that survive good technical judgement:

- **`hide_viewport` at layer-collection level** makes bakes fail with "No valid
  selected objects", even though the objects look visible.
- The bake target object **must** be render-enabled. To stop it occluding
  itself, disable its ray `visible_*` flags, not its `hide_render`.
- Restoring ray visibility in bulk turns on `visible_camera` for lights, which
  then appear as white rectangles.
- `use_fill_caps` on a bevelled curve may generate no caps at all. Check
  `boundary` on the **evaluated** mesh, not the base mesh.
- A boolean on a mesh made of intersecting solids carves stray tunnels floating
  in mid-air: inside/outside parity is ambiguous.
- `image_settings.file_format = 'FFMPEG'` may be absent from the enum on a
  freshly created scene. An external `ffmpeg` also gives you `yuv420p` and CRF
  control.
- A GPU without RT cores adds throughput under CUDA and drags under OptiX.
  Measure both.
- `collection.objects` returns only DIRECT children. Any check that iterates
  a parent collection expecting it to reach subcollections silently checks
  zero objects — and if the check's pass condition is a trivial inequality
  over sentinel values (`min >= threshold` with `min` still at its `+1e9`
  starting value), zero objects reads as a pass. Use `collection.all_objects`,
  and make the function itself refuse to report success when it evaluated
  nothing.
- PIL/Pillow is not part of Blender's bundled Python, and a `blender.exe`
  installed from the Microsoft Store cannot `pip install` into it — `from
  PIL import Image` inside a verification function makes that function
  uninvocable in a normal user session, not just slower. Read rendered
  pixels via `bpy.data.images.load()` + `Image.pixels.foreach_get()` into
  numpy instead; Blender already has the result in memory.
- **The axis signs a PCA/SVD returns are arbitrary, per component.** Building
  a local frame from `numpy.linalg.svd` gives correct axis DIRECTIONS and
  meaningless orientations: on one hand's five nails the third axis needed
  flipping on three of them, and on the mirrored hand on a different two.
  Every axis of a derived frame needs its own geometric test — and confirm
  the test with a second, independent one. Here: "a nail's cross-section is
  a dome, the centre sits higher than the edges", cross-checked against "a
  point 3 mm along the outward normal must be outside the hand". They agreed
  on all ten; the face-normal method they replaced did not.
- A parametric surface's radius is **not** scale-invariant, its depth ratio
  is. Widening a circular-arc cross-section while holding the radius fixed
  opens the arc angle instead of scaling the shape: half-width 4.77 → 5.32 mm
  at R = 5.6 took a measured 46° arc to 72° and rolled a nail into a
  half-tube. Parameterise by `r = h/a = tan(θ/2)` and derive
  `R = a(1+r²)/2r`.
- Bending a grid's boundary by **displacing** its vertices folds the mesh as
  soon as the displacement exceeds the row spacing — 1.6 mm of cuticle curve
  against a 0.594 mm first row put row 0's edge past row 1. Reparameterise
  per column instead (`x = x₀(i) + (total − x₀(i))·σ(j)`), which is monotone
  in `j` by construction and cannot fold. Verify by measuring the minimum
  step per column.
- After `Solidify`, vertex `k` is the original surface and `k + n_original`
  its offset copy, so `normalize(V[k] − V[k+n])` is the EXACT outward normal
  — free, and immune to the winding problems that make face normals
  unreliable. Deriving that direction from the solid's centroid instead put
  every bead and spike **inside** the part on a curved surface: 92 of 156
  vertices on one.
- Offsetting a surface that carries relief folds it wherever the relief's
  radius of curvature is smaller than the offset. A 2.5 mm inward solidify
  over a 3 mm raised crest with a 4 mm blend left 145 sliver faces up to
  1249:1 on the inner wall — and they showed up as failures of the boolean
  that ran afterwards, which was not the cause. Build the inner wall from
  the smooth base surface, not from the detailed outer one.
- Normals taken with `numpy.gradient` over the INDICES of a mapped grid are
  wrong wherever the mapping creases. On a square grid mapped to a disc they
  came out nearly tangent at the four corners: the wall thickness was pushed
  sideways and six rim faces collapsed to 0.3 mm² where they should measure
  17. Differentiate the surface function in its own parameters instead.
- A quad with one interior angle near 180° is a triangle with a spare vertex.
  It passes `manifold` and `degenerate_faces`, then unwraps concave and
  overlaps its neighbours in UV. Split it through the flat vertex.
- An `Ambient Occlusion` shader node costs its sample count on every shading
  sample. At 16 samples in every material a 1200² frame took 128 s; at 4,
  6 s for a larger frame. The same node made a 4096² five-pass bake take 22
  minutes with Blender unresponsive. Bake that mask to a texture once.
- Writing `hide_render` (or any property that tags the depsgraph) while
  iterating `collection.all_objects` can hand back `None` mid-loop:
  `'NoneType' object has no attribute 'hide_render'`. Iterate
  `list(collection.all_objects)`.
- Boolean cuts land micrometres from existing vertices and leave n-gons with
  one 0.015 mm edge — 178:1 aspect, and degenerate triangles once anything
  triangulates them. A global merge-by-distance is not the fix: on the same
  mesh the legitimate tip had 0.024 mm edges and would have collapsed. Merge
  only within a radius of the cut.
