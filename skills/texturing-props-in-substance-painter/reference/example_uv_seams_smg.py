"""UV seams for sheet-metal bodies (developable: one island each), a swept rod (seam along its inner generatrix, marked on the loose part) and a grip. Excerpt of the SMG's construir_lp.py; `CS` is the prop's dimension module."""
def _costura_varilla(ob, n, tramo=0.11):
    """Marca en la varilla de la culata (un barrido de `n` lados y 700 mm de largo) su costura a lo largo, por la
    generatriz que mira al arma en el tramo que corre sobre el cajon, y un anillo cada `tramo` metros. Se marca en
    la pieza suelta, donde los vertices van anillo a anillo; la marca viaja en un atributo de arista (`costura`)."""
    import numpy as np
    me = ob.data
    V = np.array([v.co[:] for v in me.vertices])
    if len(V) % n:
        return {"error": "vertices %d no multiplo de %d" % (len(V), n)}
    A = V.reshape(-1, n, 3)
    cen = A.mean(1)
    tan = np.gradient(cen, axis=0)
    tan /= np.linalg.norm(tan, axis=1)[:, None] + 1e-12
    horiz = np.abs(tan[:, 0]) > 0.9
    k0 = int(np.argmin(A[horiz, :, 2].mean(0)))                    # la generatriz mas baja donde la varilla va horizontal
    largo = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))])
    cortes = {int(np.argmin(np.abs(largo - d))) for d in np.arange(tramo, largo[-1] - tramo / 2, tramo)}
    at = me.attributes.new("costura", "BOOLEAN", "EDGE")
    val = []
    for e in me.edges:
        i, j = e.vertices
        ri, ki, rj, kj = i // n, i % n, j // n, j % n
        val.append((ki == k0 and kj == k0 and abs(ri - rj) == 1) or (ri == rj and ri in cortes))
    at.data.foreach_set("value", val)
    return {"anillos": len(A), "k0": k0, "cortes": len(cortes), "aristas": int(sum(val)), "largo_mm": round(float(largo[-1]) * 1000)}


# ------------------------------------------------------------------ UV con costuras propias

TUBOS = {"Canon": (0, 0, -1), "Cajon_1": (0, 0, -1)}        # revoluciones sobre X: costura a lo largo, por debajo
CHAPAS = {"Cajon_0": (0, 0, -1), "Armazon_0": (0, 0, 1)}    # cuerpos de chapa: se abren por la cara que tapa el otro cuerpo
LOSAS = ("Cargador_0",)                                     # costados planos contra canto redondo


def _costuras(bm, piezas):
    """Aristas que son costura, por tipo de pieza:

    - cuerpos de chapa (tapa y armazon): son desarrollables. Se abren por UNA linea a lo largo, en la cara que queda
      contra el otro cuerpo (el fondo de la tapa, el techo del armazon), y cada uno es una sola isla sin estirar.
    - cargador: los dos costados planos contra su canto.
    - empunadura: plano de simetria, por el frente y por la trasera.
    - canon y morro: tapas por la normal y una linea a lo largo, por debajo.
    - varilla de la culata: su generatriz interior y un anillo cada 110 mm (atributo de arista `costura`).
    El resto lo resuelve el umbral de angulo de `uv.desplegar`."""
    from mathutils import Vector
    capa = bm.faces.layers.int["pieza"]
    S = set()
    eje = Vector((1, 0, 0))
    marca = bm.edges.layers.bool.get("costura")
    if marca is not None:
        S.update(e.index for e in bm.edges if e[marca])
    for k, nombre in enumerate(piezas):
        caras = [f for f in bm.faces if f[capa] == k]
        cen = {f: f.calc_center_median() for f in caras}
        aristas = {e for f in caras for e in f.edges if len(e.link_faces) == 2 and all(g in cen for g in e.link_faces)}
        if nombre in LOSAS:
            for e in aristas:
                a, b = e.link_faces
                if (abs(a.normal.y) > 0.985) != (abs(b.normal.y) > 0.985):
                    S.add(e.index)
        elif nombre in CHAPAS:
            d = Vector(CHAPAS[nombre])
            for e in aristas:
                a, b = e.link_faces
                if (abs(a.normal.x) > 0.7) != (abs(b.normal.x) > 0.7):                 # testeros
                    S.add(e.index)
                elif a.normal.dot(d) > 0.7 and b.normal.dot(d) > 0.7:
                    ya, yb = cen[a].y, cen[b].y                                          # la cara central (y = 0) contra su vecina de +Y
                    if (abs(ya) < 2e-4 and yb > 5e-4) or (abs(yb) < 2e-4 and ya > 5e-4):
                        S.add(e.index)
        elif nombre == "Empunadura_0":
            for e in aristas:
                a, b = e.link_faces
                if cen[a].y * cen[b].y < 0 and abs(a.normal.z) < 0.7 and abs(b.normal.z) < 0.7:
                    S.add(e.index)
        elif nombre in TUBOS:
            vs = {v for f in caras for v in f.verts}
            c = sum((v.co for v in vs), Vector()) / len(vs)
            d = Vector(TUBOS[nombre])
            lado = d.cross(eje)

            def ang(v):
                r = v.co - c
                return math.atan2(r.dot(lado), r.dot(d))
            a0 = min((ang(v) for v in vs), key=abs)
            for e in aristas:
                a, b = e.link_faces
                if (abs(a.normal.x) > 0.7) != (abs(b.normal.x) > 0.7):
                    S.add(e.index)
                elif all(abs(ang(v) - a0) < math.radians(1.5) for v in e.verts) and abs(a.normal.x) < 0.7 and abs(b.normal.x) < 0.7:
                    S.add(e.index)
    return S


def desplegar(margen=0.0018):
    import bmesh
    import uv
    from mathutils import Vector
    ob = bpy.data.objects[NOMBRE]
    piezas = ob["piezas"].split(",")
    for e in ob.data.edges:
        e.use_seam = False
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    S = _costuras(bm, piezas)
    bm.free()
    info = uv.desplegar([NOMBRE], margen=margen, angulo_grados=50, vista=Vector((-0.3, -0.8, 0.5)).normalized(),
                        extra=lambda e: e.index in S)
    info["costuras_propias"] = len(S)
    info["ocultas"] = uv.encoger_ocultas(NOMBRE, margen=margen)
    info["uv_soldadas"] = uv.soldar_uv(NOMBRE)
    return info
