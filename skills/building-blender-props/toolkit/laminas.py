"""Laminas de entrega: wireframe, split render/wireframe, hoja UV y tira de mapas.

Cada funcion fija ella misma la camara, la resolucion y lo que se ve, y restaura
el estado al salir. Las imagenes se componen con numpy; no hay PIL en Blender.
"""
import os

import bmesh
import bpy
import numpy as np


def _leer(ruta, crudo=False):
    """`crudo`: devuelve los valores del fichero sin linealizar (para mapas de
    datos y para copiar una imagen tal cual a otra lamina)."""
    img = bpy.data.images.load(ruta, check_existing=False)
    if crudo:
        img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)


def _escribir(px, ruta):
    h, w = px.shape[:2]
    img = bpy.data.images.new("_lamina", w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px, dtype=np.float32).ravel())
    img.filepath_raw = ruta
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return {"ruta": ruta, "ok": os.path.exists(ruta) and os.path.getsize(ruta) > 0, "res": [w, h]}


def _reducir(px, lado):
    """Reduccion por promedio de bloques hasta ~`lado` px de ancho."""
    f = max(1, px.shape[1] // lado)
    h, w = (px.shape[0] // f) * f, (px.shape[1] // f) * f
    return px[:h, :w].reshape(h // f, f, w // f, f, 4).mean((1, 3))


def wireframe(objetos, camara, salida, res=(2560, 2560), samples=64, grosor=0.0009, ocultar=(),
              solo_alambre=(), tambien=()):
    """Render de la LP en arcilla con su malla dibujada encima (modificador
    Wireframe sobre copias temporales).

    `solo_alambre`: objetos de los que se dibuja solo la malla, sin superficie
    (un visor transparente: en arcilla opaca taparia lo que tiene detras).
    `tambien`: objetos que salen en arcilla sin malla (soporte de exhibicion),
    para que la escena sea la misma que en el render con el que se compara."""
    sc = bpy.context.scene
    arcilla = bpy.data.materials.get("M_Topo_Arcilla") or bpy.data.materials.new("M_Topo_Arcilla")
    arcilla.use_nodes = True
    b = arcilla.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.62, 0.64, 0.66, 1)
    b.inputs["Roughness"].default_value = 0.6
    tinta = bpy.data.materials.get("M_Topo_Tinta") or bpy.data.materials.new("M_Topo_Tinta")
    tinta.use_nodes = True
    nt = tinta.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (0.01, 0.02, 0.04, 1)
    nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    obs = [bpy.data.objects[n] for n in objetos]
    estado = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath,
              {x.name: x.hide_render for x in bpy.data.objects})
    visibles = set(objetos) | {x.name for x in bpy.data.objects if x.type in {"LIGHT", "CAMERA"}}
    visibles |= {"Backdrop_360"} | set(tambien)
    temporales, mats = [], {}
    try:
        for x in list(bpy.data.objects):
            x.hide_render = x.name not in visibles or x.name in ocultar or x.name in solo_alambre
        for n in tambien:
            ob = bpy.data.objects[n]
            mats[n] = [s.material for s in ob.material_slots]
            for s in ob.material_slots:
                s.material = arcilla
        for ob in obs:
            mats[ob.name] = [s.material for s in ob.material_slots]
            for s in ob.material_slots:
                s.material = arcilla
            c = ob.copy()
            c.data = ob.data.copy()
            c.name = ob.name + "_WIRE"
            sc.collection.objects.link(c)
            c.data.materials.clear()
            c.data.materials.append(tinta)
            m = c.modifiers.new("w", "WIREFRAME")
            m.thickness = grosor
            m.use_replace = True
            m.use_even_offset = False
            c.hide_render = False
            temporales.append(c)
        sc.camera = bpy.data.objects[camara]
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.cycles.samples = samples
        sc.render.filepath = salida
        bpy.ops.render.render(write_still=True)
    finally:
        for c in temporales:
            d = c.data
            bpy.data.objects.remove(c)
            bpy.data.meshes.remove(d)
        for ob in obs + [bpy.data.objects[n] for n in tambien]:
            for s, m in zip(ob.material_slots, mats[ob.name]):
                s.material = m
        sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath = estado[:5]
        for n, h in estado[5].items():
            if n in bpy.data.objects:
                bpy.data.objects[n].hide_render = h
    return {"ruta": salida, "ok": os.path.exists(salida), "res": list(res)}


def par_split(objetos_lp, camara, carpeta, res=(3840, 2160), samples=160, grosor=0.0005,
              solo_alambre=(), tambien=(), ocultar_en_render=()):
    """Renderiza las DOS pasadas del split con la misma camara, sin tocarla entre
    una y otra, y las compone. Es la unica forma de garantizar la misma
    perspectiva: el primer split del casco se compuso con dos camaras, una con
    shift_x = -0.07 heredado y otra sin el, y las mitades no casaban.

    Devuelve `misma_camara`: la posicion, rotacion, focal y shift de la camara
    leidos antes de la primera pasada y despues de la segunda deben ser iguales."""
    sc = bpy.context.scene
    cam = bpy.data.objects[camara]
    firma = (tuple(cam.matrix_world.translation), tuple(cam.matrix_world.to_euler()), cam.data.lens,
             cam.data.shift_x, cam.data.shift_y)
    estado = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples,
              sc.render.filepath, {o.name: o.hide_render for o in bpy.data.objects})
    r_render = os.path.join(carpeta, "split_render.png")
    r_wire = os.path.join(carpeta, "wireframe.png")
    try:
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.cycles.samples = samples
        for n in set(objetos_lp) | set(ocultar_en_render):
            bpy.data.objects[n].hide_render = True
        sc.render.filepath = r_render
        bpy.ops.render.render(write_still=True)
    finally:
        sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath = estado[:5]
        for n, h in estado[5].items():
            if n in bpy.data.objects:
                bpy.data.objects[n].hide_render = h
    wireframe(objetos_lp, camara, r_wire, res=res, samples=64, grosor=grosor,
              solo_alambre=solo_alambre, tambien=tambien)
    firma2 = (tuple(cam.matrix_world.translation), tuple(cam.matrix_world.to_euler()), cam.data.lens,
              cam.data.shift_x, cam.data.shift_y)
    comp = split(r_render, r_wire, os.path.join(carpeta, "split.png"))
    comp["misma_camara"] = firma == firma2
    return comp


def split(ruta_render, ruta_wire, salida, grosor_linea=3):
    """Compone render | wireframe partidos por una diagonal. Ambas imagenes deben
    venir de la misma camara y resolucion (usar `par_split`)."""
    a, b = _leer(ruta_render, crudo=True), _leer(ruta_wire, crudo=True)
    if a.shape != b.shape:
        return {"ok": False, "error": "resoluciones distintas", "a": a.shape[:2], "b": b.shape[:2]}
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    # diagonal de abajo-izquierda (40 %) a arriba-derecha (60 %)
    d = xx - (0.40 * w + 0.20 * w * yy / h)
    out = np.where((d < 0)[..., None], a, b)
    out[np.abs(d) < grosor_linea] = (1, 1, 1, 1)
    return _escribir(out, salida)


def hoja_uv(objetos, salida, res=2048, fondo=(0.06, 0.07, 0.09), linea=(0.85, 0.9, 1.0)):
    """Dibuja las aristas UV de cada objeto. Varios objetos = una hoja por objeto,
    una al lado de la otra (cada set ocupa su propio 0-1)."""
    hojas = []
    for n in objetos:
        px = np.empty((res, res, 4), dtype=np.float32)
        px[..., :3] = fondo
        px[..., 3] = 1
        bm = bmesh.new()
        bm.from_mesh(bpy.data.objects[n].data)
        uv = bm.loops.layers.uv.active
        segs = set()
        for f in bm.faces:
            ls = [l[uv].uv for l in f.loops]
            for i in range(len(ls)):
                a, b = ls[i], ls[(i + 1) % len(ls)]
                k = (round(a.x, 5), round(a.y, 5), round(b.x, 5), round(b.y, 5))
                segs.add(k if k[:2] <= k[2:] else k[2:] + k[:2])
        bm.free()
        for ax, ay, bx, by in segs:
            m = int(max(abs(bx - ax), abs(by - ay)) * res) + 2
            t = np.linspace(0, 1, m)
            x = np.clip(((ax + (bx - ax) * t) * (res - 1)).astype(int), 0, res - 1)
            y = np.clip(((ay + (by - ay) * t) * (res - 1)).astype(int), 0, res - 1)
            px[y, x, :3] = linea
        px[[0, -1], :, :3] = 0.35
        px[:, [0, -1], :3] = 0.35
        hojas.append(px)
    return _escribir(np.concatenate(hojas, 1), salida)


def tira_mapas(rutas, salida, lado=1024):
    """Tira horizontal con los mapas dados (BaseColor | Normal | ORM ...)."""
    partes = [_reducir(_leer(r, crudo=True), lado) for r in rutas]
    h = min(p.shape[0] for p in partes)
    out = np.concatenate([p[:h] for p in partes], 1)
    out[..., 3] = 1
    return _escribir(out, salida)


def a_webp(png, webp, calidad=88):
    """Convierte con ffmpeg (debe estar en PATH)."""
    import subprocess
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", png, "-c:v", "libwebp",
                        "-quality", str(calidad), webp], capture_output=True, text=True)
    return {"ruta": webp, "ok": r.returncode == 0 and os.path.exists(webp), "error": r.stderr.strip()[:200]}
