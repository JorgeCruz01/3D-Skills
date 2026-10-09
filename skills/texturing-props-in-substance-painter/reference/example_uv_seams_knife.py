"""Low poly del cuchillo de combate con funda, toda en quads y sin booleanos.

Cada pieza sale del MISMO constructor que su high poly (`construir_cuchillo`, `lp=True`), con menos estaciones:

- Hoja: las filas pasan por el lomo, la linea del contrafilo, la linea del bisel y el filo. El vaceo y el bisel
  secundario van al mapa de normales.
- Puno: 24 lados, con las cinco ranuras en la malla (cambian la silueta); las juntas de arandela, al normal.
- Guarda, pomo, dorso con su presilla, vira, frente y correa: los mismos lofts.
- Costura, remaches, letras, estampado, ojal y ranuras de la correa no tienen malla: van a los mapas. La correa
  cruza el colgador donde en el high poly pasa por sus ranuras.

Las piezas no se sueldan entre si: son cascaras cerradas en un solo objeto y un material. Se colocan con la pose
que guardo el high poly (`pose.json`), no se vuelven a posar."""
import math

import bpy
import numpy as np
from mathutils import Vector

import construir_cuchillo as CC
import formas as F
import quads as Q

COL = "LP Collection"
NOMBRE = "Cuchillo_Combate_LP"
SET = "Cuchillo"
MM = F.MM


def _vaciar():
    col = bpy.data.collections[COL]
    for o in list(col.all_objects):
        d = o.data
        bpy.data.objects.remove(o)
        if d and d.users == 0:
            bpy.data.meshes.remove(d)


PIEZAS = ("Hoja", "Guarda", "Puno", "Pomo", "Funda_Dorso", "Funda_Vira", "Funda_Frente", "Correa")


def construir():
    """Cada pieza se cuadra por separado y lleva en sus caras el atributo entero `pieza` (indice en PIEZAS): asi el
    despliegue UV puede dar a cada una las costuras que le tocan despues de unirlas en un objeto."""
    _vaciar()
    Pk = CC.piezas_cuchillo(COL, lp=True)
    CC.colocar(list(Pk.values()), CC.pose("cuchillo"))
    Pf = CC.piezas_funda(COL, lp=True)
    CC.colocar(list(Pf.values()), CC.pose("funda"))
    piezas = list(Pk.values()) + list(Pf.values())
    por_pieza, sin = {}, []
    for o in piezas:
        base = o.name[:-3]
        Q.ensamblar(o.name, [o], aspecto=40.0, ocultas=False)
        sin.append(o["sin_resolver"])
        at = o.data.attributes.new("pieza", "INT", "FACE")
        at.data.foreach_set("value", [PIEZAS.index(base)] * len(o.data.polygons))
        por_pieza[base] = len(o.data.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    for o in piezas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = piezas[0]
    bpy.ops.object.join()
    lp = piezas[0]
    lp.name = lp.data.name = NOMBRE
    lp["sin_resolver"] = str(sin)
    m = bpy.data.materials.get("LP_" + SET) or bpy.data.materials.new("LP_" + SET)
    m.use_nodes = True
    m.use_fake_user = True
    lp.data.materials.clear()
    lp.data.materials.append(m)
    for p in lp.data.polygons:
        p.material_index = 0
    F.sombrear(lp, 50)
    lp.data.calc_loop_triangles()
    hp = [o for o in bpy.data.collections["Model Collection"].objects if o.type == "MESH"]
    return {"tris": len(lp.data.loop_triangles), "censo": Q.censo(lp), "sin_resolver": lp["sin_resolver"], "caras_por_pieza": por_pieza,
            "desvio": Q.desvio(lp, hp)}


LOSAS = ("Hoja", "Guarda", "Funda_Vira", "Funda_Frente")       # dos caras anchas y un canto
TUBOS = ("Puno", "Pomo")                                       # una piel alrededor de un eje y dos tapas
CINTAS = ("Funda_Dorso", "Correa")                             # banda doblada: cara de fuera, de dentro y dos cantos
TIRA = 0.13                                                    # largo maximo de una tira de canto, en metros


def _ejes(pts):
    """Ejes principales de una nube (de mayor a menor extension) y su centro."""
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c, full_matrices=False)
    return vt, c


def _costuras_por_pieza(bm):
    """Indices de las aristas que son costura, con una regla por tipo de pieza en vez de un umbral de angulo:

    - losa: costura donde una cara ancha (normal a lo largo del eje fino de la pieza) se encuentra con el canto, y en
      las esquinas vivas del canto. Dos islas grandes por pieza y el canto en tiras.
    - tubo: costura alrededor de cada tapa y UNA linea a lo largo, por debajo (la que apoya en el suelo).
    - cinta: costura entre cada cara ancha y sus cantos, en los testeros, y donde la banda se da la vuelta (la normal
      cambia de mirar arriba a mirar abajo): el doblez del colgador y los dos de la correa.
    """
    capa = bm.faces.layers.int["pieza"]
    S = set()
    for k, nombre in enumerate(PIEZAS):
        caras = [f for f in bm.faces if f[capa] == k]
        vs = {v for f in caras for v in f.verts}
        ej, c = _ejes(np.array([v.co for v in vs]))
        largo, fino = Vector(ej[0]), Vector(ej[2])
        aristas = {e for f in caras for e in f.edges}
        cc0 = Vector(c)

        def tramo(f):
            """En que tramo de TIRA m cae la cara, a lo largo de la pieza: los cantos se cortan ahi. Una tira de canto
            entera (el del dorso mide 420 mm) es la isla mas larga del atlas y fija la escala de todas las demas."""
            return math.floor((f.calc_center_median() - cc0).dot(largo) / TIRA + 0.5)
        if nombre in LOSAS:
            ancha = {f: abs(f.normal.dot(fino)) > 0.5 for f in caras}
            for e in aristas:
                a, b = e.link_faces
                if ancha[a] != ancha[b] or (not ancha[a] and (a.normal.angle(b.normal) > math.radians(50) or tramo(a) != tramo(b))):
                    S.add(e.index)
        elif nombre in TUBOS:
            # el pomo es una seta: con 0.85 la cara de golpeo y el cuello quedaban en la misma isla que el canto y se
            # desplegaba hecha un ocho. 0.6 separa las dos caras que miran a lo largo del eje.
            tapa = {f: abs(f.normal.dot(largo)) > (0.6 if nombre == "Pomo" else 0.85) for f in caras}
            abajo = Vector((0, 0, -1))
            abajo = (abajo - largo * abajo.dot(largo)).normalized()
            lado = abajo.cross(largo)
            cc = Vector(c)

            def ang(v):
                d = v.co - cc
                return math.atan2(d.dot(lado), d.dot(abajo))
            # la columna de vertices mas cercana a "abajo": no tiene por que caer justo en 0 grados (en el pomo no
            # caia, se quedaba sin costura a lo largo y la piel se desplegaba hecha un ocho)
            a0 = min((ang(v) for f in caras if not tapa[f] for v in f.verts), key=abs)
            for e in aristas:
                a, b = e.link_faces
                if tapa[a] != tapa[b]:
                    S.add(e.index)
                elif not tapa[a] and all(abs(ang(v) - a0) < math.radians(1.5) for v in e.verts):
                    S.add(e.index)
        else:
            ancho = Vector((0, 1, 0)) if nombre == "Funda_Dorso" else Vector((1, 0, 0))     # la banda corre en X / en Y
            canto = {f: abs(f.normal.dot(ancho)) > 0.6 for f in caras}
            for e in aristas:
                a, b = e.link_faces
                if canto[a] != canto[b] or (canto[a] and tramo(a) != tramo(b)):
                    S.add(e.index)
                elif a.normal.angle(b.normal) > math.radians(60):
                    S.add(e.index)
                elif not canto[a] and (a.normal.z > 0) != (b.normal.z > 0) and min(abs(a.normal.z), abs(b.normal.z)) < 0.5:
                    S.add(e.index)
    return S


def desplegar(margen=0.0022):
    import bmesh
    import uv
    ob = bpy.data.objects[NOMBRE]
    for e in ob.data.edges:
        e.use_seam = False
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    S = _costuras_por_pieza(bm)
    bm.free()
    # angulo 179: ninguna costura por angulo; solo las propias y las que anade la red de seguridad a las islas que se
    # pisan (las 7 caras del broche). Con el umbral de 50 grados y el troceo de tiras salian 128 islas; asi, 71.
    info = uv.desplegar([NOMBRE], margen=margen, angulo_grados=179, vista=Vector((0.2, -0.75, 1.0)).normalized(),
                        extra=lambda e: e.index in S)
    info["costuras_propias"] = len(S)
    info["ocultas"] = encoger_ocultas()
    info["uv_soldadas"] = soldar_uv()
    return info


def encoger_ocultas(factor=0.55, alcance=0.009, fraccion=0.7, margen=0.0022):
    """Las islas que no se ven (caras pegadas a otra pieza o que miran al hueco de la funda: la vira, el interior
    del dorso y del frente, el interior de la presilla) se reducen a `factor` y se vuelve a empaquetar: el atlas
    que liberan sube la densidad de lo que si se ve. Una isla es oculta si mas de `fraccion` de su area lanza un
    rayo por su normal que da en la propia malla a menos de `alcance`."""
    import bmesh
    import uv
    from mathutils.bvhtree import BVHTree
    ob = bpy.data.objects[NOMBRE]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    arbol = BVHTree.FromBMesh(bm)
    capa = bm.loops.layers.uv.active
    n, area_oc = 0, 0.0
    for isla in uv._islas(bm):
        tot = oc = 0.0
        for f in isla:
            a = f.calc_area()
            tot += a
            if arbol.ray_cast(f.calc_center_median() + f.normal * 5e-5, f.normal, alcance)[0] is not None:
                oc += a
        if tot and oc / tot > fraccion:
            ls = [l for f in isla for l in f.loops]
            c = sum((l[capa].uv for l in ls), Vector((0.0, 0.0))) / len(ls)
            for l in ls:
                l[capa].uv = c + (l[capa].uv - c) * factor
            n += 1
            area_oc += tot
    bm.to_mesh(ob.data)
    bm.free()
    area = next(a for a in bpy.context.window.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(area=area, region=region, active_object=ob, object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(rotate=True, margin=margen, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")
    return {"islas": n, "area_cm2": round(area_oc * 1e4, 1), "factor": factor}


def soldar_uv(tol=0.0008):
    """Une las UV de un mismo vertice que quedaron a menos de `tol`: una costura que no llega a cerrar su isla deja
    los dos lados separados media celda y solapados (dos caras del canto de la hoja, 0.0002 de UV: 3 celdas a 2048)."""
    me = bpy.data.objects[NOMBRE].data
    uvs = me.uv_layers.active.data
    por_vertice = {}
    for l in me.loops:
        por_vertice.setdefault(l.vertex_index, []).append(l.index)
    n = 0
    for ls in por_vertice.values():
        hechos = set()
        for a in ls:
            if a in hechos:
                continue
            grupo = [b for b in ls if b not in hechos and (uvs[a].uv - uvs[b].uv).length < tol]
            hechos.update(grupo)
            if len(grupo) > 1 and any((uvs[a].uv - uvs[b].uv).length > 0 for b in grupo):
                m = sum((uvs[b].uv for b in grupo), uvs[a].uv * 0.0) / len(grupo)
                for b in grupo:
                    uvs[b].uv = m
                n += 1
    me.update()
    return n
