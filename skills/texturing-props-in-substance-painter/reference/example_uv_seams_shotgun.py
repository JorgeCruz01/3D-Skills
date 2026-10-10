"""UV seams by piece type for a long gun (tubes, a symmetric stock, a receiver). Excerpt of the shotgun's construir_lp.py;
`CE` is the prop's dimension module, `MM` = 0.001."""
# ------------------------------------------------------------------ UV con costuras propias

# pieza de revolucion sobre Y -> hacia donde mira su costura a lo largo (el lado que no se ve)
TUBOS = {"Canon": (0, 0, -1), "Tubo_Almacen": (0, 0, 1), "Tapon_Almacen": (0, 0, 1), "Cerrojo": (1, 0, 0), "Enganche_Portafusil": (0, 0, 1)}
# anillos donde se parte una piel demasiado larga para el atlas (cota y de la foto): el canon, bajo la anilla
ANILLOS = {"Canon": (CE.Y_ANILLA[0] + 3.0,)}
BOCA_VISTA = 45.0            # mm de anima que se ven desde la boca; el resto del anima es una isla oculta


def _anima(f, c):
    """Cara del interior del canon: mira hacia el eje."""
    r = f.calc_center_median() - c
    r.y = 0
    return r.length < (CE.CANON["anima"] + 0.8) * MM and f.normal.dot(r) < 0


def _costuras(bm, piezas):
    """Aristas que son costura, con una regla por tipo de pieza:

    - tubo (canon, almacen, tapon, cerrojo): UNA linea a lo largo por el lado que tapa otra pieza, costura en cada
      tapa (la pone el umbral de angulo) y los anillos de ANILLOS. El anima se separa de su boca.
    - culata: plano de simetria, por el lomo y por el vientre: dos mitades que se despliegan casi sin estirar.
    - guardamanos: linea central del techo, bajo el canon.
    - cajon: las dos lineas del fondo donde empieza la boca de carga; costados y techo quedan en UNA isla.
    El resto (cantonera, guardamonte, piezas pequenas) lo resuelve el umbral de angulo de `uv.desplegar`."""
    from mathutils import Vector
    capa = bm.faces.layers.int["pieza"]
    S = set()
    for k, nombre in enumerate(piezas):
        caras = [f for f in bm.faces if f[capa] == k]
        aristas = {e for f in caras for e in f.edges}
        cen = {f: f.calc_center_median() for f in caras}
        if nombre in TUBOS:
            vs = {v for f in caras for v in f.verts}
            c = sum((v.co for v in vs), Vector()) / len(vs)
            d = Vector(TUBOS[nombre])
            lado = d.cross(Vector((0, 1, 0)))

            def ang(v):
                r = v.co - c
                return math.atan2(r.dot(lado), r.dot(d))
            a0 = min((ang(v) for v in vs), key=abs)
            cortes = [CE.Y(y) for y in ANILLOS.get(nombre, ())]
            boca = CE.Y(CE.Y_BOCA) + BOCA_VISTA * MM
            for e in aristas:
                a, b = e.link_faces
                if (abs(a.normal.y) > 0.7) != (abs(b.normal.y) > 0.7):      # tapa: el chaflan de 45 grados no llega al umbral de angulo
                    S.add(e.index)
                elif all(abs(ang(v) - a0) < math.radians(1.2) for v in e.verts) and abs(a.normal.y) < 0.7 and abs(b.normal.y) < 0.7:
                    S.add(e.index)
                elif any((cen[a].y - y) * (cen[b].y - y) < 0 for y in cortes):
                    S.add(e.index)
                elif nombre == "Canon" and (cen[a].y - boca) * (cen[b].y - boca) < 0 and _anima(a, c) and _anima(b, c):
                    S.add(e.index)
        elif nombre in ("Culata", "Guardamanos"):
            for e in aristas:
                a, b = e.link_faces
                if nombre == "Guardamanos" and (abs(a.normal.y) > 0.5) != (abs(b.normal.y) > 0.5):     # testeros, a mitad del canto redondo
                    S.add(e.index)
                elif cen[a].x * cen[b].x < 0 and abs(a.normal.y) < 0.7 and abs(b.normal.y) < 0.7:
                    if nombre == "Culata" or a.normal.z > 0.5:
                        S.add(e.index)
        elif nombre == "Cajon":
            x0 = 10.5 * MM
            for e in aristas:
                a, b = e.link_faces
                if a.normal.z < -0.9 and b.normal.z < -0.9 and (abs(cen[a].x) - x0) * (abs(cen[b].x) - x0) < 0:
                    S.add(e.index)
    return S


def desplegar(margen=0.0022):
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
    info = uv.desplegar([NOMBRE], margen=margen, angulo_grados=50, vista=Vector((0.6, -0.5, 0.6)).normalized(),
                        extra=lambda e: e.index in S)
    info["costuras_propias"] = len(S)
    y_boca = CE.Y(CE.Y_BOCA) + BOCA_VISTA * MM
    eje = Vector((0, 0, CE.Z(0)))

    def anima(isla):                      # el anima, salvo su boca: nadie la ve y es una tira de 600 mm
        c = sum((f.calc_center_median() for f in isla), Vector()) / len(isla)
        return c.y > y_boca and all(_anima(f, eje) for f in isla)
    info["ocultas"] = uv.encoger_ocultas(NOMBRE, margen=margen, tambien=anima)
    info["uv_soldadas"] = uv.soldar_uv(NOMBRE)
    return info
