# jorge-3d-skills

Claude Code plugin marketplace with skills for 3D prop production.

## Install

```
/plugin marketplace add JorgeCruz01/jorge-3d-skills
/plugin install blender-props@jorge-3d-skills
```

To pull later updates:

```
/plugin marketplace update jorge-3d-skills
```

## Plugins

### `blender-props`

**`verifying-blender-props`** — measurement discipline for a Blender prop
pipeline driven through MCP or `bpy` scripts. Verification gates per phase, each
returning a number against a threshold, plus `verifications.py`: 14 functions
covering manifold and dimension checks, degenerate faces, clearance between
parts (static and animated), UV density and overlap, LP-vs-HP silhouette,
backdrop coverage during a turntable, framing across an animation range,
turntable loop closure, and render cost.

Every function in it caught at least one real defect that visual inspection had
already waved through.

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
