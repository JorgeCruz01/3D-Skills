"""Materiales PBR del high poly: base de ambientCG / Poly Haven + capas procedurales.

El HP no tiene UV: las texturas se proyectan en caja sobre coordenadas de objeto,
con `tam_m` = metros de mundo que cubre un mosaico. Las capas de suciedad en
cavidades (nodo AO) y desgaste de canto (Pointiness) se hornean despues al atlas
de la low poly, que es donde vive el material final.
"""
import bpy


def _img(ruta, color):
    img = bpy.data.images.load(ruta, check_existing=True)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def pbr(nombre, mapas, tinte=(1, 1, 1), tam_m=0.25, rough=(0.0, 1.0), metal=None,
        normal=1.0, suciedad=0.35, color_suciedad=(0.05, 0.04, 0.03), desgaste=0.0,
        color_desgaste=(0.8, 0.8, 0.8), transmision=0.0, ior=1.45, mezcla_tinte=1.0,
        manchas=0.0, color_manchas=(0.06, 0.05, 0.04), escala_manchas=9.0,
        desconchado=0.0, escala_desconchado=45.0):
    """Crea (o rehace) el material `nombre`. `rough` = (suma, factor) sobre el mapa."""
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    out.location = (900, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (600, 0)
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = N.new("ShaderNodeTexCoord")
    tc.location = (-1100, 0)
    mp = N.new("ShaderNodeMapping")
    mp.location = (-900, 0)
    mp.inputs["Scale"].default_value = (1 / tam_m,) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])

    def tex(clave, color, y):
        if clave not in mapas:
            return None
        t = N.new("ShaderNodeTexImage")
        t.image = _img(mapas[clave], color)
        t.projection = "BOX"
        t.projection_blend = 0.25
        t.location = (-650, y)
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    # --- color base: textura x tinte, luego suciedad y desgaste
    tcol = tex("color", True, 300)
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.location = (-350, 300)
    mul.inputs["Factor"].default_value = mezcla_tinte
    if tcol:
        L.new(tcol.outputs["Color"], mul.inputs["A"])
    else:
        mul.inputs["A"].default_value = (1, 1, 1, 1)
    mul.inputs["B"].default_value = (*tinte, 1)
    col = mul.outputs["Result"]

    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.location = (-650, 650)
    ao.samples = 4
    ao.inputs["Distance"].default_value = 0.012
    ruido = N.new("ShaderNodeTexNoise")
    ruido.location = (-650, 900)
    ruido.inputs["Scale"].default_value = 18.0
    ruido.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], ruido.inputs["Vector"])
    rampa = N.new("ShaderNodeValToRGB")
    rampa.location = (-400, 650)
    rampa.color_ramp.elements[0].position = 0.35
    rampa.color_ramp.elements[0].color = (1, 1, 1, 1)
    rampa.color_ramp.elements[1].position = 0.9
    rampa.color_ramp.elements[1].color = (0, 0, 0, 1)
    L.new(ao.outputs["AO"], rampa.inputs["Fac"])
    cav = N.new("ShaderNodeMath")
    cav.operation = "MULTIPLY"
    cav.location = (-150, 650)
    cav.inputs[1].default_value = suciedad
    L.new(rampa.outputs["Color"], cav.inputs[0])
    cav2 = N.new("ShaderNodeMath")
    cav2.operation = "MULTIPLY"
    cav2.location = (0, 800)
    L.new(cav.outputs[0], cav2.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.location = (-400, 900)
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.4
    mr.inputs["To Max"].default_value = 1.0
    L.new(ruido.outputs["Fac"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], cav2.inputs[1])
    sucio = N.new("ShaderNodeMix")
    sucio.data_type = "RGBA"
    sucio.location = (0, 300)
    L.new(cav2.outputs[0], sucio.inputs["Factor"])
    L.new(col, sucio.inputs["A"])
    sucio.inputs["B"].default_value = (*color_suciedad, 1)
    col = sucio.outputs["Result"]

    borde = None
    if desgaste > 0:
        geo = N.new("ShaderNodeNewGeometry")
        geo.location = (-650, 1200)
        r2 = N.new("ShaderNodeValToRGB")
        r2.location = (-400, 1200)
        r2.color_ramp.elements[0].position = 0.52
        r2.color_ramp.elements[1].position = 0.62
        L.new(geo.outputs["Pointiness"], r2.inputs["Fac"])
        b2 = N.new("ShaderNodeMath")
        b2.operation = "MULTIPLY"
        b2.location = (-150, 1200)
        L.new(r2.outputs["Color"], b2.inputs[0])
        L.new(mr.outputs["Result"], b2.inputs[1])
        b3 = N.new("ShaderNodeMath")
        b3.operation = "MULTIPLY"
        b3.location = (0, 1200)
        b3.inputs[1].default_value = desgaste
        L.new(b2.outputs[0], b3.inputs[0])
        borde = b3.outputs[0]
        gast = N.new("ShaderNodeMix")
        gast.data_type = "RGBA"
        gast.location = (200, 300)
        L.new(borde, gast.inputs["Factor"])
        L.new(col, gast.inputs["A"])
        gast.inputs["B"].default_value = (*color_desgaste, 1)
        col = gast.outputs["Result"]
    # --- manchas (suaves, grandes) y desconchones (duros, pequenos): rompen el
    # aspecto de pieza recien pintada que dejaban solo cavidad y canto
    def _capa(escala, p0, p1, fuerza, color, x):
        r = N.new("ShaderNodeTexNoise")
        r.location = (x, 1500)
        r.inputs["Scale"].default_value = escala
        r.inputs["Detail"].default_value = 8.0
        r.inputs["Roughness"].default_value = 0.65
        L.new(tc.outputs["Object"], r.inputs["Vector"])
        rp = N.new("ShaderNodeValToRGB")
        rp.location = (x + 200, 1500)
        rp.color_ramp.elements[0].position = p0
        rp.color_ramp.elements[1].position = p1
        L.new(r.outputs["Fac"], rp.inputs["Fac"])
        f = N.new("ShaderNodeMath")
        f.operation = "MULTIPLY"
        f.location = (x + 450, 1500)
        f.inputs[1].default_value = fuerza
        L.new(rp.outputs["Color"], f.inputs[0])
        m = N.new("ShaderNodeMix")
        m.data_type = "RGBA"
        m.location = (x + 650, 1500)
        L.new(f.outputs[0], m.inputs["Factor"])
        L.new(col, m.inputs["A"])
        m.inputs["B"].default_value = (*color, 1)
        return m.outputs["Result"], f.outputs[0]

    mancha = None
    if manchas > 0:
        col, mancha = _capa(escala_manchas, 0.48, 0.72, manchas, color_manchas, -650)
    if desconchado > 0:
        col, _ = _capa(escala_desconchado, 0.66, 0.68, desconchado, color_desgaste, 250)
    L.new(col, bsdf.inputs["Base Color"])

    # --- rugosidad: mapa * factor + suma, mas aspera donde hay suciedad
    trou = tex("roughness", False, 0)
    ma = N.new("ShaderNodeMath")
    ma.operation = "MULTIPLY_ADD"
    ma.location = (-350, 0)
    ma.use_clamp = True
    if trou:
        L.new(trou.outputs["Color"], ma.inputs[0])
    else:
        ma.inputs[0].default_value = 0.5
    ma.inputs[1].default_value = rough[1]
    ma.inputs[2].default_value = rough[0]
    rs = N.new("ShaderNodeMath")
    rs.operation = "ADD"
    rs.use_clamp = True
    rs.location = (0, 0)
    L.new(ma.outputs[0], rs.inputs[0])
    rsm = N.new("ShaderNodeMath")
    rsm.operation = "MULTIPLY"
    rsm.location = (-150, -150)
    rsm.inputs[1].default_value = 0.35
    L.new(cav2.outputs[0], rsm.inputs[0])
    L.new(rsm.outputs[0], rs.inputs[1])
    if mancha is not None:
        rs2 = N.new("ShaderNodeMath")
        rs2.operation = "MULTIPLY_ADD"
        rs2.use_clamp = True
        rs2.location = (200, 0)
        L.new(mancha, rs2.inputs[0])
        rs2.inputs[1].default_value = 0.3
        L.new(rs.outputs[0], rs2.inputs[2])
        rs = rs2
    L.new(rs.outputs[0], bsdf.inputs["Roughness"])

    # --- metalico
    tmet = tex("metallic", False, -300)
    if metal is not None:
        bsdf.inputs["Metallic"].default_value = metal
    elif tmet:
        L.new(tmet.outputs["Color"], bsdf.inputs["Metallic"])

    # --- normal
    tnor = tex("normal", False, -600)
    if tnor:
        nm = N.new("ShaderNodeNormalMap")
        nm.location = (-350, -600)
        nm.inputs["Strength"].default_value = normal
        L.new(tnor.outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    if transmision > 0:
        bsdf.inputs["Transmission Weight"].default_value = transmision
        bsdf.inputs["IOR"].default_value = ior
    return mat


def asignar(objeto, material, limpiar=True):
    ob = bpy.data.objects[objeto]
    if limpiar:
        ob.data.materials.clear()
    ob.data.materials.append(material)
    return len(ob.data.materials) - 1


def relieve(nombre, tipo, paso, fondo, caja=None, x_min=None, angulo=30.0):
    """Anade a un material ya creado un relieve fino por sombreado (nodo Bump), en
    coordenadas de objeto, para detalle que no merece geometria y que el bake si
    recoge en el mapa de normales.

    tipo "picado": dos familias de surcos cruzados a +-`angulo` (cachas de madera).
    tipo "hoyuelos": celdas redondas (goma antideslizante).
    `paso` y `fondo` en metros. `caja` = ((y0, y1), (z0, z1)) limita la zona en el
    plano YZ; `x_min` deja el relieve solo donde |x| supera ese valor."""
    import math
    m = bpy.data.materials[nombre]
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    previo = bsdf.inputs["Normal"].links[0].from_socket if bsdf.inputs["Normal"].links else None
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs["Vector"])

    def mat(op, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    y, z, x = sep.outputs["Y"], sep.outputs["Z"], sep.outputs["X"]
    if tipo == "picado":
        k = 2 * math.pi / paso
        c, s_ = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
        u = mat("ADD", mat("MULTIPLY", y, c * k), mat("MULTIPLY", z, s_ * k))
        v = mat("ADD", mat("MULTIPLY", y, c * k), mat("MULTIPLY", z, -s_ * k))
        # piramides: el minimo de dos senos elevados deja surcos en V entre rombos
        alto = mat("MINIMUM", mat("ABSOLUTE", mat("SINE", u)), mat("ABSOLUTE", mat("SINE", v)))
    elif tipo == "tejido":
        # ligamento tafetan visto en coordenadas de objeto: en cada cara dominan las dos
        # coordenadas tangentes y la tercera solo suma una constante
        k = math.pi / paso
        alto = mat("MULTIPLY", mat("ADD", mat("ADD", mat("ABSOLUTE", mat("SINE", mat("MULTIPLY", x, k))),
                                              mat("ABSOLUTE", mat("SINE", mat("MULTIPLY", y, k)))),
                                   mat("ABSOLUTE", mat("SINE", mat("MULTIPLY", z, k)))), 1.0 / 3.0)
    elif tipo == "canale":
        # canale de cincha: surcos finos a lo largo de Z y de la horizontal
        k = math.pi / paso
        alto = mat("ABSOLUTE", mat("SINE", mat("MULTIPLY", mat("ADD", mat("ADD", x, y), z), k)))
    elif tipo == "surcos_y":
        # canales transversales repetidos a lo largo de Y (agarre de un guardamanos): valle estrecho, meseta ancha
        k = math.pi / paso
        alto = mat("POWER", mat("ABSOLUTE", mat("SINE", mat("MULTIPLY", y, k))), 0.35)
    elif tipo == "arruga":
        # arrugado fino de tela: ruido suave del tamano `paso`
        rn = N.new("ShaderNodeTexNoise")
        rn.inputs["Scale"].default_value = 1.0 / paso
        rn.inputs["Detail"].default_value = 3.0
        rn.inputs["Roughness"].default_value = 0.55
        L.new(tc.outputs["Object"], rn.inputs["Vector"])
        alto = rn.outputs["Fac"]
    else:
        vor = N.new("ShaderNodeTexVoronoi")
        vor.feature = "F1"
        vor.inputs["Scale"].default_value = 1.0 / paso
        L.new(tc.outputs["Object"], vor.inputs["Vector"])
        alto = mat("SUBTRACT", 1.0, mat("MULTIPLY", vor.outputs["Distance"], 2.2), clamp=True)
    mascara = None
    if caja:
        for sock, (a, b) in ((y, caja[0]), (z, caja[1])):
            for op, lim in (("GREATER_THAN", a), ("LESS_THAN", b)):
                t = mat(op, sock, lim)
                mascara = t if mascara is None else mat("MULTIPLY", mascara, t)
    if x_min is not None:
        t = mat("GREATER_THAN", mat("ABSOLUTE", x), x_min)
        mascara = t if mascara is None else mat("MULTIPLY", mascara, t)
    if mascara is not None:
        alto = mat("MULTIPLY", alto, mascara)
    b = N.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 1.0
    b.inputs["Distance"].default_value = fondo
    L.new(alto, b.inputs["Height"])
    if previo is not None:
        L.new(previo, b.inputs["Normal"])
    L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m
