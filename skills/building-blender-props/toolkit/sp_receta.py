"""Constructor de recetas para `sp_apply_recipe` del MCP de Substance 3D Painter.

Una receta es una lista de operaciones que Painter aplica en un solo paso de deshacer. Este
modulo solo arma el JSON; no habla con Painter (eso es `sp.py`).

    r = Receta("LP_Cuchillo")
    g = r.grupo("Acero", clases=("Recubrimiento", "Tinta"))        # mascara = MK_Recubrimiento + MK_Tinta
    r.capa("Acero base", g, {"baseColor": "#B9BABD", "roughness": 0.30, "metallic": 1})
    f = r.capa("Rayado", g, {"roughness": 0.5})
    r.mapa(f, "CP_Rayado_Largo")                                   # mascara = mapa horneado en Blender
    r.escaneo(f, 0.55, 0.8)                                        # ... recortado (Histogram Scan)
    r.gen(f, "Metal Edge Wear", {...}, fusion="Multiply")          # ... por un generador

Reglas que costaron una pasada cada una:
- Un fill solo afecta a los canales que reciben fuente. NO usar `disable_channels` sobre un fill
  recien creado: reasignar sus canales activos devuelve las fuentes al valor por defecto y todo
  sale gris (0.906) sin ningun error.
- En una mascara los efectos se apilan en el orden de las llamadas; el segundo en adelante
  necesita su fusion (LinearDodge suma clases, Multiply recorta).
- Un grunge en proyeccion Triplanar no depende de las UV y no deja costura; un mapa horneado
  (MK_, HL_, CP_) va siempre en proyeccion UV.
"""
import json


class Receta:
    def __init__(self, texture_set, nombre="receta"):
        self.ts, self.nombre, self.ops, self._n = texture_set, nombre, [], 0

    def _ref(self, p):
        self._n += 1
        return "%s%d" % (p, self._n)

    # ---------------------------------------------------------------- capas
    def grupo(self, nombre, dentro=None, clases=()):
        r = self._ref("g")
        o = {"op": "add_layer", "ref": r, "kind": "group", "name": nombre}
        if dentro:
            o["position"] = {"inside": "$" + dentro}
        self.ops.append(o)
        self.clases(r, clases)
        return r

    def capa(self, nombre, dentro, canales, opac=None, fusion=None, proy=None, clases=(), material=None):
        """Fill. `canales` = {canal: '#hex' | numero | nombre de recurso | {resource, usage, params}}.
        `opac` y `fusion` admiten un valor o {canal: valor}."""
        r = self._ref("f")
        o = {"op": "add_layer", "ref": r, "kind": "fill", "name": nombre, "position": {"inside": "$" + dentro},
             "channels": canales}
        if material:
            o["material"] = material
        if proy:
            o["projection"] = proy
        if opac is not None:
            o["opacity"] = opac
        if fusion is not None:
            o["blending"] = fusion
        self.ops.append(o)
        self.clases(r, clases)
        return r

    # ---------------------------------------------------------------- mascaras
    def _efecto(self, e, fusion, opac, nombre=None):
        if fusion:
            e["blending"] = fusion
        if opac is not None:
            e["opacity"] = opac
        if nombre:
            e["name"] = nombre
        self.ops.append(e)

    def clases(self, r, clases):
        """Suma de mascaras de clase MK_<clase> (la primera en Normal, las demas en LinearDodge)."""
        for i, c in enumerate(clases):
            self.mapa(r, "MK_" + c, fusion="LinearDodge" if i else None)

    def mapa(self, r, recurso, fusion=None, opac=None):
        """Mapa horneado en Blender e importado como textura (MK_, HL_, CP_), en UV."""
        self._efecto({"op": "add_effect", "uid": "$" + r, "kind": "fill", "target": "mask", "value": recurso,
                      "usage": "texture", "projection": {"mode": "UV"}}, fusion, opac, recurso)

    def grunge(self, r, recurso, escala=3.0, fusion=None, params=None, opac=None):
        """Procedural de la biblioteca en triplanar. `escala` mayor = grano mas fino."""
        self._efecto({"op": "add_effect", "uid": "$" + r, "kind": "fill", "target": "mask", "value": recurso,
                      "usage": "procedural", "projection": {"mode": "Triplanar", "scale": escala},
                      "params": params or {}}, fusion, opac)

    def gen(self, r, recurso, params=None, fusion=None, opac=None):
        """Generador que lee los mesh maps (Metal Edge Wear, Dirt, Mask Editor, Curvature...)."""
        self._efecto({"op": "add_effect", "uid": "$" + r, "kind": "generator", "target": "mask", "resource": recurso,
                      "params": params or {}}, fusion, opac)

    def filtro(self, r, recurso, params=None, destino="mask"):
        self.ops.append({"op": "add_effect", "uid": "$" + r, "kind": "filter", "target": destino, "resource": recurso,
                         "params": params or {}})

    def escaneo(self, r, posicion=0.5, contraste=0.5):
        """Histogram Scan sobre lo que la mascara lleva hasta aqui: `posicion` mueve el umbral
        (MAYOR = MAS blanco: 0.15 deja hilos sueltos, 0.7 lo cubre casi todo) y `contraste`
        endurece el borde. Es el control de cantidad."""
        self.filtro(r, "Histogram Scan", {"Position": posicion, "Contrast": contraste})

    def invertir(self, r):
        self.filtro(r, "Invert", {})

    def desenfoque(self, r, intensidad=1.0):
        self.filtro(r, "Blur", {"Intensity": intensidad})

    def valor(self, r, v, fusion=None, opac=None):
        """Relleno uniforme dentro de la mascara (subir o bajar el conjunto)."""
        self._efecto({"op": "add_effect", "uid": "$" + r, "kind": "fill", "target": "mask", "value": float(v)},
                     fusion, opac)

    # ---------------------------------------------------------------- salida
    def json(self, borrar=()):
        ops = [{"op": "delete", "uid": u} for u in borrar] + self.ops
        return {"name": self.nombre, "texture_set": self.ts, "ops": ops}

    def guardar(self, ruta, borrar=()):
        with open(ruta, "w", encoding="utf8") as fh:
            json.dump(self.json(borrar), fh, indent=1)
        return len(self.ops)


def tri(escala):
    return {"mode": "Triplanar", "scale": escala}
