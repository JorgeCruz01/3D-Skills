"""Estudio comun del lote: rig de luz y camaras que se escala al tamano del prop.

El rig viene de Extintor.blend, dimensionado para un objeto de 0.51 m de alto.
`encuadrar` lo reescala al prop: las posiciones y el tamano de las luces crecen
linealmente y la potencia con el cuadrado, de modo que la exposicion y la dureza
de la sombra se mantienen iguales en los 18 props.
"""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

REF_ALTO = 0.51          # alto del prop para el que se ajusto el rig original
LUCES = ("Area.001", "Area.002", "Area.003", "Area.004")
CAMARAS = ("CAM_Beauty", "CAM_Detalle", "CAM_Topo")
# Convencion del lote: el frente del prop mira a -Y. Direccion objetivo -> camara.
DIRECCIONES = {"CAM_Beauty": (0.8, -1.0, 0.42), "CAM_Detalle": (-0.9, -0.75, 0.2),
               "CAM_Topo": (0.8, -1.0, 0.42)}
# el rig del Extintor escalado solo por area queda corto en props mas anchos que altos
GANANCIA = 2.2


def _bbox(coleccion):
    """Esquinas en mundo del bounding box EVALUADO de todas las mallas."""
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.collections[coleccion].all_objects:
        if o.type not in {"MESH", "CURVE", "FONT", "SURFACE"}:
            continue
        ev = o.evaluated_get(dg)
        pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def _esquinas(lo, hi):
    return [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]


def guardar_base():
    """Registra la pose original del rig en propiedades, una sola vez."""
    for n in LUCES:
        o = bpy.data.objects[n]
        if "base_loc" not in o:
            o["base_loc"] = list(o.location)
            o["base_size"] = o.data.size
            o["base_energy"] = o.data.energy
    for n in CAMARAS:
        o = bpy.data.objects.get(n)
        if o:
            o["base_dir"] = list(Vector(DIRECCIONES[n]).normalized())


def escalar_luces(coleccion):
    bb = _bbox(coleccion)
    if bb is None:
        return {"ok": False, "evaluated": 0}
    lo, hi = bb
    dim = hi - lo
    s = max(dim) / REF_ALTO
    centro_xy = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for n in LUCES:
        o = bpy.data.objects[n]
        o.location = centro_xy + Vector(o["base_loc"]) * s
        o.data.size = o["base_size"] * s
        o.data.energy = o["base_energy"] * s * s * GANANCIA * bpy.context.scene.get("luz_" + n, 1.0)
    return {"ok": True, "escala": round(s, 4), "dim_m": [round(v, 4) for v in dim]}


def aspecto(look="AgX - Medium High Contrast", exp=-1.0, mundo=0.3, fondo=0.31, luces=None):
    """Aspecto del render de un prop, guardado en la escena (lo respeta `escalar_luces`).

    El rig da cuatro luces iguales y un mundo a 1.0: sobre un prop oscuro (cuero, laca, plastico negro) el albedo
    0.12 sale mas claro que el fondo y el material se lava. Medido en la silla vaquera: cuero #604632 en el mapa,
    canela (200, 130, 85) en la lamina. `exp` baja la exposicion, `fondo` sube el albedo del ciclorama lo mismo
    para que su gris no cambie, `mundo` quita relleno y `luces` = {nombre: factor} da clave y relleno distintos."""
    sc = bpy.context.scene
    sc.view_settings.look = look
    sc.view_settings.exposure = exp
    for n in sc.world.node_tree.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value = mundo
    m = bpy.data.materials.get("M_Fondo")
    if m and fondo:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (fondo, fondo, fondo * 1.03, 1)
    for n in LUCES:
        sc["luz_" + n] = float((luces or {}).get(n, 1.0))
    return {"look": look, "exp": exp, "mundo": mundo, "fondo": fondo, "luces": {n: sc["luz_" + n] for n in LUCES}}


def encuadrar(camara, coleccion, margen=0.12, res=None):
    """Coloca `camara` mirando al centro del bbox de `coleccion`, a la distancia
    minima en que las 8 esquinas caben con `margen` de aire. Fija la resolucion
    ella misma si se pasa `res`, porque la proyeccion depende del aspecto."""
    sc = bpy.context.scene
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
    bb = _bbox(coleccion)
    if bb is None:
        return {"ok": False, "evaluated": 0, "all_inside": None}
    lo, hi = bb
    centro = (lo + hi) / 2
    cam = bpy.data.objects[camara]
    d = Vector(cam["base_dir"]).normalized()
    esquinas = _esquinas(lo, hi)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = d.to_track_quat("Z", "Y")

    def cabe(dist):
        cam.location = centro + d * dist
        bpy.context.view_layer.update()
        for p in esquinas:
            u = world_to_camera_view(sc, cam, p)
            if not (margen <= u.x <= 1 - margen and margen <= u.y <= 1 - margen and u.z > 0):
                return False
        return True

    a, b = 0.01, 400.0
    if not cabe(b):
        return {"ok": False, "all_inside": False}
    for _ in range(48):
        m = (a + b) / 2
        if cabe(m):
            b = m
        else:
            a = m
    ok = cabe(b)
    cam.data.clip_start = max(0.001, b / 200)
    cam.data.clip_end = b * 50 + 100
    sc.camera = cam
    return {"ok": ok, "all_inside": ok, "distancia_m": round(b, 4),
            "res": [sc.render.resolution_x, sc.render.resolution_y]}


VISTAS = {
    "tres_cuartos": (0.75, -1.0, 0.45),
    "perfil": (1.0, 0.0, 0.08),
    "frente": (0.0, -1.0, 0.08),
    "trasera": (-0.6, 1.0, 0.5),
    "cenital": (0.0, -0.05, 1.0),
    "inferior": (0.5, -0.8, -0.75),
}


def vistas_previas(coleccion, carpeta, vistas=("tres_cuartos", "perfil", "frente"),
                   res=(900, 900), samples=24, prefijo="prev"):
    """Renders rapidos para JUZGAR FORMA, nunca para detectar defectos.
    Camara temporal, fondo y suelo ocultos, pelicula transparente."""
    import os
    sc = bpy.context.scene
    guardar_base()
    escalar_luces(coleccion)
    cam_d = bpy.data.cameras.new("_prev")
    cam_d.lens = 85
    cam = bpy.data.objects.new("_prev", cam_d)
    sc.collection.objects.link(cam)
    fondo = bpy.data.objects.get("Backdrop_360")
    estado = (sc.cycles.samples, sc.render.film_transparent, sc.camera,
              fondo.hide_render if fondo else None, sc.render.filepath)
    sc.cycles.samples = samples
    sc.render.film_transparent = True
    if fondo:
        fondo.hide_render = True
    salidas = []
    try:
        for v in vistas:
            cam["base_dir"] = list(Vector(VISTAS[v]).normalized())
            r = encuadrar("_prev", coleccion, 0.06, res)
            ruta = os.path.join(carpeta, "%s_%s.png" % (prefijo, v))
            sc.render.filepath = ruta
            __import__("solo_gpu").asegurar(horneado=False)      # prohibido renderizar u hornear con la CPU
            bpy.ops.render.render(write_still=True)
            salidas.append({"vista": v, "ruta": ruta, "ok": r["ok"]})
    finally:
        sc.cycles.samples, sc.render.film_transparent, sc.camera = estado[0], estado[1], estado[2]
        if fondo:
            fondo.hide_render = estado[3]
        sc.render.filepath = estado[4]
        bpy.data.objects.remove(cam)
        bpy.data.cameras.remove(cam_d)
    return salidas


def preparar(coleccion, camara="CAM_Beauty", res=(2560, 2560), margen=0.12):
    guardar_base()
    r = escalar_luces(coleccion)
    r["encuadre"] = encuadrar(camara, coleccion, margen, res)
    return r


TARJETAS = (  # (posicion en tamanos del prop desde el centro, (ancho, alto) en tamanos, fuerza)
    ((-1.1, -0.9, 0.2), (0.35, 1.6), 6.0),      # tira vertical a la izquierda delante: el filo de luz largo
    ((1.2, -0.6, 0.3), (0.5, 1.4), 4.0),        # caja a la derecha
    ((0.0, 0.2, 1.4), (1.2, 0.6), 3.0),         # techo
    ((0.3, 1.3, 0.1), (0.3, 1.4), 3.5),         # tira de contra
)


def tarjetas(coleccion, specs=TARJETAS, color=(1.0, 0.98, 0.95)):
    """Tarjetas de reflejo para metal pulido o lacado: planos emisivos que NO ve la camara ni dan luz difusa ni sombra,
    solo se reflejan. Sin ellas un laton al 0,14 de rugosidad refleja un ciclorama gris uniforme y se lee mate.
    Se recrean a la escala del prop en cada llamada (coleccion `Tarjetas`)."""
    lo, hi = _bbox(coleccion)
    c = (lo + hi) / 2
    s = max(hi - lo)
    col = bpy.data.collections.get("Tarjetas")
    if col is None:
        col = bpy.data.collections.new("Tarjetas")
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        d = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(d)
    m = bpy.data.materials.get("_Tarjeta") or bpy.data.materials.new("_Tarjeta")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    for i, (p, (w, h), f) in enumerate(specs):
        me = bpy.data.meshes.new("_tarjeta%d" % i)
        me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
        me.materials.append(m)
        o = bpy.data.objects.new("Tarjeta_%d" % i, me)
        col.objects.link(o)
        o.location = c + Vector(p) * s
        o.scale = (s, s, s)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = (c - o.location).normalized().to_track_quat("Z", "Y")
        o["fuerza"] = f
        o.visible_camera = False
        o.visible_diffuse = False
        o.visible_shadow = False
        o.visible_volume_scatter = False
        o.visible_transmission = False
    e.inputs["Strength"].default_value = 1.0
    # cada tarjeta con su fuerza: material por tarjeta
    for o in col.objects:
        mm = m.copy()
        mm.node_tree.nodes["Emission"].inputs["Strength"].default_value = o["fuerza"]
        o.data.materials[0] = mm
    return {"n": len(col.objects), "escala_m": round(s, 3)}
