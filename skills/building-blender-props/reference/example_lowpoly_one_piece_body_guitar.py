"""Low poly de la guitarra, toda en quads y sin booleanos.

- Cuerpo y pala: `piel.losa`, las mismas losas del high poly con menos
  secciones. El cuerpo son dos (cuerpo y cuerno) que se tocan en una recta.
- Mastil: el mismo loft, con 19 secciones de 16 puntos.
- Golpeador: prisma con las tapas en rejilla. Herrajes: las piezas del high
  poly a baja resolucion. Cuerdas: barridos de seccion cuadrada.

Las piezas se cruzan y las caras enterradas se borran. Un objeto, dos
materiales (dos sets): el cuerpo, y el mastil con los herrajes."""
import bpy

import construir_guitarra as CG
import formas as F
import quads as Q

COL = "LP Collection"
NOMBRE = "Guitarra_Electrica_LP"
MM = F.MM


def _vaciar():
    col = bpy.data.collections[COL]
    for o in list(col.all_objects):
        d = o.data
        bpy.data.objects.remove(o)
        if d and d.users == 0:
            bpy.data.meshes.remove(d)


PARTES = (NOMBRE + "_cuerpo", NOMBRE + "_mastil")        # un objeto por set hasta desplegar; `juntar` los une


def _material(n):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n)
    m.use_nodes = True
    m.use_fake_user = True
    return m


QUADS_CUERPO, QUADS_GOLPEADOR = 12000, 2400


def _remallar(nombre, hp, quads, vivos, info, grosor_x=1.0):
    """Copia aligerada del high poly remallada en quads (QuadriFlow) y pegada a el.
    `grosor_x`: una placa de 2 mm no se puede remallar con quads de 5 (sale con el canto desgarrado): se engorda en
    Z ese factor alrededor de su plano medio, se remalla y se devuelve a su grosor."""
    import bmesh
    import tela as T
    from mathutils import Matrix, Vector
    src = bpy.data.objects[hp]
    o = T.diezmar(nombre, src, 120000, COL)
    if grosor_x != 1.0:
        zs = [v.co.z for v in o.data.vertices]
        zm = (min(zs) + max(zs)) / 2
        M = Matrix.Translation(Vector((0, 0, zm))) @ Matrix.Diagonal((1, 1, grosor_x, 1)) @ Matrix.Translation(Vector((0, 0, -zm)))
        o.data.transform(M)
    r = Q.retopo(o, quads, vivos=vivos, escala=10.0)
    if grosor_x != 1.0:
        o.data.transform(M.inverted())
    a = Q.ajustar(o, [src])
    # QuadriFlow deja lazos ondulados donde no siguen una arista; una placa fina no se relaja: suavizar la aplasta
    for _ in range(0 if vivos else 3):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.to_mesh(o.data)
        bm.free()
        a = Q.ajustar(o, [src])
    info[nombre] = {"censo": {k: r[k] for k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}, "ajuste": a, "desvio": Q.desvio(o, [src])}
    return o


def _cuerpo_lp(info, nombre="Cuerpo_LP"):
    """El cuerpo, de una pieza y con lazos limpios en el canto: prisma de canto VIVO del contorno limpio, remallado
    en quads conservando esas dos aristas (QuadriFlow alinea un lazo con cada una), y pegado despues al high poly: el
    lazo del canto cae en el centro del redondeo y lo aproxima con un chaflan UNIFORME en todo el perimetro; el resto
    del redondeo va al mapa de normales. Remallando el high poly ya redondeado, el canto de 3.2 mm caia dentro de
    un quad de 5 a una altura distinta cada vez y la silueta salia ondulada. Un bisel de Blender sobre ese lazo deja
    triangulos y n-gonos en cada polo."""
    import bmesh
    import numpy as np
    C = F.remuestrear(np.array(CG._D["cuerpo_limpio"], float)[:, ::-1], 900, cerrada=True)
    o = F.prisma(nombre, C * MM, (0, 0, 0), "Z", CG.GROSOR * MM, COL)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()
    CG.a_mundo(o)
    r = Q.retopo(o, QUADS_CUERPO, vivos=30, escala=10.0)
    a = Q.ajustar(o, ["Cuerpo"])
    c = Q.censo(o)
    info[nombre] = {"censo": {k: c[k] for k in ("caras", "tris", "ngonos", "polos", "aristas_no_estancas")}, "quadriflow": r["quadriflow"], "ajuste": a,
                    "desvio": Q.desvio(o, ["Cuerpo"])}
    return o


def construir(q=0.5, remallar=True):
    """q = 0.3 y `CG.DENSO` apagado dan la low poly de 2026-10-06 (13 476 triangulos)."""
    _vaciar()
    CG.DENSO = True
    F.COSTURA_BARRIDO = True            # cada cuerda lleva su costura: una isla por tramo, no una por cara
    P = CG.piezas(q, COL)
    CG.DENSO = False
    F.COSTURA_BARRIDO = False
    cuerpo = {k: P.pop(k) for k in [k for k in P if k.startswith("Cuerpo_")]}
    info = {}
    if remallar:
        # el cuerpo y el golpeador, de UNA pieza: remallados en quads sobre el high poly. En losas, cada corte se
        # veia como una linea en el canto del cuerpo y en la cara del golpeador
        for o in list(cuerpo.values()) + [P.pop(k) for k in [k for k in P if k.startswith("Golpeador_")]]:
            d = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(d)
        cuerpo = {"Cuerpo": _cuerpo_lp(info)}
        P["Golpeador"] = _remallar("Golpeador_LP", "Golpeador", QUADS_GOLPEADOR, 30, info, grosor_x=12.0)
    out = {}
    for nombre, piezas, mat in ((PARTES[0], cuerpo, "LP_Cuerpo"), (PARTES[1], P, "LP_Mastil")):
        lp = Q.ensamblar(nombre, list(piezas.values()))
        lp.data.materials.clear()
        lp.data.materials.append(_material(mat))
        F.sombrear(lp, 50)
        lp.data.calc_loop_triangles()
        out[nombre] = {"tris": len(lp.data.loop_triangles), "censo": Q.censo(lp), "sin_resolver": lp["sin_resolver"], "ocultas": list(lp["ocultas"])}
    out["remallado"] = info
    return out


def juntar():
    lp = F.unir(NOMBRE, [bpy.data.objects[n] for n in PARTES])
    F.sombrear(lp, 50)
    hp = [o for o in bpy.data.collections["Model Collection"].all_objects if o.type == "MESH"]
    lp.data.calc_loop_triangles()
    return {"tris": len(lp.data.loop_triangles), "censo": Q.censo(lp), "desvio": Q.desvio(lp, hp), "materiales": [m.name for m in lp.data.materials]}


def _cara_plana(e):
    """Costura entre una cara plana (tapa o dorso de una losa) y su canto redondeado: la tapa se despliega
    entera y sin estirar; pegada al canto, el despliegue la partia en una docena de trozos."""
    if len(e.link_faces) != 2:
        return False
    a, b = e.link_faces
    return (abs(a.normal.z) > 0.7) != (abs(b.normal.z) > 0.7)      # 0.7: el lazo del canto separa tapa (0.98) de pared (0.2)


def _fina(f):
    """Cara de cuerda: menos de 1.3 mm de ancho."""
    return f.calc_area() / max(e.calc_length() for e in f.edges) < 1.3 * MM


def uv_cuerpo(nombre, hueco=3.5):
    """UV del cuerpo a mano, sin deformacion y con densidad exacta: la tapa y el dorso son proyecciones planas (el
    dorso, en espejo) puestas lado a lado, y el canto es (longitud de arco a lo largo del contorno, altura) en tres
    tiras rectas debajo. El despliegue automatico las dejaba giradas y deformadas y el atlas se quedaba en el 44 %.
    Devuelve px/mm a 4096 y la ocupacion."""
    import bmesh
    import numpy as np
    ob = bpy.data.objects[nombre]
    C = np.array(CG._D["cuerpo_limpio"], float)                       # (y, x) local en mm
    W = np.stack([(C[:, 0] - CG.LARGO0), -C[:, 1]], 1)                # mundo (x, y) en mm
    seg = np.roll(W, -1, 0) - W
    lon = np.linalg.norm(seg, axis=1)
    acum = np.concatenate([[0.0], np.cumsum(lon)])
    total = float(acum[-1])

    def arco(p):
        t = np.clip(((p - W) * seg).sum(1) / (lon ** 2 + 1e-12), 0, 1)
        d = np.linalg.norm(W + seg * t[:, None] - p, axis=1)
        k = int(np.argmin(d))
        return float(acum[k] + t[k] * lon[k])

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    capa = bm.loops.layers.uv.verify()
    co = {v.index: np.array(v.co) * 1000.0 for v in bm.verts}
    xs, ys, zs = (np.array([c[i] for c in co.values()]) for i in range(3))
    x0, y0, y1, z0, alto = xs.min(), ys.min(), ys.max(), zs.min(), zs.max() - zs.min()
    ancho, largo = y1 - y0, xs.max() - x0
    n_tiras = 3
    lt = total / n_tiras
    s_v = {i: arco(c[:2]) for i, c in co.items()}
    ANCHO = max(2 * ancho + hueco, lt)
    ALTO = largo + n_tiras * (alto + hueco)
    lado = max(ANCHO, ALTO) + 2 * hueco
    area = 0.0
    for f in bm.faces:
        nz = f.normal.z
        if abs(nz) > 0.7:
            for l in f.loops:
                c = co[l.vert.index]
                u = (c[1] - y0) if nz > 0 else (ancho + hueco + (y1 - c[1]))
                l[capa].uv = ((u + hueco) / lado, (c[0] - x0 + hueco) / lado)
        else:
            sc = arco((np.array(f.calc_center_median()) * 1000.0)[:2])
            k = min(n_tiras - 1, int(sc / lt))
            for l in f.loops:
                sv = s_v[l.vert.index]
                if sv - sc > total / 2:
                    sv -= total
                elif sc - sv > total / 2:
                    sv += total
                l[capa].uv = ((sv - k * lt + hueco) / lado, (largo + hueco + k * (alto + hueco) + co[l.vert.index][2] - z0 + hueco) / lado)
        P = [l[capa].uv for l in f.loops]
        area += abs(sum(P[i].x * P[(i + 1) % len(P)].y - P[(i + 1) % len(P)].x * P[i].y for i in range(len(P)))) / 2
    for e in bm.edges:
        e.seam = len(e.link_faces) == 2 and ((abs(e.link_faces[0].normal.z) > 0.7) != (abs(e.link_faces[1].normal.z) > 0.7))
    bm.to_mesh(ob.data)
    bm.free()
    # en los rincones concavos del contorno (caja del mastil, cutaway) el punto mas cercano salta de un tramo a otro
    # y alguna cara del canto se pliega sobre su vecina: cada una se saca a la banda libre de arriba, proyectada en
    # su propio plano y a la misma escala
    import uv as _uv
    from mathutils import Vector
    sueltas = 0
    for _ in range(4):
        malas = _uv.caras_solapadas(nombre) or []
        if not malas:
            break
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        capa = bm.loops.layers.uv.verify()
        for i in malas:
            f = bm.faces[i]
            n = f.normal
            ex = (f.verts[1].co - f.verts[0].co).normalized()
            ey = n.cross(ex)
            col, fil = sueltas % 60, sueltas // 60
            org = Vector((hueco + col * 10.0, ALTO + 2 * hueco + fil * 10.0))
            for l in f.loops:
                d = (l.vert.co - f.verts[0].co) * 1000.0
                l[capa].uv = ((org.x + d.dot(ex) + 1.0) / lado, (org.y + d.dot(ey) + 4.0) / lado)
            for e in f.edges:
                e.seam = True
            sueltas += 1
        bm.to_mesh(ob.data)
        bm.free()
    return {"px_mm": round(float(4096.0 / lado), 3), "ocupacion_pct": round(float(area * 100), 2), "lado_mm": round(float(lado), 1),
            "perimetro_mm": round(total, 1), "caras_sueltas": sueltas, "alto_usado_mm": round(float(ALTO), 1)}


def desplegar(margen=0.0018):
    """Cada set en su atlas. Con uno solo, las dos caras del cuerpo (400 x 315 mm) mandan en el empaquetado.
    Cuerpo: la tapa y el dorso, enteros (una isla cada uno); el canto, en tiras de 340 mm. Mastil y herrajes: cara
    plana contra canto; las cuerdas (islas de 650 x 2 mm que fijaban la escala de todo el atlas) se parten cada
    170 mm y van al 55 %, como las caras tapadas."""
    import lowpoly
    import uv
    out = {}
    tiras_canto = lowpoly.costura_tiras(0.34, ancho=0.03)
    tiras_cuerda = lowpoly.costura_tiras(0.17, ancho=0.03)
    pared = lambda e: all(abs(f.normal.z) <= 0.7 for f in e.link_faces) and tiras_canto(e)
    cuerda = lambda e: all(_fina(f) for f in e.link_faces) and tiras_cuerda(e)
    reglas = {PARTES[0]: (lowpoly.cualquiera(_cara_plana, pared), 50, None),
              PARTES[1]: (lowpoly.cualquiera(_cara_plana, cuerda), 75, lambda isla: all(_fina(f) for f in isla))}
    out[PARTES[0]] = {"manual": uv_cuerpo(PARTES[0]), "solapes": len(uv.caras_solapadas(PARTES[0]) or [])}
    for n in PARTES[1:]:
        extra, ang, tb = reglas[n]
        for e in bpy.data.objects[n].data.edges:
            e.use_seam = False
        out[n] = uv.desplegar([n], margen=margen, extra=extra, angulo_grados=ang, refinado=("ejes", 25, 12, "aislar", "aislar"))
        out[n]["ocultas"] = uv.encoger_ocultas(n, margen=margen, tambien=tb)
        out[n]["repaso"] = []
        for _ in range(3):
            malas = uv.caras_solapadas(n) or []
            out[n]["repaso"].append(len(malas))
            if not malas:
                break
            uv._aislar(n, malas)
            uv._desplegar_una_vez([n], margen, "MINIMUM_STRETCH")
            uv.encoger_ocultas(n, margen=margen, tambien=tb)
    return out


def parte(set_, nombre="_LP_solo"):
    """Copia temporal de la low poly ya unida con solo las caras de un set ("LP_Cuerpo" o "LP_Mastil"): las
    mascaras de `substance` se hornean sobre UN atlas y los dos sets comparten el 0-1. Borrarla con `quitar_parte`."""
    import bmesh
    lp = bpy.data.objects[NOMBRE]
    o = lp.copy()
    o.data = lp.data.copy()
    o.name = o.data.name = nombre
    bpy.data.collections[COL].objects.link(o)
    k = [m.name for m in o.data.materials].index(set_)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != k], context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    return o.name


def quitar_parte(nombre="_LP_solo"):
    o = bpy.data.objects.get(nombre)
    if o:
        d = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(d)
