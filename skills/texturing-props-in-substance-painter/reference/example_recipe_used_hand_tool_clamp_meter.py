"""Look-dev de la pinza amperimetrica AMPVEK en Substance 3D Painter. Un set.

    python ../_herramientas/sp.py rehacer Pinza_Amperimetrica

Aspecto: herramienta de electricista USADA, de maletin. Carcasa verde azulada con grano de inyeccion, cantos rozados
a un tono mas claro, aranazos y mugre de manos en ranuras y juntas; panel negro mate con brillo de dedos alrededor
del dial y los rotulos algo gastados; mordaza grafito con roces claros donde abraza el cable; dial y boton naranjas
descoloridos y sucios en el moleteado; pantalla LCD verdosa con aranazos finos; hembrillas de laton apagado;
tornillo zincado.

Mascaras (Texturas/Bakes/Mascaras/): MK_Carcasa, MK_Panel, MK_Grafito, MK_Acento, MK_Pantalla, MK_Laton,
MK_Acero_Zinc, MK_Tinta_Blanca, MK_Tinta_Roja, MK_Tinta_Negra. Campos CP_* (eje Z).
"""
from sp_receta import Receta

MUGRE = "#2E2A24"
POLVO = "#7C776E"


def _plastico(r, nombre, cl, color, claro, rug, tintas=(), mugre=0.55):
    G = r.grupo(nombre, clases=cl)
    r.capa(nombre + ": base", G, {"baseColor": color, "roughness": rug, "metallic": 0})
    f = r.capa(nombre + ": grano de inyeccion", G, {"height": 0.0015, "roughness": rug + 0.08}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa(nombre + ": tono desigual", G, {"baseColor": claro, "roughness": rug + 0.05}, opac=0.14)
    r.grunge(f, "Clouds 2", 4)
    f = r.capa(nombre + ": brillo de manos", G, {"roughness": rug - 0.22}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.5, 0.4)
    for clase, col in tintas:
        r.capa(nombre + ": rotulo " + clase, G, {"baseColor": col, "roughness": 0.5}, clases=(clase,))
    if tintas:
        f = r.capa(nombre + ": rotulos gastados", G, {"baseColor": color, "roughness": rug}, opac=0.25, clases=tuple(t for t, _ in tintas))
        r.grunge(f, "Grunge Scratches Fine", 9)
        r.escaneo(f, 0.3, 0.6)
    f = r.capa(nombre + ": aranazos", G, {"baseColor": claro, "roughness": rug + 0.12, "height": -0.002}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.12, 0.85)
    f = r.capa(nombre + ": cantos rozados", G, {"baseColor": claro, "roughness": rug + 0.1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.24, "Wear_Contrast": 0.7, "Grunge_Amount": 0.85, "grunge_scale": 8})
    f = r.capa(nombre + ": mugre en ranuras", G, {"baseColor": MUGRE, "roughness": 0.85}, opac=mugre)
    r.gen(f, "Dirt", {"dirt_level": 0.22, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    f = r.capa(nombre + ": motas", G, {"baseColor": MUGRE, "roughness": 0.8}, opac=0.35)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.05, 0.88)
    return G


def construir():
    r = Receta("LP_Pinza", "pinza AMPVEK")
    Z = r.grupo("Fondo")
    r.capa("Gris de fondo", Z, {"baseColor": "#1C1D1F", "roughness": 0.55, "metallic": 0})

    _plastico(r, "Carcasa", ("Carcasa",), "#0E6F78", "#4FA3A8", 0.5)
    _plastico(r, "Panel", ("Panel", "Tinta_Blanca", "Tinta_Roja"), "#141517", "#44464A", 0.55,
              (("Tinta_Blanca", "#CFCFCA"), ("Tinta_Roja", "#C4281C")), mugre=0.3)
    _plastico(r, "Mordaza", ("Grafito",), "#2C2E32", "#6A6D72", 0.5, mugre=0.4)
    _plastico(r, "Dial", ("Acento",), "#D8731E", "#E0A066", 0.5, mugre=0.75)

    P = r.grupo("Pantalla", clases=("Pantalla", "Tinta_Negra"))
    r.capa("LCD verdoso", P, {"baseColor": "#7E8672", "roughness": 0.14, "metallic": 0})
    r.capa("Digitos", P, {"baseColor": "#17181A", "roughness": 0.14}, clases=("Tinta_Negra",))
    f = r.capa("Pantalla: aranazos", P, {"baseColor": "#A0A698", "roughness": 0.4}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.12, 0.85)
    f = r.capa("Pantalla: huellas", P, {"roughness": 0.35}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)

    L = r.grupo("Hembrillas", clases=("Laton",))
    r.capa("Laton apagado", L, {"baseColor": "#9A7A3A", "roughness": 0.38, "metallic": 1})
    f = r.capa("Laton: patina", L, {"baseColor": "#4A3A1E", "roughness": 0.6}, opac=0.55)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.45, 0.4)

    T = r.grupo("Tornillo", clases=("Acero_Zinc",))
    r.capa("Acero zincado", T, {"baseColor": "#9A9C9E", "roughness": 0.36, "metallic": 1})
    f = r.capa("Tornillo: oscurecido", T, {"baseColor": "#4A4844", "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 12)
    r.escaneo(f, 0.4, 0.5)
    return r
