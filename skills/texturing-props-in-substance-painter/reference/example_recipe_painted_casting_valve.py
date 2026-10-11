"""Look-dev de la valvula de compuerta VALDRUX DN50 en Substance 3D Painter.

    python ../_herramientas/sp.py rehacer Valvula_Compuerta

Aspecto: valvula USADA, anos en una sala de bombas (Jorge, 2026-10-10: los props que siguen a la guitarra van
usados). Fundicion pintada con epoxi azul: la pintura salta en los cantos y donde se golpea al montarla y deja ver
el hierro, que ya esta pardo; oxido que corre hacia abajo desde las juntas y los tornillos; el aro del volante
pulido al hierro por la mano. Caras mecanizadas con oxido superficial. Tornilleria zincada con velo blanco y
puntos de oxido rojo. Husillo de inox con grasa vieja. Asientos de laton con patina. Placa de aluminio rayada.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y pieza (Pintura, Volante, Mecanizado, Acero_Zinc, Inox,
Laton, Grafito, Placa, Tinta); ZN_Mano (aro del volante), ZN_Suelo (bajo de las bridas, donde apoya), ZN_Prensa
(prensaestopas y cuello: grasa y fuga), ZN_Juntas (cerco de la junta del bonete y tornillos: de ahi cae el oxido);
CP_Rayado_Largo (a lo largo de Z: chorretones) y CP_Manchas.
"""
from sp_receta import Receta

POLVO = "#A39C8E"
HIERRO = "#4B4039"          # fundicion ya parda
OXIDO = "#743F21"
AZUL, AZUL_CLARO = "#124C9E", "#4C7EC2"


def construir():
    r = Receta("LP_Valvula", "valvula VALDRUX")

    F = r.grupo("Fundicion", clases=("Pintura", "Volante"))
    r.capa("Hierro fundido", F, {"baseColor": HIERRO, "roughness": 0.62, "metallic": 1})
    f = r.capa("Hierro: oxido", F, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.8)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.5, 0.4)

    P = r.grupo("Pintura epoxi", dentro=F, clases=("Pintura", "Volante"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.5, "Wear_Contrast": 0.75, "Grunge_Amount": 0.85, "grunge_scale": 6}, fusion="Multiply")
    r.capa("Epoxi azul", P, {"baseColor": AZUL, "roughness": 0.36, "metallic": 0, "height": 0.006})
    f = r.capa("Tono desigual", P, {"baseColor": AZUL_CLARO, "roughness": 0.46}, opac=0.3)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Brillo comido", P, {"roughness": 0.58}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa("Aranazos claros", P, {"baseColor": AZUL_CLARO, "roughness": 0.55, "height": -0.003}, opac=0.6)
    r.grunge(f, "Grunge Scratches Dirty", 5)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)

    f = r.capa("Desconchones al hierro", F, {"baseColor": HIERRO, "roughness": 0.6, "metallic": 1, "height": -0.006}, opac=0.95)
    r.mapa(f, "ZN_Suelo")
    r.mapa(f, "ZN_Juntas", fusion="LinearDodge", opac=0.6)
    r.grunge(f, "Grunge Dirt", 5, fusion="Multiply")
    r.escaneo(f, 0.16, 0.8)
    f = r.capa("Desconchones sueltos", F, {"baseColor": HIERRO, "roughness": 0.6, "metallic": 1, "height": -0.006}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 4)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Volante: pulido al hierro por la mano", F, {"baseColor": "#6A5F58", "roughness": 0.34, "metallic": 1, "height": -0.004}, opac=0.95, clases=("Volante",))
    r.mapa(f, "ZN_Mano", fusion="Multiply")
    r.grunge(f, "Grunge Stains Heavy", 5, fusion="Multiply")
    r.escaneo(f, 0.5, 0.6)
    f = r.capa("Chorretones de oxido", F, {"baseColor": OXIDO, "roughness": 0.8}, opac=0.7)
    r.mapa(f, "CP_Rayado_Largo")
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Oxido en rincones", F, {"baseColor": "#5F3219", "roughness": 0.85}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.28, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Grasa del prensaestopas", F, {"baseColor": "#16110C", "roughness": 0.28}, opac=0.6)
    r.mapa(f, "ZN_Prensa")
    r.grunge(f, "Grunge Stains Heavy", 4, fusion="Multiply")
    r.escaneo(f, 0.4, 0.4)
    f = r.capa("Polvo posado", F, {"baseColor": POLVO, "roughness": 0.95}, opac=0.14)
    r.grunge(f, "Grunge Dusty Powder Soft", 5)
    r.escaneo(f, 0.42, 0.3)

    M = r.grupo("Mecanizado", clases=("Mecanizado",))
    r.capa("Acero torneado", M, {"baseColor": "#8F8D89", "roughness": 0.34, "metallic": 1})
    f = r.capa("Mecanizado: velo", M, {"roughness": 0.5}, opac=0.6)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa("Mecanizado: oxido superficial", M, {"baseColor": "#7B4A2B", "roughness": 0.82}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.34, 0.5)
    f = r.capa("Mecanizado: mugre en rincones", M, {"baseColor": "#1F1812", "roughness": 0.7}, opac=0.3)
    r.gen(f, "Dirt", {"dirt_level": 0.2, "dirt_contrast": 0.55, "grunge_amount": 0.8})

    Z = r.grupo("Tornilleria zincada", clases=("Acero_Zinc",))
    r.capa("Zincado", Z, {"baseColor": "#A3A6A9", "roughness": 0.42, "metallic": 1})
    f = r.capa("Zinc: velo blanco", Z, {"baseColor": "#D5D8D8", "roughness": 0.66}, opac=0.55)
    r.grunge(f, "Clouds 2", 9)
    f = r.capa("Zinc: oxido rojo", Z, {"baseColor": OXIDO, "roughness": 0.8}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.32, 0.6)
    f = r.capa("Zinc: mugre en rincones", Z, {"baseColor": "#2A1F15", "roughness": 0.75}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.75})

    I = r.grupo("Husillo inox", clases=("Inox",))
    r.capa("Inox", I, {"baseColor": "#C6C7C9", "roughness": 0.24, "metallic": 1})
    f = r.capa("Husillo: grasa vieja", I, {"baseColor": "#2B2118", "roughness": 0.36}, opac=0.55)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.42, 0.4)

    L = r.grupo("Laton", clases=("Laton",))
    r.capa("Laton", L, {"baseColor": "#B38C40", "roughness": 0.3, "metallic": 1})
    f = r.capa("Laton: patina", L, {"baseColor": "#5F4A23", "roughness": 0.6}, opac=0.5)
    r.grunge(f, "Clouds 2", 7)
    f = r.capa("Laton: cardenillo", L, {"baseColor": "#4F8D77", "roughness": 0.85}, opac=0.3)
    r.gen(f, "Dirt", {"dirt_level": 0.2, "dirt_contrast": 0.5, "grunge_amount": 0.8})

    G = r.grupo("Junta de grafito", clases=("Grafito",))
    r.capa("Grafito", G, {"baseColor": "#1D1D1F", "roughness": 0.5, "metallic": 0})

    A = r.grupo("Placa", clases=("Placa", "Tinta"))
    r.capa("Aluminio", A, {"baseColor": "#C4C6C7", "roughness": 0.3, "metallic": 1})
    f = r.capa("Placa: velo", A, {"roughness": 0.48}, opac=0.6)
    r.grunge(f, "Clouds 2", 8)
    r.capa("Tinta negra", A, {"baseColor": "#131315", "roughness": 0.5, "metallic": 0}, clases=("Tinta",))
    f = r.capa("Tinta gastada", A, {"baseColor": "#C4C6C7", "roughness": 0.32, "metallic": 1}, opac=0.8, clases=("Tinta",))
    r.grunge(f, "Grunge Scratches Dirty", 9)
    r.escaneo(f, 0.2, 0.6)
    f = r.capa("Placa: aranazos", A, {"baseColor": "#E0E1E1", "roughness": 0.4}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.07, 0.85)
    f = r.capa("Placa: mugre", A, {"baseColor": "#2A2219", "roughness": 0.8}, opac=0.35)
    r.gen(f, "Dirt", {"dirt_level": 0.18, "dirt_contrast": 0.55, "grunge_amount": 0.8})

    G2 = r.grupo("Polvo global")
    f = r.capa("Polvo fino", G2, {"baseColor": POLVO, "roughness": 0.95}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
