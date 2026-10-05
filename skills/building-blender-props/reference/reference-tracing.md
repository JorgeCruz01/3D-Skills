# Reference photos and tracing

For any object a viewer recognises, the outline comes from a photograph, not
from dimensions and not from memory. Measured case: a revolver built from class
figures (overall length, barrel, cylinder, cartridge) passed every gate and was
rejected three times — grip, trigger and hammer "not realistic", cylinder "too
small". The fifth version, traced from one profile photo, is the one that
stands. A cordless drill built from its data-sheet envelope read as a heat gun.

Props shipped without a photo say so in their README ("Sin referencia
fotográfica"), and their proportions are declared as estimated.

## 1. Collect, before writing the builder

Into `<prop>/Referencias/`:

| File | Content |
|---|---|
| `ref_<what>.jpg` | 2–3 photos. One clean **profile** (the one to trace), one of the opposite side, one detail |
| `ficha_<prop>.pdf` + `ref_ficha_p<N>.png` | manufacturer data sheet and its pages as images (`toolkit/pdf_a_referencia.py`, system Python) |
| `Fuentes.md` | one row per image: file, original title/URL, download date, **what was taken from it** |
| `Specs.md` | dimensions table with source and type (`publicada` / `norma` / `estimada`), what fixes the scale, what verifies it, the shape-feature list |

`Fuentes.md` also states the limit of use, in one sentence: the photos are read
for proportions and part breakdown; the prop reproduces no brand, logo, engraving
or corporate colour scheme. See `fictitious-brands.md`.

Downloading: Wikimedia Commons returned HTTP 429 to anonymous automated
downloads (a helmet shipped without its assembly photo because of it) and
answered once the request carried an identifying `User-Agent`. Product pages
disappear: two lathe pages returned 404 and that prop has no reference sheet.
Save the file the day you find it.

Note **which side** each photo shows. The revolver was built mirrored — latch
and crane on the right, side-plate screws on the left — and only the comparison
with a left-side photo exposed it.

## 2. Put a millimetre grid on the profile photo

1. Pick two points whose real distance is known and that lie in the picture
   plane. The revolver used the barrel (152.4 mm) and the overall length
   (305 mm): 2.85 px/mm.
2. Choose the origin and axes the builder will use (revolver: bore axis is
   z = 0, front face of the cylinder is y = 0) and mark them.
3. Draw grid lines every 5 or 10 mm, labelled, and save the result next to the
   original (`ref_<what>_rejilla.png`).

The script that drew the grid for the revolver was not archived. This is a
sketch with the toolkit's own image helpers (no PIL in Blender); **written for
this document, not run in production**:

```python
import numpy as np, laminas
px = laminas._leer(r".../Referencias/ref_586.jpg", crudo=True)      # (h, w, 4), row 0 = bottom
PX_MM, X0, Y0 = 2.85, 412, 655                                      # scale and origin, in pixels
h, w = px.shape[:2]
for mm in range(-400, 401, 5):
    fuerte = mm % 50 == 0
    for eje, n, o in ((1, w, X0), (0, h, Y0)):
        p = int(round(o + mm * PX_MM))
        if 0 <= p < n:
            sl = (slice(None), p) if eje == 1 else (p, slice(None))
            px[sl][..., :3] = (1, 0.2, 0.2) if fuerte else px[sl][..., :3] * 0.6 + 0.4
laminas._escribir(px, r".../Referencias/ref_586_rejilla.png")
```

Then **look at the gridded image** (Read tool) and read coordinates off it.

## 3. Read outlines as point lists

Walk each outline once, in one direction, reading a point wherever the curve
changes: 12–50 points per outline. Readings are by eye, ±1 mm — say so in
`Fuentes.md`. Store them in the builder exactly as read, with the suffix
`_FOTO`, and a comment naming the features in walking order:

```python
# silueta del armazon ... en sentido horario desde el frente del puente: puente, caida tras el alza,
# joroba, nudillo, lomo, culata, frente de la empunadura, guardamonte y frente del armazon
SILUETA_FOTO = [(-18, 14.5), (20, 14.5), (50, 14.5), (56.5, 13.5), (59, 8), ...]      # (y, z) in mm, 52 points
SILUETA_VIVOS = (0, len(SILUETA_FOTO) - 1)                                             # corners that stay sharp
HUECO_FOTO   = [...]      # trigger-guard opening
CACHAS_FOTO  = [...]      # grip panels
PICADO_FOTO  = [...]      # checkering panel
```

`Revolver_Accion_Simple/construir_revolver.py` holds seven such lists
(`SILUETA`, `HUECO`, `CACHAS`, `PICADO`, `MARTILLO`, `CRESTA`, `GATILLO`).

Turn a list into geometry with `F.spline(points, n, vivos=...)` →
`F.prisma(..., por_normal=True)`; never extrude the raw polygon — a dozen
straight segments read as facets.

Keep photo coordinates and model coordinates apart. Where the model must
differ from the photo, map with one function instead of editing the list:

```python
def _f(y):
    """Cota y de la foto -> modelo."""      # the photo's cylinder is 47 mm at scale, the model's 42.9
    if y <= 0: return y
    if y <= Y_TAMBOR_FOTO: return y * Y_ESCUDO / Y_TAMBOR_FOTO
    return y - (Y_TAMBOR_FOTO - Y_ESCUDO) + 5.4 * (y - Y_TAMBOR_FOTO) / (Y_TALON_FOTO - Y_TAMBOR_FOTO)
```

That remap is a declared deviation in the README ("what was traced behind the
cylinder moved 4 mm forward; the offset is spread to the heel to keep the
overall length").

## 4. Fix the scale with one dimension, check with another

The dimension that set the px/mm factor cannot verify the model (see
verifying-blender-props, "No circular verification": 0.000 mm against itself,
6.5 % against an independent one).

Revolver: barrel and overall length fixed the scale. Independent checks,
measured on the mesh: cartridge length 40.40 mm against 40.4 (SAAMI), rim
11.18 against 11.2, top chamber coaxial with the bore (x = 0.000, z = 0.000),
0.185 mm minimum clearance between cartridge and cylinder with 0 vertices
inside. Overall length came out 304.51 against 305.

A traced dimension with no outside figure is reported as such: "height
160.5 mm comes from the tracing; it has no reference value".

## 5. Compare before baking

Render the high poly from the photo's side (`estudio.vistas_previas`, view
`perfil`), put it next to the photo, and walk the feature list from `Specs.md`.
Each rebake cost 6–17 minutes before the joined-copy bake and still invalidates
stills and sheets. Auditing the first render against the reference corrected:
a microscope arm 235 mm wide narrowed to 180; a drill's block trigger, smooth
rubber and unchamfered battery; a pallet truck's gussets standing out like fins.

What a photo settled that numbers could not (revolver): how much of the frame
window the cylinder fills (39.6 → 43.0 mm), that the stocks stand proud of the
frame (7.4 mm per side at mid height), that the hammer sits at top-strap height.
