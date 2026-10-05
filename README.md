# 3D-Skills

Claude Code plugin marketplace with skills for 3D prop production.

## Install

```
/plugin marketplace add JorgeCruz01/3D-Skills
/plugin install blender-props@jorge-3d-skills
```

The repo is `3D-Skills`; the marketplace it declares is named `jorge-3d-skills`.
The two do not have to match — you add it by repo path and install from it by
marketplace name.

To pull later updates:

```
/plugin marketplace update jorge-3d-skills
```

## Plugins

### `blender-props`

**`verifying-blender-props`** — measurement discipline for a Blender prop
pipeline driven through MCP or `bpy` scripts. Verification gates per phase, each
returning a number against a threshold, plus `verifications.py`: 28 functions
covering manifold and dimension checks, degenerate faces, clearance and
seating between parts (static and animated), signed distance to a surface,
leak test of cavities, high-poly fingerprint, decal visibility,
UV density and overlap, LP-vs-HP silhouette, bake fidelity, texture files on
disk, FBX round-trip, datablocks on disk, backdrop coverage during a
turntable, framing across an animation range, turntable loop closure, render
cost, occlusion-map statistics and self-intersection of simulated cloth.

Every function in it caught at least one real defect that visual inspection had
already waved through.

**`building-blender-props`** — the pipeline that produced sixteen game-ready
props in Blender 5.2 through MCP: a prop is three parametric Python builders
(dimensions and solids, high poly, low poly) and a folder of measured evidence.
Phase order from reference photos to README, with the decision rules each
phase taught and the prop and number behind each one. Ships:

- `toolkit/` — 18 modules: parametric solids, cast-then-machine high poly,
  boolean low poly with replicas, seam-driven unwrap, joined-copy bake to
  BaseColor / Normal / ORM, FBX + GLB export, studio framing, stills,
  split / wireframe / UV / map sheets, CC0 PBR download. It calls
  `verifications.py` from the skill above.
- `reference/` — the toolkit API, tracing outlines from reference photos,
  fictitious brands and how to rebrand a finished prop, the limits of driving
  one Blender over MCP, and build lessons by phase.

The toolkit needs a studio template `.blend` (lights, three cameras, backdrop,
two collections) that is not in this repo; `toolkit/README.md` lists what it
must contain.

**`building-blender-soft-goods`** — what changes when the prop is fabric,
webbing or padding. The fabric is one closed skin inflated by the cloth solver;
straps, zippers and piping are traced onto the simulated skin instead of being
placed by coordinates. Simulation settings with their measured results, three
projection modes for sewn-on parts, the assembly gate for parts that cross on
purpose, and low poly and UV for a mesh with no hard edges. Measured on one
prop, a 29-litre backpack; it says what it has not been tried on. The code is
`toolkit/tela.py` in the skill above.

The skills split the work: the two `building` skills say what to make and
which function to call, `verifying` says whether it passed.

## Contributing

The skill grows from production failures. When a defect reaches a deliverable
render, that means no gate caught it — which is a gap in the skill, not bad
luck. The fix is:

1. Measure where the defect actually is, before fixing anything.
2. Write that measurement as a function in `verifications.py`, with a docstring
   explaining which real case it uncovered and why the eye misses it.
3. Add the row to the gate table in `SKILL.md`, with its threshold.
4. If the failure was discipline rather than knowledge, add the excuse to the
   rationalizations table, in the exact words you told yourself.

Do not add what the model already knows. Baseline testing with subagents showed
it already has the Blender 5.x API, the boolean → bevel → subsurf order, and the
bake traps. What is always missing is measuring.
