"""Look-dev del taladro DRUVAK en Substance 3D Painter.

    python ../_herramientas/sp.py rehacer Taladro_Percutor

Aspecto: taladro de obra USADO (Jorge, 2026-10-10: los props que siguen a la guitarra van usados). Carcasa de ABS
verde azulado con el brillo comido donde se apoya y se agarra, aranazos claros a lo largo, polvo de obra en las
ranuras y mugre oscura en la empunadura. Goma negra con polvo en los hoyuelos y la cresta pulida por la mano.
Portabrocas de acero pavonado con el moleteado gastado hasta el metal; broca de nitruro de titanio con el filo
ya en acero. Bateria de grafito con la base rayada de dejarla en el suelo. Tornillos de oxido negro.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y pieza; ZN_Agarre, ZN_Gatillo, ZN_Suelo (base de la
bateria), ZN_Morro (portabrocas y collar), ZN_Apoyo (trasera, costados y lomo de la cabeza: donde roza al dejarlo
tumbado); CP_Relieve_Canto / _Hueco (hoyuelos de la goma, moleteado, grano del plastico); CP_Rayado_Largo (a lo
largo del husillo) y CP_Manchas.
"""
from sp_receta import Receta

POLVO = "#B8B1A2"          # polvo de yeso y hormigon


def plastico(r, G, base, claro, rug=0.36):
    r.capa("Base", G, {"baseColor": base, "roughness": rug, "metallic": 0})
    f = r.capa("Tono desigual", G, {"baseColor": claro, "roughness": rug + 0.08}, opac=0.25)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Brillo comido donde roza", G, {"roughness": rug + 0.2}, opac=0.6)
    r.mapa(f, "ZN_Apoyo")
    r.mapa(f, "ZN_Suelo", fusion="LinearDodge")
    r.grunge(f, "Grunge Scratches Dirty", 5, fusion="Multiply")
    r.escaneo(f, 0.4, 0.4)
    f = r.capa("Aranazos claros", G, {"baseColor": claro, "roughness": rug + 0.18, "height": -0.004}, opac=0.7)
    r.mapa(f, "CP_Rayado_Largo")
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Canto blanquecino", G, {"baseColor": claro, "roughness": rug + 0.15}, opac=0.45)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.25, "Wear_Contrast": 0.7, "Grunge_Amount": 0.85, "grunge_scale": 7})
    f = r.capa("Golpes", G, {"baseColor": claro, "roughness": rug + 0.25, "height": -0.008}, opac=0.7)
    r.mapa(f, "ZN_Apoyo")
    r.mapa(f, "ZN_Suelo", fusion="LinearDodge")
    r.grunge(f, "Grunge Dirt", 7, fusion="Multiply")
    r.escaneo(f, 0.12, 0.6)
    f = r.capa("Polvo de obra en ranuras", G, {"baseColor": POLVO, "roughness": 0.95}, opac=0.45)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.8})
    f = r.capa("Polvo posado", G, {"baseColor": POLVO, "roughness": 0.95}, opac=0.14)
    r.grunge(f, "Grunge Dusty Powder Soft", 5)
    r.escaneo(f, 0.42, 0.3)


def construir():
    r = Receta("LP_Taladro", "taladro DRUVAK")
    C = r.grupo("Carcasa", clases=("Carcasa",))
    plastico(r, C, "#0A7780", "#4FA9AE", 0.34)
    f = r.capa("Mugre de la mano", C, {"baseColor": "#0A2E33", "roughness": 0.3}, opac=0.5)
    r.mapa(f, "ZN_Agarre")
    r.mapa(f, "ZN_Gatillo", fusion="LinearDodge")
    r.grunge(f, "Grunge Stains Heavy", 4, fusion="Multiply")
    r.escaneo(f, 0.4, 0.35)

    G = r.grupo("Grafito", clases=("Grafito", "Bateria", "Collar", "Inversor", "Tinta_Blanca", "Tinta_Naranja"))
    plastico(r, G, "#2B2C2F", "#77777A", 0.4)
    f = r.capa("Base rayada de la bateria", G, {"baseColor": "#8A8A88", "roughness": 0.6, "height": -0.005}, opac=0.8, clases=("Bateria",))
    r.mapa(f, "ZN_Suelo", fusion="Multiply")
    r.grunge(f, "Grunge Scratches Dirty", 4, fusion="Multiply")
    r.escaneo(f, 0.22, 0.6)
    r.capa("Rotulos blancos", G, {"baseColor": "#D9D7CF", "roughness": 0.5}, clases=("Tinta_Blanca",))
    r.capa("Rotulo naranja", G, {"baseColor": "#DE6A1C", "roughness": 0.5}, clases=("Tinta_Naranja",))
    f = r.capa("Rotulos gastados", G, {"baseColor": "#2B2C2F", "roughness": 0.45}, opac=0.75, clases=("Tinta_Blanca", "Tinta_Naranja"))
    r.grunge(f, "Grunge Scratches Dirty", 9, fusion="Multiply")
    r.escaneo(f, 0.28, 0.5)
    f = r.capa("Rotulos: polvo", G, {"baseColor": POLVO, "roughness": 0.9}, opac=0.25, clases=("Tinta_Blanca", "Tinta_Naranja"))
    r.grunge(f, "Grunge Dusty Powder Soft", 8, fusion="Multiply")

    A = r.grupo("Acento naranja", clases=("Acento",))
    plastico(r, A, "#E2641A", "#F2A268", 0.38)

    K = r.grupo("Goma", clases=("Goma", "Gatillo"))
    r.capa("Goma negra", K, {"baseColor": "#151617", "roughness": 0.62, "metallic": 0})
    f = r.capa("Goma: cresta pulida por la mano", K, {"baseColor": "#0D0D0E", "roughness": 0.34}, opac=0.7)
    r.mapa(f, "ZN_Agarre")
    r.mapa(f, "ZN_Gatillo", fusion="LinearDodge")
    r.mapa(f, "CP_Relieve_Canto", fusion="Multiply")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Goma: polvo en los hoyuelos", K, {"baseColor": POLVO, "roughness": 0.95}, opac=0.6)
    r.mapa(f, "CP_Relieve_Hueco")
    r.grunge(f, "Grunge Dusty Powder Soft", 4, fusion="Multiply")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Goma: polvo en rincones", K, {"baseColor": POLVO, "roughness": 0.95}, opac=0.3)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.8})
    f = r.capa("Goma: rozaduras", K, {"baseColor": "#3A3A3B", "roughness": 0.7}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.07, 0.85)

    P = r.grupo("Portabrocas", clases=("Porta",))
    r.capa("Acero", P, {"baseColor": "#B4B5B8", "roughness": 0.3, "metallic": 1})
    PV = r.grupo("Pavonado", dentro=P, clases=("Porta",))
    r.gen(PV, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.5, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8}, fusion="Multiply")
    r.capa("Oxido negro", PV, {"baseColor": "#1B1C1F", "roughness": 0.42, "metallic": 1})
    f = r.capa("Pavonado: pulido por la mano", PV, {"baseColor": "#2A2B2E", "roughness": 0.28}, opac=0.6)
    r.mapa(f, "ZN_Morro")
    r.grunge(f, "Grunge Fingerprints Smeared", 6, fusion="Multiply")
    f = r.capa("Portabrocas: mugre en el moleteado", P, {"baseColor": "#141210", "roughness": 0.75}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.35, "dirt_contrast": 0.55, "grunge_amount": 0.75})
    f = r.capa("Portabrocas: polvo", P, {"baseColor": POLVO, "roughness": 0.95}, opac=0.25)
    r.mapa(f, "CP_Relieve_Hueco")
    r.grunge(f, "Grunge Dusty Powder Soft", 6, fusion="Multiply")

    S = r.grupo("Acero", clases=("Acero", "Mordaza", "Clip"))
    r.capa("Acero zincado", S, {"baseColor": "#C6C7CA", "roughness": 0.26, "metallic": 1})
    f = r.capa("Acero: velo", S, {"roughness": 0.42}, opac=0.6)
    r.grunge(f, "Clouds 2", 7)
    f = r.capa("Acero: aranazos", S, {"baseColor": "#A9AAAD", "roughness": 0.4}, opac=0.7)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.12, 0.85)
    f = r.capa("Acero: picaduras de oxido", S, {"baseColor": "#6B4A30", "roughness": 0.7}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.12, 0.6)
    f = r.capa("Acero: mugre en rincones", S, {"baseColor": "#1E1A15", "roughness": 0.7}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.75})

    B = r.grupo("Broca", clases=("Broca",))
    r.capa("Acero rapido", B, {"baseColor": "#B9BABD", "roughness": 0.28, "metallic": 1})
    TN = r.grupo("Nitruro de titanio", dentro=B, clases=("Broca",))
    r.gen(TN, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.55, "Wear_Contrast": 0.6, "Grunge_Amount": 0.7, "grunge_scale": 8}, fusion="Multiply")
    r.mapa(TN, "MK_Broca", fusion="LinearDodge", opac=0.55)          # para el generador, una broca de 8 mm es todo canto
    r.capa("TiN dorado", TN, {"baseColor": "#B98A2C", "roughness": 0.3, "metallic": 1})
    f = r.capa("Broca: polvo en los canales", B, {"baseColor": POLVO, "roughness": 0.95}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.8})

    T = r.grupo("Tornillos", clases=("Tornillo",))
    r.capa("Oxido negro", T, {"baseColor": "#1A1A1C", "roughness": 0.4, "metallic": 1})
    f = r.capa("Tornillo: canto al acero", T, {"baseColor": "#A8A9AC", "roughness": 0.3, "metallic": 1}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.35, "Wear_Contrast": 0.7, "Grunge_Amount": 0.6, "grunge_scale": 8})
    f = r.capa("Tornillo: polvo en la cruz", T, {"baseColor": POLVO, "roughness": 0.95}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.7})

    L = r.grupo("Lente del led", clases=("Lente",))
    r.capa("Policarbonato", L, {"baseColor": "#D6D9D0", "roughness": 0.16, "metallic": 0})
    f = r.capa("Lente: polvo", L, {"baseColor": POLVO, "roughness": 0.9}, opac=0.35)
    r.grunge(f, "Grunge Dusty Powder Soft", 8)

    G2 = r.grupo("Polvo global")
    f = r.capa("Polvo fino", G2, {"baseColor": POLVO, "roughness": 0.95}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
