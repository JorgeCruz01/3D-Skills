"""Excerpt of a `preparar_sp.py` (handheld multimeter): UV seams for a height-field shell and unwrapping its visible
face FLATTENED. `CM` is the prop builder, `L` is `lowpoly`, `MM` = 0.001. Call order: `g = aplanar(o)`, then
`uv.desplegar([o], extra=costuras_de(o), metodo="MINIMUM_STRETCH")`, then `restaurar(o, g)`."""
def costuras_de(nombre):
    """Cada media funda es una cascara lisa: se abre entre la cara vista y el canto, y el canto se parte con un corte a
    45 grados en cada esquina (de una pieza manda en la escala del atlas)."""
    w, h, zc = CM.W * MM, CM.H2 * MM, CM.ZC * MM
    marco = lambda c: abs(c.x) > w - 0.008 or abs(c.z - zc) > h - 0.008
    return L.cualquiera(L.costura_por_orientacion((0, 1, 0), 0.5), L.costura_por_orientacion((1, 0, 0), 0.7, marco))


def aplanar(nombre):
    """Lleva a un plano los vertices de la cara vista de una media funda que NO estan en el canto redondeado (los que
    distan del contorno mas que el radio de rodadura). Asi la cara, con su rebaje, es una sola isla y su UV es la
    proyeccion plana exacta; el canto redondo se despliega tal cual. Devuelve {indice: y original} para `restaurar`."""
    o = bpy.data.objects[nombre]
    gi = o.vertex_groups["Cara_Frente"].index
    lado = -1.0 if "Frente" in nombre else 1.0
    guardado = {}
    for v in o.data.vertices:
        if v.co.y * lado <= 0.004 or not any(g.group == gi for g in v.groups):
            continue
        if float(CM.distancia_al_borde(v.co.x * 1000, v.co.z * 1000 - CM.ZC)) >= CM.RODADO - 0.01:
            guardado[v.index] = v.co.y
            v.co.y = lado * CM.D2 * MM
    o.data.update()
    return guardado


def restaurar(nombre, guardado):
    me = bpy.data.objects[nombre].data
    for i, y in guardado.items():
        me.vertices[i].co.y = y
    me.update()
