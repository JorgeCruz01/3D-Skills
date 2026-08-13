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
| Machined parts | `shading(part)` | `sharp_edges > 0` if the part has hard edges |
| Retopo | `silhouette_hp_vs_lp(...)` | `differing_px_pct < 1` |
| UV | `uv_overlap(set)` | `overlapping_cells == 0`, `degenerate_uv_faces ≈ 0` |
| UV | `uv_density(set)` | `deviation_pct < 1` within each set |
| Bake | compare LP+normal render against HP | mean difference `< 2/255` |
| Animation | `animated_clearance(...)` | positive across the **whole** range, not just at rest |
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
