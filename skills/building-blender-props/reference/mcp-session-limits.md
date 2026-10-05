# Driving one Blender through MCP: limits

Everything runs in a single Blender instance through
`mcp__blender__execute_blender_code`. These limits shaped the toolkit.

## One instance

There is one Blender and one open `.blend`. Work cannot be split between
subagents, and two props cannot be built at once. A subagent may read and write
files; only one agent talks to Blender.

`prop.crear(nombre)` refuses to switch file when the open session has unsaved
changes; `prop.guardar(nombre)` refuses to save when the open file is not that
prop's `.blend`. Keep both refusals: after an `open_mainfile` the session
points at another prop and nothing else warns you.

## Calls longer than 120 s go to the background

The MCP call returns control and Blender keeps working. The return value is
lost. Therefore:

- Long functions **write their result to disk**: `bake.hornear` →
  `Texturas/Bakes/bake_log.json`; `tanda.hornear_y_exportar` →
  `<prop>/_ultimo.json`; `reexportar` → `<root>/_reexportacion.json`.
- After a long call, read that file and the outputs it names. Do not re-send
  the call to "see what happened": a second bake starts on top of the first.
- Renders go **one per call**: `entrega.still` is one still, by design.

## The connection drops after about 5 minutes

Blender finishes; the connection does not come back with the answer. Split the
work so that no call needs more than that:

| Split | Measured |
|---|---|
| decals + bake + export · then · stills + sheets + package + close | the rebrand of 16 props ran as two calls per prop for this reason |
| one still per call | 4 stills at 3840×2160, 160 samples |
| bake in its own call | 29–78 s joined; 287–1,036 s before joining the high poly |

Check on disk between the halves (`texture_files` on `Texturas/`, existence of
the FBX), then send the second half.

Time one unit before sending a batch (`render_cost` in
verifying-blender-props).

## Open a .blend in one call, operate in the next

Opening a file and using operators in the same script fails with a stale
context (`Context has no attribute selected_objects`; `object.join` poll
fails). `reexportar` is built around it: each `paso()` exports the open file
and leaves the next one open for the following call. Same for `prop.crear`:
call it, return, then build.

## Modules persist across calls and across files

Python modules stay loaded in Blender for the whole process.

- Reload the toolkit when switching prop (`toolkit/README.md`). A welder baked
  in 823 s because the loaded `bake` predated the joined-copy default.
- Every prop has `construir_hp.py` and `construir_lp.py`. Remove the previous
  prop's folder from `sys.path` and its `construir_*` entries from
  `sys.modules`, or you rebuild the previous prop inside the new file.
- Module-level state does not survive a reload: `colada._HUELLAS`,
  `lowpoly.PLANOS`.

## The session is not the file

`bpy.data` is the open session. Save at the end of each phase
(`prop.guardar`) and check the file on disk before handing anything over
(`entrega.cerrar` runs `datablocks_on_disk` on a copy). Materials created for
later use need `use_fake_user = True` — the toolkit sets it in `M.pbr` and
`bake.material_final`.

## Operators need a viewport

`uv.desplegar` enters edit mode with `temp_override(area=VIEW_3D ...)`: Blender
must have a 3D viewport open in its window. `F.texto`, `F.unir` and
`F.mecanizar` use `bpy.ops` on the active object: do not run them while another
call is still working in the background.
