"""Bake HP -> LP a un juego de mapas por material de la low poly.

Un set = un material de la LP. Cada material recibe BaseColor, Normal (16 bit,
OpenGL) y ORM (R = AO, G = Roughness, B = Metallic), mas los intermedios en
`Bakes/`. BaseColor, Roughness y Metallic se hornean por EMISION, recableando
temporalmente cada material del HP: el pase DIFFUSE devuelve negro en los
metales y no existe pase de Metallic.
"""
import os
import time

import bpy
import numpy as np

CANALES = {"BaseColor": ("Base Color", True), "Roughness": ("Roughness", False), "Metallic": ("Metallic", False)}


def _imagen(nombre, res, flotante=False, color=False):
    img = bpy.data.images.get(nombre)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(nombre, res, res, alpha=False, float_buffer=flotante)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def _nodo_destino(mat, img):
    nt = mat.node_tree
    n = nt.nodes.get("_BAKE") or nt.nodes.new("ShaderNodeTexImage")
    n.name = "_BAKE"
    n.image = img
    for x in nt.nodes:
        x.select = False
    n.select = True
    nt.nodes.active = n
    return n


def _a_emision(mat, canal):
    """Recablea `mat` para emitir el valor de la entrada `canal` del Principled.
    Devuelve una funcion que deshace el cambio."""
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not out or not bsdf:
        return lambda: None
    previo = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
    em = nt.nodes.new("ShaderNodeEmission")
    ent = bsdf.inputs[canal]
    if ent.links:
        nt.links.new(ent.links[0].from_socket, em.inputs["Color"])
    else:
        v = ent.default_value
        em.inputs["Color"].default_value = tuple(v) if hasattr(v, "__len__") else (v, v, v, 1)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

    def deshacer():
        if previo:
            nt.links.new(previo, out.inputs["Surface"])
        nt.nodes.remove(em)
    return deshacer


def _a_emision_rm(mat):
    """Como `_a_emision`, pero emite Roughness en R y Metallic en G a la vez:
    un pase en lugar de dos. Cada pase a 4096 cuesta ~3 min de proyeccion en CPU."""
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not out or not bsdf:
        return lambda: None
    previo = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
    em = nt.nodes.new("ShaderNodeEmission")
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for destino, canal in (("Red", "Roughness"), ("Green", "Metallic")):
        ent = bsdf.inputs[canal]
        if ent.links:
            nt.links.new(ent.links[0].from_socket, comb.inputs[destino])
        else:
            comb.inputs[destino].default_value = ent.default_value
    comb.inputs["Blue"].default_value = 0.0
    nt.links.new(comb.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

    def deshacer():
        if previo:
            nt.links.new(previo, out.inputs["Surface"])
        nt.nodes.remove(em)
        nt.nodes.remove(comb)
    return deshacer


def _pixeles(img):
    a = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _guardar(img, ruta):
    """PNG de 8 bits con los valores del buffer tal cual, sin transformacion de vista."""
    img.filepath_raw = ruta
    img.file_format = "PNG"
    img.save()
    return ruta


def hornear(hp, lp, sets, destino, res=4096, extrusion=0.004, max_ray=0.0, margen=16,
            samples=16, samples_ao=64, unir=True, solo_ao=False):
    """hp: nombres de los objetos del high poly. lp: nombre del objeto LP (activo).
    sets: {nombre_material_LP: nombre_set}. Devuelve rutas y tiempos por set.

    `solo_ao`: hornea unicamente la oclusion y recompone el ORM con el mapa de
    rugosidad y metalico que ya esta en Bakes/. No toca Normal ni BaseColor."""
    sc = bpy.context.scene
    lp_ob = bpy.data.objects[lp]
    hp_obs = [bpy.data.objects[n] for n in hp]
    if not lp_ob.data.uv_layers:
        return {"ok": False, "error": "la LP no tiene UV"}
    temporal = None
    if unir and len(hp_obs) > 1:
        # Copia unida del high poly, solo para hornear. Con muchos objetos de origen
        # el bake se dispara (contactor: 69 objetos, 1 036 s; farol: 10 objetos y
        # casi las mismas caras, 287 s). Medido en el microscopio: 23 objetos y 1.7 M
        # de caras, unidos, 52 s en total con fidelidad 0.98/255; el durometro, con
        # 34 objetos sin unir y 1.6 M de caras, 958 s. Los originales no se tocan.
        copias = []
        for o in hp_obs:
            c = o.copy()
            c.data = o.data.copy()
            sc.collection.objects.link(c)
            copias.append(c)
        bpy.ops.object.select_all(action="DESELECT")
        for c in copias:
            c.hide_set(False)
            c.select_set(True)
        bpy.context.view_layer.objects.active = copias[0]
        with bpy.context.temp_override(active_object=copias[0], object=copias[0], selected_objects=copias,
                                       selected_editable_objects=copias):
            bpy.ops.object.join()
        temporal = copias[0]
        temporal.name = "_HP_unido_bake"
        ocultos = {o.name: o.hide_render for o in hp_obs}
        for o in hp_obs:
            o.hide_render = True
        hp_originales, hp_obs = hp_obs, [temporal]
    bakes = os.path.join(destino, "Bakes")
    os.makedirs(bakes, exist_ok=True)
    estado = (sc.render.engine, sc.cycles.samples, sc.cycles.use_denoising,
              {o.name: o.hide_render for o in hp_obs + [lp_ob]})
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = False
    # cada pase tardaba ~3 min con 8 o con 24 muestras: el coste es fijo, preparar
    # 1.6 M de caras del HP cinco veces. Con datos persistentes se prepara una.
    persistente = sc.render.use_persistent_data
    sc.render.use_persistent_data = True
    for o in hp_obs + [lp_ob]:
        o.hide_render = False
        o.hide_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    for o in hp_obs:
        o.select_set(True)
    lp_ob.select_set(True)
    bpy.context.view_layer.objects.active = lp_ob
    bk = sc.render.bake
    bk.use_selected_to_active = True
    bk.cage_extrusion = extrusion
    bk.max_ray_distance = max_ray
    bk.margin = margen
    bk.use_clear = True
    mats_lp = {s.material.name: s.material for s in lp_ob.material_slots if s.material}
    mats_hp = {s.material.name: s.material for o in hp_obs for s in o.material_slots if s.material}
    # el nodo de oclusion de cada material se evalua en cada muestra de cada pase:
    # con 4 muestras, el bake del casco tardo 22 minutos. Durante el horneado basta
    # 1: las muestras del propio pase ya promedian el ruido.
    nodos_ao = [(n, n.samples, n.only_local) for m in mats_hp.values() if m.node_tree
                for n in m.node_tree.nodes if n.type == "AMBIENT_OCCLUSION"]
    for n, _, _ in nodos_ao:
        n.samples = 1
        # only_local: el nodo solo cuenta la propia pieza. Sin esto ve a la LP
        # destino aunque tenga la visibilidad a rayos apagada (el nodo ignora esos
        # flags) y hornea una linea de suciedad en cada arista de la LP. El contacto
        # ENTRE piezas lo recoge el pase AO, que si respeta los flags.
        n.only_local = True
    # la LP destino no debe ocluir: esta a decimas de milimetro del high poly y el
    # nodo de oclusion (y el pase AO) la toman por una pieza vecina. Medido en la
    # valvula: lineas de "suciedad" en cada arista de la LP y fidelidad de 5.29/255.
    # Se apaga su visibilidad a rayos, no su hide_render: debe seguir renderizable.
    flags = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission",
             "visible_volume_scatter", "visible_shadow")
    rayos = {f: getattr(lp_ob, f) for f in flags}
    for f in flags:
        setattr(lp_ob, f, False)
    # Nada mas debe verse durante el horneado. El pase AO cuenta TODO lo renderizable: con el
    # ciclorama y el suelo del estudio presentes, una cara despejada salia a 0.2-0.5 en vez de ~1
    # (medido en los 30 sets del primer lote: mediana 0.21-0.54). No lo delato la fidelidad
    # porque el material de la LP no usaba la oclusion.
    propios = set(o.name for o in hp_obs) | {lp_ob.name}
    ajenos = [o for o in sc.objects if o.name not in propios and not o.hide_render
              and o.type in ("MESH", "CURVE", "SURFACE", "FONT", "META")]
    for o in ajenos:
        o.hide_render = True
    tiempos, imgs = {}, {}

    def pase(etiqueta, tipo, flotante, color, n_samples, antes=None, lado=None, **kw):
        t = time.time()
        for mn, sn in sets.items():
            img = _imagen("BK_%s_%s" % (sn, etiqueta), lado or res, flotante, color)
            imgs[(sn, etiqueta)] = img
            _nodo_destino(mats_lp[mn], img)
        deshacer = [antes(m) for m in mats_hp.values()] if antes else []
        sc.cycles.samples = n_samples
        try:
            bpy.ops.object.bake(type=tipo, **kw)
        finally:
            for d in deshacer:
                d()
        tiempos[etiqueta] = round(time.time() - t, 1)

    # cuatro pases, no cinco: rugosidad y metalico van juntos. La oclusion, de baja
    # frecuencia, se hornea a media resolucion y se amplia.
    if not solo_ao:
        pase("Normal", "NORMAL", True, False, samples, normal_space="TANGENT")
    pase("AO", "AO", False, False, samples_ao, lado=res // 2)
    if not solo_ao:
        pase("BaseColor", "EMIT", False, True, samples, antes=lambda m: _a_emision(m, "Base Color"))
        pase("RM", "EMIT", False, False, samples, antes=_a_emision_rm)
    else:
        for sn in sets.values():
            ruta_rm = os.path.join(bakes, "TX_%s_RM.png" % sn)
            # sin RM intermedio (los primeros props no lo guardaban), se toma del ORM ya entregado
            previo = bpy.data.images.load(ruta_rm if os.path.exists(ruta_rm) else os.path.join(destino, "TX_%s_ORM.png" % sn),
                                          check_existing=False)
            previo.colorspace_settings.name = "Non-Color"
            previo["desde_orm"] = not os.path.exists(ruta_rm)
            imgs[(sn, "RM")] = previo

    salida = {}
    for mn, sn in sets.items():
        r = {}
        for etiqueta in (("AO",) if solo_ao else ("Normal", "AO", "BaseColor", "RM")):
            img = imgs[(sn, etiqueta)]
            final = etiqueta in ("Normal", "BaseColor")
            ruta = os.path.join(destino if final else bakes, "TX_%s_%s.png" % (sn, etiqueta))
            if etiqueta == "Normal":
                s = sc.render.image_settings
                prev = (s.file_format, s.color_mode, s.color_depth)
                s.file_format, s.color_mode, s.color_depth = "PNG", "RGB", "16"
                img.save_render(ruta, scene=sc)
                s.file_format, s.color_mode, s.color_depth = prev
            else:
                _guardar(img, ruta)
            r[etiqueta] = ruta
        rm = _pixeles(imgs[(sn, "RM")])
        ro, me = (rm[..., 1], rm[..., 2]) if imgs[(sn, "RM")].get("desde_orm") else (rm[..., 0], rm[..., 1])
        ao = _pixeles(imgs[(sn, "AO")])[..., 0]
        f = res // ao.shape[0]
        if f > 1:
            ao = np.repeat(np.repeat(ao, f, axis=0), f, axis=1)
        orm = _imagen("BK_%s_ORM" % sn, res, False, False)
        px = np.stack([ao, ro, me, np.ones_like(ao)], -1).astype(np.float32)
        orm.pixels.foreach_set(px.ravel())
        r["ORM"] = _guardar(orm, os.path.join(destino, "TX_%s_ORM.png" % sn))
        salida[sn] = r
        mats_lp[mn].node_tree.nodes.remove(mats_lp[mn].node_tree.nodes["_BAKE"])
    for n, s, loc in nodos_ao:
        n.samples = s
        n.only_local = loc
    for f, v in rayos.items():
        setattr(lp_ob, f, v)
    for o in ajenos:
        o.hide_render = False
    sc.render.use_persistent_data = persistente
    sc.render.engine, sc.cycles.samples, sc.cycles.use_denoising = estado[0], estado[1], estado[2]
    for n, h in estado[3].items():
        bpy.data.objects[n].hide_render = h
    if temporal is not None:
        d = temporal.data
        bpy.data.objects.remove(temporal)
        bpy.data.meshes.remove(d)
        for n, h in ocultos.items():
            bpy.data.objects[n].hide_render = h
    for clave in list(imgs):
        img = imgs[clave]
        if img.name in bpy.data.images:
            bpy.data.images.remove(img)      # las BK_ en memoria no deben usarse despues: se leen los ficheros
    resultado = {"ok": True, "sets": salida, "tiempos_s": tiempos, "res": res, "samples": samples,
                 "samples_ao": samples_ao, "dispositivo": sc.cycles.device}
    # el bake dura mas que el limite de una llamada MCP y su resultado se pierde:
    # se deja tambien en disco para leerlo despues
    import json
    with open(os.path.join(bakes, "bake_log.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=1)
    return resultado


def material_final(nombre, rutas, transmision=0.0, ior=1.45, alpha=1.0, ao=0.0):
    """Material de entrega de la LP: BaseColor + ORM + Normal sobre la UV.

    `ao` (0-1): cuanto oscurece el color el canal de oclusion del ORM. El Principled no
    tiene entrada de oclusion y un motor de juego si la aplica; sin ella, el detalle que
    sobresale horneado (cincha sobre tela) pierde su sombra de contacto y la LP se ve
    lavada. Solo para renders: el glTF se exporta con el material sin esta mezcla."""
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (200, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])

    def tex(clave, color, y):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(rutas[clave], check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        t.location = (-500, y)
        return t

    tcol = tex("BaseColor", True, 300)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.location = (-200, 0)
    nt.links.new(tex("ORM", False, 0).outputs["Color"], sep.inputs["Color"])
    if ao > 0:
        mz = nt.nodes.new("ShaderNodeMix")
        mz.data_type = "RGBA"
        mz.blend_type = "MULTIPLY"
        mz.location = (-50, 300)
        mz.inputs["Factor"].default_value = ao
        nt.links.new(tcol.outputs["Color"], mz.inputs["A"])
        nt.links.new(sep.outputs["Red"], mz.inputs["B"])
        nt.links.new(mz.outputs["Result"], b.inputs["Base Color"])
    else:
        nt.links.new(tcol.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (-200, -300)
    nt.links.new(tex("Normal", False, -300).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if transmision > 0:
        b.inputs["Transmission Weight"].default_value = transmision
        b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    return mat
