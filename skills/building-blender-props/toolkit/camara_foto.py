"""Camara ajustada a una foto en escorzo, para medir el parecido cuando no hay
ninguna vista de frente.

`parecido` compara siluetas en proyeccion ortografica y solo sirve con fotos
de perfil. Con una foto en tres cuartos se pone una camara en perspectiva que
ve el modelo como la foto ve el objeto, se renderiza la silueta al tamano de la
foto y se comparan pixel a pixel, sin reescalar ni desplazar.

La camara sale de dos cotas publicadas en dos ejes distintos (`afin`): el
vector imagen de una longitud conocida a lo largo de X y el de otra a lo largo
de Y. Con eso la proyeccion ortografica a escala queda determinada (el tercer
eje sale de que los tres son ortogonales y del mismo modulo). La focal no sale
de ahi: se ajusta mirando cuanto mas grande se ve lo cercano que lo lejano.

Limite: la camara y el modelo se ajustan contra la misma foto. Lo que valida
es que UN solido rigido explica toda la silueta a la vez, no cada cota."""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

import parecido


def afin(ax, ay, tam, ancla_px, f, ancla_mundo=(0.0, 0.0, 0.0)):
    """`ax`, `ay`: vector imagen (px, y hacia abajo) de 1 mm a lo largo de +X y de +Y del mundo. `tam` = (ancho, alto)
    de la foto. `ancla_px`: donde cae en la foto el punto `ancla_mundo` (mm). `f`: focal en pixeles."""
    a1, a2 = np.array([ax[0], ay[0]], float), np.array([ax[1], ay[1]], float)
    p, q = float(a1 @ a2), float(a1 @ a1 - a2 @ a2)
    u = math.sqrt((-q + math.sqrt(q * q + 4 * p * p)) / 2)
    v = -p / u if u > 1e-9 else -math.sqrt(-q)
    if v > 0:                                    # +Z del mundo hacia arriba en la imagen
        u, v = -u, -v
    r1, r2 = np.array([a1[0], a1[1], u]), np.array([a2[0], a2[1], v])
    s = float(np.linalg.norm(r1))
    der, abajo = r1 / s, r2 / np.linalg.norm(r2)
    fondo = np.cross(der, abajo)
    return {"der": der.tolist(), "abajo": abajo.tolist(), "fondo": fondo.tolist(), "s": s, "f": float(f), "tam": list(tam),
            "ancla_px": list(ancla_px), "ancla_mundo": list(ancla_mundo)}


def poner(c, nombre="CAM_Foto"):
    """Crea (o rehace) la camara de Blender. Unidades de mundo: metros; `c` va en milimetros."""
    old = bpy.data.objects.get(nombre)
    if old:
        d = old.data
        bpy.data.objects.remove(old)
        bpy.data.cameras.remove(d)
    cd = bpy.data.cameras.new(nombre)
    cam = bpy.data.objects.new(nombre, cd)
    bpy.context.scene.collection.objects.link(cam)
    W, H = c["tam"]
    cd.sensor_fit, cd.sensor_width = "HORIZONTAL", 36.0
    cd.lens = c["f"] * 36.0 / W
    if "R" in c:                                                # camara ya resuelta: R (mundo -> camara, filas derecha, abajo, fondo) y centro C en mm
        der, abajo, fondo = (Vector(v) for v in c["R"])
        C, D = Vector(c["C"]), Vector(c["C"]).length
    else:
        der, abajo, fondo = (Vector(c[k]) for k in ("der", "abajo", "fondo"))
        D = c["f"] / c["s"]                                     # mm
        dx, dy = (c["ancla_px"][0] - W / 2) / c["f"] * D, (c["ancla_px"][1] - H / 2) / c["f"] * D
        C = Vector(c["ancla_mundo"]) - fondo * D - der * dx - abajo * dy
    R = Matrix((der, -abajo, -fondo)).transposed()
    cam.matrix_world = Matrix.Translation(C * 0.001) @ R.to_4x4()
    cd.clip_start, cd.clip_end = 0.01, D * 0.001 * 4 + 5
    return cam


def mascara(c, ruta=None, ocultar=("Backdrop_360",), samples=4, color=False):
    """Silueta del modelo vista por la camara de la foto, al tamano de la foto. `color=True` deja ademas el render en `ruta`."""
    sc = bpy.context.scene
    cam = poner(c)
    W, H = c["tam"]
    est = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.render.film_transparent, sc.render.filepath,
           sc.cycles.samples, sc.render.image_settings.file_format, sc.render.image_settings.color_mode)
    ocultos = [(o, o.hide_render) for o in (bpy.data.objects.get(n) for n in ocultar) if o]
    ruta = ruta or os.path.join(bpy.app.tempdir, "_camara_foto.png")
    try:
        for o, _ in ocultos:
            o.hide_render = True
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
        sc.render.film_transparent = True
        sc.cycles.samples = samples
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = "PNG", "RGBA"
        sc.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
    finally:
        for o, v in ocultos:
            o.hide_render = v
        (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.render.film_transparent, sc.render.filepath,
         sc.cycles.samples) = est[:7]
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = est[7], est[8]
    return parecido.mascara_ref(ruta, "alfa")


def comparar(ref, modelo, salida=None):
    """IoU pixel a pixel de dos siluetas del MISMO tamano (la de la foto y la del modelo visto por su camara)."""
    R, M_ = ref, modelo
    inter, union = (R & M_).sum(), (R | M_).sum()
    out = {"iou": round(float(inter / union), 4), "falta_pct": round(float((R & ~M_).sum() / R.sum() * 100), 2),
           "sobra_pct": round(float((M_ & ~R).sum() / R.sum() * 100), 2)}
    if salida:
        px = np.zeros(R.shape + (4,), np.float32)
        px[..., 3] = 1.0
        px[..., :3] = 0.06
        px[R & M_, :3] = 0.55
        px[R & ~M_] = (0.95, 0.15, 0.12, 1.0)
        px[M_ & ~R] = (0.15, 0.35, 0.98, 1.0)
        im = bpy.data.images.new("_cf", R.shape[1], R.shape[0])
        im.pixels[:] = px[::-1].ravel()
        im.filepath_raw, im.file_format = salida, "PNG"
        im.save()
        bpy.data.images.remove(im)
        out["imagen"] = salida
    return out


def guardar_mascara(m, ruta):
    """Mascara booleana a PNG en gris, para superponerla a la foto fuera de Blender."""
    px = np.repeat(m[::-1, :, None].astype(np.float32), 4, 2)
    px[..., 3] = 1
    im = bpy.data.images.new("_m", m.shape[1], m.shape[0])
    im.pixels[:] = px.ravel()
    im.filepath_raw, im.file_format = ruta, "PNG"
    im.save()
    bpy.data.images.remove(im)


def resuelta(c):
    """(f, R, C) de cualquiera de los dos formatos, en numpy y milimetros."""
    if "R" in c:
        return c["f"], np.array(c["R"], float), np.array(c["C"], float)
    R = np.array([c["der"], c["abajo"], c["fondo"]], float)
    W, H = c["tam"]
    D = c["f"] / c["s"]
    C = np.array(c["ancla_mundo"], float) - R[2] * D - R[0] * (c["ancla_px"][0] - W / 2) / c["f"] * D - R[1] * (c["ancla_px"][1] - H / 2) / c["f"] * D
    return c["f"], R, C


def en_plano(c, px, eje, valor):
    """Punto de mundo (mm) que la foto ve en el pixel `px` y que esta en el plano eje = valor (eje 0, 1 o 2). Es como
    se leen cotas de una foto en escorzo: cada rasgo se supone en un plano conocido (el de simetria, una cara, la
    altura de las palas) y el pixel fija las otras dos coordenadas."""
    f, R, C = resuelta(c)
    W, H = c["tam"]
    d = R[2] + R[0] * (px[0] - W / 2) / f + R[1] * (px[1] - H / 2) / f
    t = (valor - C[eje]) / d[eje]
    return C + t * d


def proyectar(c, X):
    """Pixel de la foto donde cae el punto de mundo X (mm)."""
    f, R, C = resuelta(c)
    W, H = c["tam"]
    v = R @ (np.asarray(X, float) - C)
    return np.array([W / 2 + f * v[0] / v[2], H / 2 + f * v[1] / v[2]])
