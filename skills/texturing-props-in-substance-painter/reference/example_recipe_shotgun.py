"""Look-dev de la escopeta de corredera HALVREK ARMS en Substance 3D Painter.

    python ../_herramientas/sp.py rehacer Escopeta_Corredera vistas_sp.json

Aspecto: arma de servicio con anos de uso y bien cuidada. Pavonado negro azulado que blanquea en aristas, en la boca
y donde corre la corredera (barras de accion y tubo del almacen); nogal al aceite con veta a lo largo, barniz gastado
en los cantos y oscurecido por la mano en la garganta y en los surcos del guardamanos; cantonera de goma mate.

Mascaras (Texturas/Bakes/Mascaras/): ZN_ zonas de uso (mano, mejilla, boca, ventana, apoyo: `substance.zonas`); MK_ por pieza del high poly (`por_objeto`), HL_ cerco de pasadores y guardamonte,
CP_ ruido orientado al canon a dos escalas: fino (rayado) y `_Veta` (veta ancha de la madera); CP_Relieve_Canto/Hueco,
crestas y fondos del relieve de material (surcos, moleteado, cantonera), sacados de la normal horneada en Blender.

El relieve fino del high poly esta en sus materiales, no en su geometria: el mesh map Normal del proyecto es
Texturas/Bakes/NORMAL_blender.png (`substance.normal_hp` + `sp.py normal`), no el horneado de Painter.
"""
from sp_receta import Receta

SET = "LP_Escopeta"
# Blender Y (eje del arma) es -Z en Painter: el nogal se proyecta en triplanar girado para que la veta corra a lo largo
VETA = {"mode": "Triplanar", "scale": 3.0}
PAVONADO = ("Cajon", "Canon", "Tubo", "Guardamonte", "Gatillo", "Barras", "Herrajes", "Pasadores", "Elevador", "Moleteado", "Tinta")


def acero(r):
    A = r.grupo("Acero", clases=PAVONADO + ("Acero_Pulido",))
    r.capa("Acero base", A, {"baseColor": "#B8B9BC", "roughness": 0.30, "metallic": 1})
    f = r.capa("Acero rectificado", A, {"baseColor": "#A3A4A8", "roughness": 0.46})
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.5, 0.5)
    f = r.capa("Acero patina", A, {"baseColor": "#77726C", "roughness": 0.55}, opac=0.45)
    r.grunge(f, "Grunge Dirt", 3)

    P = r.grupo("Pavonado", dentro=A, clases=PAVONADO)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.34, "Wear_Contrast": 0.75, "Grunge_Amount": 0.55, "grunge_scale": 3},
          fusion="Multiply")
    r.capa("Pavon", P, {"baseColor": "#15171C", "roughness": 0.36, "metallic": 1})
    f = r.capa("Pavon gastado a gris", P, {"baseColor": "#3B3A3C", "roughness": 0.46}, opac=0.6)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.38, 0.3)
    r.grunge(f, "Grunge Dirt Scratched", 3, fusion="Multiply")
    f = r.capa("Pavon velo pardo", P, {"baseColor": "#2C2420", "roughness": 0.5}, opac=0.4)
    r.grunge(f, "Clouds 2", 2.5)
    f = r.capa("Aceite y huellas", P, {"roughness": 0.2}, opac=0.55)
    r.grunge(f, "Grunge Fingerprints Smeared", 2.5)
    f = r.capa("Mate de polvo", P, {"roughness": 0.58}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 4)
    r.capa("Marcaje", P, {"baseColor": "#7C7D82", "roughness": 0.4, "height": -0.02}, clases=("Tinta",))

    # roces a lo largo: la corredera sobre el tubo y las barras, el enfundado sobre canon y cajon
    f = r.capa("Roce de la corredera", A, {"baseColor": "#A7A8AC", "roughness": 0.3, "metallic": 1}, opac=0.75)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.24, 0.8)
    r.grunge(f, "Grunge Dirt", 2.0, fusion="Multiply")
    r.mapa(f, "MK_Tubo", fusion="Multiply")
    f = r.capa("Roce de las barras", A, {"baseColor": "#A7A8AC", "roughness": 0.3, "metallic": 1}, opac=0.9)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.4, 0.8)
    r.mapa(f, "MK_Barras", fusion="Multiply")
    f = r.capa("Aranazos largos", A, {"baseColor": "#9A9BA0", "roughness": 0.34, "metallic": 1, "height": -0.008}, opac=0.8)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.024, 0.9)
    r.mapa(f, "CP_Manchas", fusion="Multiply")             # un grunge triplanar aqui dejaba una marca repetida a lo largo del canon
    f = r.capa("Moleteado gastado en las crestas", A, {"baseColor": "#9FA0A4", "roughness": 0.32, "metallic": 1}, opac=0.85,
               clases=("Moleteado",))
    r.mapa(f, "CP_Relieve_Canto", fusion="Multiply")
    r.escaneo(f, 0.6, 0.5)
    f = r.capa("Moleteado mugre en el fondo", A, {"baseColor": "#0E0C0A", "roughness": 0.7}, opac=0.8, clases=("Moleteado",))
    r.mapa(f, "CP_Relieve_Hueco", fusion="Multiply")
    r.escaneo(f, 0.6, 0.4)
    # huella del disparo y del servicio: lo que solo pasa en un sitio del arma
    f = r.capa("Ventana: canto blanqueado", A, {"baseColor": "#B4B5B8", "roughness": 0.28, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.55, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 10})
    r.mapa(f, "ZN_Ventana", fusion="Multiply")
    r.escaneo(f, 0.35, 0.5)
    f = r.capa("Ventana: roces de laton de las vainas", A, {"baseColor": "#B08C4A", "roughness": 0.32, "metallic": 1}, opac=0.7)
    r.mapa(f, "CP_Rayado_Ancho")
    r.escaneo(f, 0.1, 0.9)
    r.mapa(f, "ZN_Ventana", fusion="Multiply")
    r.mapa(f, "MK_Cajon", fusion="Multiply")
    f = r.capa("Ventana: hollin", A, {"baseColor": "#0A0A0A", "roughness": 0.82}, opac=0.6)
    r.mapa(f, "ZN_Ventana")
    r.grunge(f, "Grunge Dusty Powder Soft", 2.5, fusion="Multiply")
    r.escaneo(f, 0.3, 0.3)
    f = r.capa("Boca: corona blanqueada", A, {"baseColor": "#B4B5B8", "roughness": 0.3, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.6, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 10})
    r.mapa(f, "ZN_Boca", fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Boca: hollin", A, {"baseColor": "#0B0B0B", "roughness": 0.85}, opac=0.75)
    r.mapa(f, "ZN_Boca")
    r.grunge(f, "Grunge Dusty Powder Soft", 3.0, fusion="Multiply")
    r.escaneo(f, 0.42, 0.3)
    f = r.capa("Apoyo: pavon comido", A, {"baseColor": "#8E8F93", "roughness": 0.38, "metallic": 1}, opac=0.85)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Dirty", 2.5, fusion="Multiply")
    r.escaneo(f, 0.26, 0.6)
    f = r.capa("Mano: pavon pulido", A, {"baseColor": "#45464A", "roughness": 0.24, "metallic": 1}, opac=0.6, clases=("Guardamonte", "Gatillo"))
    r.grunge(f, "Grunge Fingerprints Smeared", 3.0, fusion="Multiply")
    f = r.capa("Aranazos finos al azar", A, {"baseColor": "#6E6F74", "roughness": 0.5}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 2.2)
    r.escaneo(f, 0.14, 0.85)
    f = r.capa("Picaduras de oxido", A, {"baseColor": "#4A2A16", "roughness": 0.9, "metallic": 1, "height": 0.004}, opac=0.5)
    r.grunge(f, "Grunge Rust Fine", 3.5)
    r.escaneo(f, 0.12, 0.8)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.capa("Cerrojo pulido", A, {"baseColor": "#8D8E91", "roughness": 0.26, "metallic": 1}, clases=("Acero_Pulido",))
    f = r.capa("Cerrojo rayas", A, {"roughness": 0.4, "baseColor": "#A9AAAD"}, clases=("Acero_Pulido",))
    r.mapa(f, "CP_Rayado_Largo", fusion="Multiply")
    f = r.capa("Oxido en rincones", A, {"baseColor": "#3D2516", "roughness": 0.85}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.12, "dirt_contrast": 0.8, "grunge_amount": 0.95})
    f = r.capa("Grasa junto a pasadores", A, {"baseColor": "#0C0B0A", "roughness": 0.25}, opac=0.6)
    r.mapa(f, "HL_Pasadores")
    f = r.capa("Polvo en huecos", A, {"baseColor": "#7C7468", "roughness": 0.9}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.28, "dirt_contrast": 0.5, "grunge_amount": 0.6})


def madera(r):
    M = r.grupo("Nogal", clases=("Nogal", "Nogal_Surcos"))
    # madera escaneada (ambientCG Wood049, CC0, la misma del high poly): figura y poro reales, en triplanar con la
    # veta a lo largo del arma. Importarla antes: sp.py llamar sp_import_resource sobre Texturas/Fuente/Wood049/*.jpg
    tex = lambda m: {"resource": "Wood049_2K-JPG_" + m, "usage": "texture"}
    r.capa("Nogal base", M, {"baseColor": tex("Color"), "roughness": tex("Roughness"), "normal": tex("NormalGL"), "metallic": 0}, proy=VETA,
           opac={"normal": 0.16})          # entera, la normal del escaneo es madera vieja sin acabado
    r.capa("Nogal tono", M, {"baseColor": "#6E3B20"}, opac=0.92, fusion="Multiply")
    f = r.capa("Veta ancha oscura", M, {"baseColor": "#1E0D06", "roughness": 0.42}, opac=0.5)
    r.mapa(f, "CP_Rayado_Largo_Veta")
    r.escaneo(f, 0.4, 0.25)
    f = r.capa("Aguas claras", M, {"baseColor": "#A3602A"}, opac=0.2)
    r.mapa(f, "CP_Manchas_Veta")
    r.escaneo(f, 0.42, 0.25)
    f = r.capa("Figura oscura", M, {"baseColor": "#2E1508"}, opac=0.3)
    r.mapa(f, "CP_Manchas_Veta")
    r.invertir(f)
    r.escaneo(f, 0.35, 0.3)
    r.capa("Poro", M, {"height": {"resource": "CP_Rayado_Largo", "usage": "texture"}}, opac={"height": 0.002}, proy={"mode": "UV"})
    # acabado al aceite: satinado, con el brillo roto por el uso
    r.capa("Aceite satinado", M, {"roughness": 0.34}, opac=0.8)
    f = r.capa("Aceite brillante", M, {"roughness": 0.2}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 1.6)
    f = r.capa("Acabado mate por zonas", M, {"roughness": 0.58}, opac=0.35)
    r.mapa(f, "CP_Manchas")              # "Grunge Wipe Dusty" dejaba una banda de canto recto a media culata
    r.invertir(f)
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Acabado gastado en cantos", M, {"baseColor": "#8A5830", "roughness": 0.62, "height": -0.01}, opac=0.6)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.2, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 6})
    # donde toca el cuerpo: la mano oscurece y pule, la mejilla se lleva el acabado
    f = r.capa("Mano: madera oscurecida", M, {"baseColor": "#27130A", "roughness": 0.26}, opac=0.6)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Fingerprints Smeared Wide", 1.5, fusion="Multiply")
    r.escaneo(f, 0.42, 0.35)
    f = r.capa("Mejilla: acabado comido", M, {"baseColor": "#7A4A26", "roughness": 0.56}, opac=0.4)
    r.mapa(f, "ZN_Mejilla")
    r.grunge(f, "Grunge Dirt", 1.3, fusion="Multiply")
    r.escaneo(f, 0.3, 0.35)
    f = r.capa("Aranazos finos", M, {"baseColor": "#B08357", "roughness": 0.6, "height": -0.006}, opac=0.4)
    r.grunge(f, "Grunge Scratches Fine", 1.4)
    r.escaneo(f, 0.05, 0.85)             # a 0.16 el rayado tapaba la veta y se leia como veta en diagonal
    f = r.capa("Golpes", M, {"baseColor": "#24120A", "roughness": 0.55, "height": -0.03}, opac=0.75)
    r.grunge(f, "Grunge Scratches Rough", 1.6)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.25, 0.7)
    f = r.capa("Golpes de apoyo: madera cruda", M, {"baseColor": "#B58A5C", "roughness": 0.72, "height": -0.035}, opac=0.8)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Rough", 2.2, fusion="Multiply")
    r.escaneo(f, 0.2, 0.75)
    # relieve labrado: surcos del guardamanos y picado del pistolete
    f = r.capa("Labrado: fondo sucio", M, {"baseColor": "#140A05", "roughness": 0.72}, opac=0.85)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.7, 0.4)
    f = r.capa("Surcos: cresta gastada", M, {"baseColor": "#A8763F", "roughness": 0.5}, opac=0.45, clases=("Nogal_Surcos",))
    r.mapa(f, "CP_Relieve_Canto", fusion="Multiply")
    r.escaneo(f, 0.6, 0.4)
    f = r.capa("Labrado: cresta pulida por la mano", M, {"baseColor": "#3A1F10", "roughness": 0.22}, opac=0.7)
    r.mapa(f, "CP_Relieve_Canto")
    r.mapa(f, "ZN_Mano", fusion="Multiply")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Mugre en rincones", M, {"baseColor": "#170C06", "roughness": 0.75}, opac=0.8)
    r.gen(f, "Dirt", {"dirt_level": 0.5, "dirt_contrast": 0.5, "grunge_amount": 0.7})


def resto(r):
    G = r.grupo("Goma", clases=("Goma",))
    r.capa("Goma base", G, {"baseColor": "#1B1B1C", "roughness": 0.72, "metallic": 0})
    f = r.capa("Goma rozada", G, {"baseColor": "#3D3D3D", "roughness": 0.6}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.5, "Grunge_Amount": 0.8, "grunge_scale": 7})
    f = r.capa("Goma polvo", G, {"baseColor": "#6A655C", "roughness": 0.9}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.45, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    f = r.capa("Goma: polvo en el dibujo", G, {"baseColor": "#7A7468", "roughness": 0.92}, opac=0.7)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.6, 0.4)
    f = r.capa("Goma: crestas pulidas", G, {"baseColor": "#2C2C2D", "roughness": 0.5}, opac=0.7)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.6, 0.4)
    L = r.grupo("Laton", clases=("Laton",))
    r.capa("Laton", L, {"baseColor": "#C29D5E", "roughness": 0.3, "metallic": 1})
    f = r.capa("Laton patina", L, {"baseColor": "#5A4428", "roughness": 0.7}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.5, "dirt_contrast": 0.5, "grunge_amount": 0.8})


def construir():
    r = Receta(SET, "escopeta HALVREK")
    acero(r)
    madera(r)
    resto(r)
    S = r.grupo("Suciedad global")
    f = r.capa("Polvo", S, {"baseColor": "#8C7F6C", "roughness": 0.85}, opac=0.08)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
