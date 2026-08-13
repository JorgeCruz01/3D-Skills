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
| High poly | `dimensions(part, expected_mm)` | within declared tolerance |
| High poly | `degenerate_faces(part)` | nothing above 100:1 aspect ratio |
| Machined detail | `axis_clearance(...)` | **positive**: a hole must still be a hole after modifiers |
| Assembly | `axis_clearance` / `profile_clearance` | positive between every pair of parts that touch |
| Assembly | `pairwise_intersections(collection)` | `clean == True` **and** `unverified_parts == []` — bulk, catches crossing, full containment, and (with `margin>0`) near-misses as `mode: "near"`. `mode` is a hint, not a classification: treat `clean`/`overlaps` as the facts. A non-empty `unverified_parts` means containment was not checked for that part at all — fix its normals and re-run before trusting `clean`. Time it on a subset before the full assembly |
| Machined parts | `shading(part)` | `sharp_edges > 0` if the part has hard edges |
| Retopo | `silhouette_hp_vs_lp(...)` | `differing_px_pct < 1` |
| UV | `uv_overlap(set)` | `overlapping_cells == 0`, `degenerate_uv_faces ≈ 0` |
| UV | `uv_density(set)` | `deviation_pct < 1` within each set |
| Bake | compare LP+normal render against HP | mean difference `< 2/255` |
| Animation | `animated_clearance(...)` | positive across the **whole** range, not just at rest |
| Animation | `animated_intersections(moving, others, f0, f1)` | `clean == True` across the whole range. `cap_reached == True` means at least one ray cast hit the 64-surface parity cap; a non-empty `unverified_parts` means containment could not be checked for that part at all — neither is a clean result you can trust as-is |
| Animation | `framing_check(...)` | `all_inside == True` |
| Turntable | `turntable_loop(cam, 1, N+1)` | error `< 1e-6` and uniform step |
| Backdrop | `backdrop_coverage(...)` | `frames_with_world_AT_EDGES == none` |
| Render | `render_cost(...)` | measure and **report** before launching the batch |

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
   being silently treated as clean.

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
