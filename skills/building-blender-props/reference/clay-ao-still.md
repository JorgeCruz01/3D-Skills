# The clay + AO still

Every prop ships one still of the high poly in grey clay with ambient
occlusion: `Renders/Stills/05_arcilla_ao.png`. It shows form without texture.
A camouflage, a wood grain or a brushed metal hides a flat stock; clay does
not. Three stocks that had passed every gate read as cut-out boards in it.

Approved as the standard for all props on 2026-10-06, after a batch of 23.

## What it is

| | |
|---|---|
| Subject | the HIGH poly, decals included, low poly hidden |
| Camera | the hero's: same direction, same framing (`entrega.still`) |
| Lights, backdrop | the studio's, unchanged |
| Material | one override for the whole view layer: Principled, roughness 0.62, base colour = an Ambient Occlusion node (colour grey 0.62, 16 samples) |
| AO distance | 6 % of the prop's bounding-box diagonal |
| Size | 3840×2160 PNG, 160 samples, denoised |
| Package | `Renders/Portafolio/clay.webp`, and `clayUrl` in both blocks of `asset.json` |

AO alone, unlit, comes out flat, and a white model on the white backdrop
disappears: the occlusion multiplies a lit grey material instead.

## How to make it

```python
entrega.arcilla(NOMBRE, HERO)            # HERO = the direction given to 01_hero.png
laminas.a_webp(ruta_png, os.path.join(R["renders_portafolio"], "clay.webp"))
# asset.json: a[k]["clayUrl"] = "assets/images/assets-3d/<id>/clay.webp" for k in ("es", "en")
```

One MCP call per prop (50–70 s at 4K; the first render after opening a file
can take 3 min). `arcilla` sets `view_layer.material_override`, calls `still`
and restores the override in a `finally`: the scene is left as it was. It
changes neither the model nor the textures, so it can be added to a finished
prop without rebaking.

## When

- **During the high poly**, at 1920×1080 and 48 samples
  (`entrega.arcilla(..., res=(1920, 1080), samples=48)`), before any low poly:
  if the form does not hold in clay, the prop is not ready for phase 6.
- **At delivery**, at full size, after the four stills.

## Rules

1. **Record the hero direction** where the stills are declared. Two props had
   no record; their clay still was aimed by eye and one came out from the far
   side, then down the barrel. Compare `05_arcilla_ao.png` with `01_hero.png`
   side by side before accepting it.
2. **Glass goes opaque under the override.** A face shield in clay hid the
   helmet behind it. Hide the transparent part for this still
   (`ocultar=("Visor",)`) and say so in the README.
3. **Show what the hero shows.** If the file hides the backdrop or a display
   stand for the bake, unhide them (`hide_render = False`) before the call: a
   helmet came out on the dark world instead of the studio grey.
4. **Do not retouch it.** No sharpening, no levels. It is evidence.
5. A flat form found here is a defect of the high poly: fix the model
   (`reference-likeness.md`, "Moulded bodies"), not the lighting.

## Checklist

- [ ] same side and framing as `01_hero.png`
- [ ] low poly hidden, decals visible
- [ ] backdrop and stand as in the hero; transparent parts hidden and declared
- [ ] `clay.webp` in the package, `clayUrl` in `es` and `en`
