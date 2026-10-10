"""Cast parts (a revolver frame, hammer, trigger) as a quad low poly: decimate the high poly, QuadriFlow it with sharp
edges kept, snap back, relax. And the seams that work on a remeshed part, which has no edge loops to follow.
Excerpt of a prop's `construir_lp.py`; comments are in Spanish like the toolkit. `Q` = quads, `T` = tela, `L` = lowpoly."""


def _retopo(nombre, origen, caras, vivos=None, previo=90000, semilla=0, relajar=3):
    """Low poly de una pieza colada: copia diezmada del high poly, remallada en quads con QuadriFlow y pegada otra
    vez al high poly. Sale redonda donde el high poly es redondo, que es lo que una jaula de prismas cruzados no da.
    `vivos` (grados): sin el, QuadriFlow cruza los cantos del guardamonte y su union con la empunadura sale arrugada."""
    import tela as T
    o = T.diezmar(nombre, bpy.data.objects[origen], previo, COL)
    o.data.materials.clear()
    c = Q.retopo(o, caras, vivos=vivos, semilla=semilla, escala=100.0)
    a = Q.ajustar(o, [origen])
    # QuadriFlow deja los lazos ondulados donde no siguen una arista: se relajan los vertices y se vuelven a pegar
    import bmesh
    for _ in range(relajar):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.to_mesh(o.data)
        bm.free()
        a = Q.ajustar(o, [origen])
    o["retopo"] = str((c["quads"], c["tris"], c["ngonos"], a["max_mm"], a["media_mm"]))
    return o


def _costuras(bm, piezas):
    """Aristas que son costura, por tipo de pieza:

    - armazon remallado (con sus cachas): cada costado (caras que miran a +-X) es una isla grande y casi plana; el
      canto que los une (lomo, fleje, guardamonte, paredes de la ventana) queda en banda y lo abre la red de seguridad.
    - tambor: la cara delantera y la trasera contra la piel.
    - martillo y gatillo remallados: los dos costados contra el canto.
    El canon (cajas y cilindros cruzados) lo resuelve el umbral de angulo de `uv.desplegar`."""
    capa = bm.faces.layers.int["pieza"]
    S = set()
    for k, nombre in enumerate(piezas):
        caras = [f for f in bm.faces if f[capa] == k]
        dentro = set(caras)
        aristas = {e for f in caras for e in f.edges if len(e.link_faces) == 2 and all(g in dentro for g in e.link_faces)}
        if nombre in ("Armazon", "Martillo", "Gatillo", "Pestillo"):
            u = 0.78 if nombre == "Armazon" else 0.7

            def lado(f):
                """Costado derecho o izquierdo; y el canto, partido por hacia donde mira (arriba, abajo, delante,
                detras): en UNA banda se enroscaba, se pisaba y la red de seguridad lo dejaba en 801 islas."""
                n = f.normal
                if abs(n.x) > u:
                    return 1 if n.x > 0 else -1
                if abs(n.y) >= abs(n.z):
                    return 2 if n.y > 0 else -2
                return 3 if n.z > 0 else -3
            for e in aristas:
                a, b = e.link_faces
                if lado(a) != lado(b):
                    S.add(e.index)
        elif nombre == "Tambor":
            for e in aristas:
                a, b = e.link_faces
                if (abs(a.normal.y) > 0.7) != (abs(b.normal.y) > 0.7):
                    S.add(e.index)
    return S


def desplegar(margen=0.002):
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
    # sin los umbrales 5 y 0 de la red de seguridad: por DOS caras solapadas trituraba una isla de 824 en quads sueltos
    info = uv.desplegar([NOMBRE], margen=margen, angulo_grados=50, vista=Vector((0.8, -0.5, 0.4)).normalized(), extra=lambda e: e.index in S,
                        refinado=("ejes", 25, "aislar", "aislar", "aislar"))
    info["costuras_propias"] = len(S)
    info["ocultas"] = uv.encoger_ocultas(NOMBRE, margen=margen)
    # sin `uv.soldar_uv`: en esta malla remallada unia dos UV vecinas de islas distintas y dejaba 2 caras solapadas
    info["solapadas"] = len(uv.caras_solapadas(NOMBRE))
    return info
