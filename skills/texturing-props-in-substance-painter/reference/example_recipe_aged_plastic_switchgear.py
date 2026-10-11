"""Look-dev del contactor con rele termico ELKVON en Substance 3D Painter. Un set.

    python ../_herramientas/sp.py rehacer Contactor_Rele_DIN

Aspecto: aparellaje USADO, sacado de un cuadro electrico con anos de servicio. Plastico marfil amarilleado de forma
desigual, con polvo gris posado arriba y en las ranuras de ventilacion, roces y aranazos finos; plastico grafito
con velo de polvo y brillo de dedos; pulsadores y portacontactos algo descoloridos; tornillos zincados con la
cabeza marcada por el destornillador y oscurecidos; espigas de cobre apagadas; carril DIN de zinc con oxido blanco
y roces; rotulos de tampografia algo gastados.

Mascaras (Texturas/Bakes/Mascaras/): MK_Marfil, MK_Grafito, MK_Verde, MK_Naranja, MK_Cobre, MK_Tornillo, MK_Zinc,
MK_Tinta_Negra, MK_Tinta_Blanca. Campos CP_* (eje Z).
"""
from sp_receta import Receta

POLVO = "#77726A"


def _plastico(r, nombre, clases, color, amarillo, tinta=None, color_tinta=None):
    G = r.grupo(nombre, clases=clases)
    r.capa(nombre + ": base", G, {"baseColor": color, "roughness": 0.42, "metallic": 0})
    f = r.capa(nombre + ": grano de inyeccion", G, {"height": 0.0015, "roughness": 0.5}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa(nombre + ": envejecido", G, {"baseColor": amarillo, "roughness": 0.5}, opac=0.25)
    r.grunge(f, "Clouds 2", 3)
    f = r.capa(nombre + ": brillo de dedos", G, {"roughness": 0.24}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.5, 0.4)
    if tinta:
        r.capa(nombre + ": rotulos", G, {"baseColor": color_tinta, "roughness": 0.5}, clases=tinta)
        f = r.capa(nombre + ": rotulos gastados", G, {"baseColor": color, "roughness": 0.45}, opac=0.22, clases=tinta)
        r.grunge(f, "Grunge Scratches Fine", 9)
        r.escaneo(f, 0.3, 0.6)
    f = r.capa(nombre + ": aranazos", G, {"baseColor": amarillo, "roughness": 0.6, "height": -0.0015}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(nombre + ": cantos rozados", G, {"baseColor": amarillo, "roughness": 0.62}, opac=0.5)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.16, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8})
    f = r.capa(nombre + ": polvo en ranuras", G, {"baseColor": POLVO, "roughness": 0.92}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.18, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    f = r.capa(nombre + ": polvo posado", G, {"baseColor": POLVO, "roughness": 0.92}, opac=0.1)
    r.grunge(f, "Clouds 2", 5)
    return G


def construir():
    r = Receta("LP_Contactor", "contactor ELKVON")
    Z = r.grupo("Fondo")
    r.capa("Gris de fondo", Z, {"baseColor": "#3A3A3A", "roughness": 0.5, "metallic": 0})

    _plastico(r, "Marfil", ("Marfil", "Tinta_Negra"), "#B9B3A0", "#A8935E", ("Tinta_Negra",), "#1A1A1A")
    _plastico(r, "Grafito", ("Grafito", "Tinta_Blanca"), "#2A2C30", "#3E3D3A", ("Tinta_Blanca",), "#CFCFCA")
    _plastico(r, "Verde", ("Verde",), "#157A82", "#3F8E90")
    _plastico(r, "Naranja", ("Naranja",), "#D8641A", "#CC7A3A")

    T = r.grupo("Tornillos", clases=("Tornillo",))
    r.capa("Zincado amarillo", T, {"baseColor": "#B0AA96", "roughness": 0.32, "metallic": 1})
    f = r.capa("Tornillo: oscurecido", T, {"baseColor": "#4A463C", "roughness": 0.6}, opac=0.35)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa("Tornillo: marcas del destornillador", T, {"baseColor": "#C9C7C0", "roughness": 0.25, "metallic": 1}, opac=0.85)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.3, "Wear_Contrast": 0.7, "Grunge_Amount": 0.6, "grunge_scale": 8})
    f = r.capa("Tornillo: mugre en la cruz", T, {"baseColor": "#17140F", "roughness": 0.8, "metallic": 0}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 14)          # Dirt satura en el hueco del borne y dejaba el tornillo negro
    r.escaneo(f, 0.3, 0.5)

    K = r.grupo("Cobre", clases=("Cobre",))
    r.capa("Cobre apagado", K, {"baseColor": "#A8643C", "roughness": 0.38, "metallic": 1})
    f = r.capa("Cobre: patina parda", K, {"baseColor": "#5A3A26", "roughness": 0.6}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.45, 0.4)

    C = r.grupo("Carril DIN", clases=("Zinc",))
    r.capa("Acero zincado", C, {"baseColor": "#8E9092", "roughness": 0.4, "metallic": 1})
    f = r.capa("Zinc: flor", C, {"baseColor": "#A3A5A7", "roughness": 0.5}, opac=0.5)
    r.grunge(f, "Clouds 2", 9)
    f = r.capa("Zinc: oxido blanco", C, {"baseColor": "#B9BAB6", "roughness": 0.85, "metallic": 0, "height": 0.002}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.1, 0.8)
    f = r.capa("Zinc: roces", C, {"baseColor": "#5E5F60", "roughness": 0.3, "metallic": 1, "height": -0.002}, opac=0.7)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.15, 0.8)
    f = r.capa("Zinc: polvo", C, {"baseColor": POLVO, "roughness": 0.92, "metallic": 0}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    return r
