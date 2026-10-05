"""Parecido con la referencia, medido: la silueta del modelo, vista desde donde
se tomo la foto, contra la silueta de la foto.

Las puertas de malla y de bake dicen si el prop esta bien hecho; no dicen si se
parece a lo que habia que hacer. Esta lo mide en la unica vista en que hay
dato, y deja una imagen para mirarlo: gris donde coinciden, rojo donde solo
esta la referencia (al modelo le falta), azul donde solo esta el modelo (le
sobra).

Limites: compara contornos, no relieve ni color; y solo en vistas donde la
foto esta de frente (una foto en escorzo no sirve)."""
import os

import bpy
import numpy as np
from mathutils import Vector

import estudio


def mascara_ref(ruta, modo="alfa", umbral=0.5, recorte=None):
    """Silueta de la referencia. modo 'alfa': canal alfa (recortes sobre
    transparente). 'no_blanco': todo lo que no es fondo blanco (dibujos, fotos
    de catalogo). 'no_negro': fondo negro. `recorte` = (x0, y0, x1, y1) en
    fracciones de la imagen, con y desde arriba."""
    im = bpy.data.images.load(ruta, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[::-1]
    bpy.data.images.remove(im)
    if modo == "alfa":
        m = a[..., 3] > umbral
    elif modo == "no_blanco":
        m = a[..., :3].min(2) < 1.0 - umbral * 0.2
    else:
        m = a[..., :3].max(2) > umbral * 0.2
    if recorte:
        x0, y0, x1, y1 = recorte
        m = m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    return m


def mascara_modelo(coleccion, desde, arriba, res=1600, ocultar=("Backdrop_360",), ruta=None, samples=4):
    """Silueta del modelo en proyeccion ortografica. `desde`: direccion objeto ->
    camara. `arriba`: que direccion del mundo queda hacia arriba en la imagen."""
    sc = bpy.context.scene
    lo, hi = estudio._bbox(coleccion)
    c = (lo + hi) / 2
    d = Vector(desde).normalized()
    cd = bpy.data.cameras.new("_parecido")
    cd.type = "ORTHO"
    cam = bpy.data.objects.new("_parecido", cd)
    sc.collection.objects.link(cam)
    radio = (hi - lo).length / 2
    cam.location = c + d * (radio * 3 + 0.5)
    z = d
    y = Vector(arriba) - Vector(arriba).dot(z) * z
    y.normalize()
    x = y.cross(z)
    from mathutils import Matrix
    cam.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
    cd.ortho_scale = radio * 2.1
    cd.clip_end = radio * 8 + 2
    est = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.film_transparent, sc.render.filepath, sc.cycles.samples,
           sc.render.image_settings.file_format, sc.render.image_settings.color_mode)
    ocultos = [(o, o.hide_render) for o in (bpy.data.objects.get(n) for n in ocultar) if o]
    ruta = ruta or os.path.join(bpy.app.tempdir, "_parecido.png")
    try:
        for o, _ in ocultos:
            o.hide_render = True
        sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.film_transparent = True
        sc.cycles.samples = samples
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
        sc.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
    finally:
        for o, v in ocultos:
            o.hide_render = v
        sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.film_transparent, sc.render.filepath, sc.cycles.samples = est[:6]
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = est[6], est[7]
        bpy.data.objects.remove(cam)
        bpy.data.cameras.remove(cd)
    return mascara_ref(ruta, "alfa")


def _caja(m):
    f = np.where(m.any(1))[0]
    c = np.where(m.any(0))[0]
    return m[f[0]:f[-1] + 1, c[0]:c[-1] + 1]


def _escalar(m, alto, ancho):
    fi = np.minimum((np.arange(alto) * m.shape[0] / alto).astype(int), m.shape[0] - 1)
    ci = np.minimum((np.arange(ancho) * m.shape[1] / ancho).astype(int), m.shape[1] - 1)
    return m[fi][:, ci]


def comparar(ref, modelo, salida=None, lado=1400):
    """Lleva las dos siluetas a la misma escala (por la dimension mayor, sin
    deformar) y las centra por su caja. Devuelve IoU, % de pixeles distintos
    sobre el area de la referencia, y cuanto difiere la proporcion ancho/alto."""
    r, m = _caja(ref), _caja(modelo)
    k = lado / max(r.shape)
    r = _escalar(r, max(1, int(round(r.shape[0] * k))), max(1, int(round(r.shape[1] * k))))
    km = max(r.shape) / max(m.shape)
    m = _escalar(m, max(1, int(round(m.shape[0] * km))), max(1, int(round(m.shape[1] * km))))
    mg = int(0.05 * lado)
    H, W = max(r.shape[0], m.shape[0]) + 2 * mg, max(r.shape[1], m.shape[1]) + 2 * mg
    R = np.zeros((H, W), bool)
    y0, x0 = (H - r.shape[0]) // 2, (W - r.shape[1]) // 2
    R[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r
    ym, xm = (H - m.shape[0]) // 2, (W - m.shape[1]) // 2

    def poner(dy, dx):
        M2 = np.zeros((H, W), bool)
        M2[ym + dy:ym + dy + m.shape[0], xm + dx:xm + dx + m.shape[1]] = m
        return M2
    # centrar por la caja deja descolocadas dos siluetas en cuanto una tiene un saliente que la otra no (un boton
    # de correa): se busca el desplazamiento que mas las hace coincidir
    mejor, desp = -1.0, (0, 0)
    for paso, radio in ((max(2, mg // 6), mg), (1, max(2, mg // 6))):
        cy, cx = desp
        for dy in range(cy - radio, cy + radio + 1, paso):
            for dx in range(cx - radio, cx + radio + 1, paso):
                if abs(dy) > mg or abs(dx) > mg:
                    continue
                M2 = poner(dy, dx)
                v = (R & M2).sum() / (R | M2).sum()
                if v > mejor:
                    mejor, desp = v, (dy, dx)
    M_ = poner(*desp)
    inter, union = (R & M_).sum(), (R | M_).sum()
    out = {"iou": round(float(inter / union), 4), "distintos_pct": round(float((R ^ M_).sum() / R.sum() * 100), 2),
           "falta_pct": round(float((R & ~M_).sum() / R.sum() * 100), 2), "sobra_pct": round(float((M_ & ~R).sum() / R.sum() * 100), 2),
           "proporcion_ref": round(r.shape[1] / r.shape[0], 4), "proporcion_modelo": round(m.shape[1] / m.shape[0], 4)}
    out["proporcion_dif_pct"] = round((out["proporcion_modelo"] / out["proporcion_ref"] - 1) * 100, 2)
    if salida:
        px = np.zeros((H, W, 4), np.float32)
        px[..., 3] = 1.0
        px[..., :3] = 0.06
        px[R & M_, :3] = 0.55
        px[R & ~M_] = (0.95, 0.15, 0.12, 1.0)
        px[M_ & ~R] = (0.15, 0.35, 0.98, 1.0)
        im = bpy.data.images.new("_parecido", W, H)
        im.pixels[:] = px[::-1].ravel()
        im.filepath_raw, im.file_format = salida, "PNG"
        im.save()
        bpy.data.images.remove(im)
        out["imagen"] = salida
    return out


def medir(ruta_ref, coleccion, desde, arriba, salida=None, modo="alfa", recorte=None, res=1600):
    return comparar(mascara_ref(ruta_ref, modo, recorte=recorte), mascara_modelo(coleccion, desde, arriba, res), salida)


def _rgba(ruta):
    im = bpy.data.images.load(ruta, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[::-1]
    bpy.data.images.remove(im)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones((h, w, 1), np.float32)], 2)
    return a


def lado_a_lado(ruta_ref, coleccion, desde, arriba, salida, modo="alfa", alto=1500, samples=48, ocultar=("Backdrop_360",), fondo=(0.16, 0.16, 0.18),
                recorte=None):
    """Referencia a la izquierda y render ortografico del modelo a la derecha, los dos recortados a su silueta y a
    la misma altura, sobre el mismo fondo. Para mirar lo que la silueta no mide: herrajes, proporciones interiores, color."""
    tmp = os.path.join(bpy.app.tempdir, "_parecido_render.png")
    estudio.guardar_base()
    estudio.escalar_luces(coleccion)
    mm_ = mascara_modelo(coleccion, desde, arriba, alto, ocultar, ruta=tmp, samples=samples)
    A, B = _rgba(ruta_ref), _rgba(tmp)
    mr = mascara_ref(ruta_ref, modo, recorte=recorte)
    if recorte:
        h, w = A.shape[:2]
        A = A[int(recorte[1] * h):int(recorte[3] * h), int(recorte[0] * w):int(recorte[2] * w)]
    out = []
    for img, m in ((A, mr), (B, mm_)):
        f, c = np.where(m.any(1))[0], np.where(m.any(0))[0]
        img = img[f[0]:f[-1] + 1, c[0]:c[-1] + 1]
        k = alto / img.shape[0]
        fi = np.minimum((np.arange(alto) / k).astype(int), img.shape[0] - 1)
        ci = np.minimum((np.arange(int(img.shape[1] * k)) / k).astype(int), img.shape[1] - 1)
        img = img[fi][:, ci]
        al = img[..., 3:4] if modo == "alfa" or img is not A else np.ones_like(img[..., 3:4])
        rgb = img[..., :3] * al + np.array(fondo, np.float32) * (1 - al)
        out.append(rgb)
    sep = np.full((alto, 40, 3), fondo, np.float32)
    px = np.concatenate([sep, out[0], sep, out[1], sep], 1)
    px = np.concatenate([px, np.ones(px.shape[:2] + (1,), np.float32)], 2)
    im = bpy.data.images.new("_lado", px.shape[1], px.shape[0])
    im.pixels[:] = px[::-1].ravel()
    im.filepath_raw, im.file_format = salida, "PNG"
    im.save()
    bpy.data.images.remove(im)
    return {"imagen": salida, "tam": [px.shape[1], px.shape[0]]}
