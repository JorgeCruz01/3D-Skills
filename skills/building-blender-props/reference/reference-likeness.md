# Does it look like the reference? Measure it

Mesh, UV and bake gates say a prop is well made. None of them says it looks
like the thing it was supposed to be. A game controller passed every gate and
its shoulder buttons did not resemble the photo; a guitar passed and its
pickguard, traced by eye, did not hug the neck. The first was caught by the
user, not by a gate. This is the gate that was missing.

Run it on the **high poly, before the low poly exists**. A likeness problem
found after baking costs the whole bake again.

## 1. Silhouette against the reference: `parecido.medir`

Works where a reference is shot square-on: a cut-out on transparency, an
orthographic drawing, a catalogue photo on white.

```python
import parecido
r = parecido.medir(ref_png, "Model Collection", desde=(0, 0, 1), arriba=(1, 0, 0),
                   salida="Referencias/parecido_frente.png", modo="alfa")
# {'iou': 0.978, 'distintos_pct': 2.2, 'falta_pct': 1.2, 'sobra_pct': 1.0, 'proporcion_dif_pct': 1.1}
```

`desde` is the direction object -> camera, `arriba` the world direction that is
up in the photo. Both silhouettes are cropped, scaled by their larger side
(never stretched) and shifted to the best overlap. The image is the result
that matters: grey = both, **red = only the reference (the model is missing
it)**, blue = only the model (it has too much).

Read the image, not only the number:

- A thin rim of one colour all the way round is a scale artefact: something
  the reference does not show (a strap button on the far end) is inflating the
  model's bounding box. Hide it for the measurement (`ocultar=`) and say so.
- A blob is a real error. On the guitar: tuner buttons 7 mm too long and 6 mm
  too near the nut (IoU 0.956 -> 0.978 after moving them).
- Centring by bounding box is not enough, which is why the tool searches the
  shift: one protrusion on one side moved everything and the first reading
  (0.921) was mostly misalignment.

Figures seen: 0.92 misaligned, 0.956 aligned with real errors, 0.978 after
fixing them. No threshold has been set from one prop; report the number and
the image.

## 2. Side by side: `parecido.lado_a_lado`

The silhouette cannot see anything inside the outline. Put an orthographic
render of the model next to the reference, same height, same background, and
compare part by part.

```python
parecido.lado_a_lado(ref_png, "Model Collection", (0, 0, 1), (1, 0, 0), "Referencias/comparativa_frente.png")
```

What it found on a guitar whose silhouette already read 0.978:

| Seen side by side | Cause | Fix |
|---|---|---|
| pickguard a different shape | outline read by eye off a 50 px grid | trace it from the photo (below) |
| body tan-brown, reference butter-yellow | colour = texture x tint, and the wood map is brown | mix the tint over the map (72 %) instead of multiplying |
| fret dots and headstock logo missing | rebuilding the high poly empties the label collection | rebuild labels after every rebuild |
| hairline across the body top | two slabs 0.1 mm apart | stations exactly on the cut |

An overhead orthographic view of a glossy part reflects the key light straight
back: colours read paler than in the stills. Compare hue there, not value.

## 3. Trace from the photo, not by eye

Whenever a shape is a distinct colour in the reference, extract it:

```python
osc = ((rgb.max(2) < 52) & alfa).astype(np.uint8)          # the black pickguard
osc = cv2.morphologyEx(osc, cv2.MORPH_CLOSE, kernel_9)       # strings cut it into strips
contorno = cv2.approxPolyDP(max(contours, key=cv2.contourArea), 1.0, True)
```

Write a debug image with the contour drawn over the photo and look at it: a
dark reflection on a chrome plate had merged with the pickguard and had to be
clipped. The outer outline of a cut-out comes straight from its alpha channel,
row by row.

Per-row or per-column scans assume the shape is simple in that direction. A
guitar body is neither (the waist breaks columns, the cutaway breaks rows): a
column scan silently filled the waist and produced a body with straight
sides. See "Parametric skins" in `quad-topology.md`.

## 4. Oblique references

A three-quarter photo cannot be measured. Render the model from the same
angle, put the two images side by side and go through the parts one at a
time, naming for each what differs. Do this for every reference downloaded,
not only the one that was traced: the controller's top view was traced
faithfully and its front-edge view was never opened again after the first
look.

## What to report

The IoU and the difference image for each square-on reference, the
side-by-side image, and the list of differences that remain, including the
deliberate ones (no logo, different symbols) so they are not mistaken for
misses.
