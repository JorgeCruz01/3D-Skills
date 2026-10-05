# Fictitious brands, and how to rebrand a finished prop

## Rules

1. **Every prop carries an invented brand, and each prop its own.** One brand
   across a batch reads as repetition.
2. **Search each candidate on the web together with its product category before
   it touches a mesh** ("AMPVEK clamp meter", "LUMBREK lantern"). Discard a name
   that matches or resembles a brand in the same sector.
3. **Check model designations the same way.** Three had to change after the
   brands were already clean: a cine camera "H-16" → "K-16", a contactor and
   relay "NC1/NR2" → "EK1/ET2", a generator "GE 5000" → "VK 5000".
4. **Write "MARCA FICTICIA" on the prop itself**, as a decal next to the brand,
   and repeat it in the README ("Marca **LUMBREK, ficticia**, rotulada en el
   tapón de llenado").
5. **Tell the user what the check was.** A web search is not a trademark-registry
   search. Say so when reporting the names.
6. Colours too: where the shape follows a manufacturer's data sheet, the colour
   scheme is the prop's own (a clamp meter in teal, graphite and orange, "para
   no reproducir la identidad visual de ese fabricante"). No logos or
   engravings from reference photos.

## The case

All sixteen props were first labelled "NORTEK". It is a real company name
(Nortek Control, Nortek Air Solutions). Removing it meant, for every prop: new
decals, a full rebake, re-export, four new stills, new sheets and a new
portfolio package. The low poly and its UVs survived because the brand lived
only in decals — except on the drill, where it was moulded into the housing and
the whole high poly had to be rebuilt.

Candidates rejected by the search, for resemblance to a brand in the same
sector: KASKUR (KASK), KEROVAL (KEROVI), HIDVEK (Hidtek), ZENDRAL (ZenaDrone).

Names that passed and shipped: AERVOK, LUMEQA, HARVEK, FERDUX, VOLKAM, DRUVAK,
SOLDIK, ELKVON, AMPVEK, TREVAQ, BRUNDEK, LUMBREK, VALDRUX, KINMARQ, PALZUK,
CINVARO. They are taken — invent new ones. Six or seven letters fit where a
label goes.

## Building so that a rebrand is cheap

- Brand, model and "MARCA FICTICIA" are **flat text decals** (`F.texto(...,
  relieve=0.0, ...)`) in the `Rotulos` collection, created by one function
  `_rotulos(col)` in `construir_hp.py`. Changing the brand is then: delete the
  collection's objects, call `_rotulos` again, rebake.
- Brand as cast or moulded relief (`textos=` of `colada.colar`) is part of the
  skin. Use relief for norm markings ("DN50", "CAT III 600V"), not for the
  brand, unless the prop needs it and the name is final.
- Keep the brand string in ONE place in the builder; the docstring, `Specs.md`,
  `README.md` and `asset.json` repeat it and must be replaced together.

## Rebrand procedure

The production script (`remarcar.py`) is not in the toolkit: it carried the
batch's own tables (brand per prop, sets, bake extrusion, still list, wire
thickness, sheet direction). The procedure it ran, per prop:

1. **Text.** Replace the old name, upper case and capitalised, in the prop's
   `*.py`, `*.md`, `Referencias/Specs.md` and `Renders/Portafolio/asset.json`.
2. **Open** the prop (`prop.crear(nombre)`) in one MCP call. Purge the previous
   prop's `construir_*` modules and path first (`toolkit/README.md`).
3. **Decals**, in the next call: delete every object in `Rotulos`, call
   `construir_hp._rotulos(...)`. If the brand is moulded, rebuild the high poly
   (`construir_hp.construir()`).
4. **Read the glass.** Before clearing anything, record `Transmission Weight`
   and `IOR` of every `LP_<set>` material. `bake.material_final` rebuilds the
   node tree and does not know a lantern globe (transmission 1.0, IOR 1.5) or a
   visor (1.0, 1.58) is glass.
5. **Clean the LP materials** to a bare Principled BSDF, and remove every image
   named `BK_*` or `TX_*` from the session — otherwise the next material reads
   the previous bake's pixels.
6. **Bake** on the same low poly: `lowpoly.proxy_bake` → `bake.hornear(hp +
   decals, proxy, {"LP_"+s: s}, texturas, res=4096, extrusion=<the prop's>,
   margen=6, samples=8, samples_ao=24)` → `lowpoly.quitar_proxy` in a `finally`.
7. `puertas.texturas_en_disco`, then `bake.material_final("LP_"+s, rutas,
   **vidrio[s])`, then `entrega.exportar_y_verificar`, then save.
8. **Stills** with the same file names and directions as before, one per call;
   then `entrega.laminas_tecnicas`, `entrega.paquete_portafolio`,
   `entrega.cerrar`.
9. Write the result to a JSON in the prop folder and open the next prop.

Steps 3–7 and step 8 are **two separate MCP calls** (`p1` / `p2` in the
original): together they exceed the ~5 minutes the connection survives. See
`mcp-session-limits.md`.

```python
def vidrio(sets):          # step 4
    out = {}
    for s in sets:
        b = next((n for n in bpy.data.materials["LP_" + s].node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        tw = b.inputs["Transmission Weight"].default_value if b else 0.0
        out[s] = dict(transmision=tw, ior=b.inputs["IOR"].default_value) if tw > 0 else {}
    return out
```

Keep, per prop, the parameters a rebake needs — sets, bake extrusion, the list
of stills `(file, direction, options)`, wire thickness, sheet direction — in the
prop's own builder or README. In production they lived in the rebrand script
and nowhere else.
