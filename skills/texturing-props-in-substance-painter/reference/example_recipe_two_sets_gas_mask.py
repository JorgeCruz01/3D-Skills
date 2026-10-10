"""Look-dev de la mascara NERVOK en Substance 3D Painter. Dos sets: la mascara y el busto de exhibicion.

    python ../_herramientas/sp.py rehacer Mascara_Antigas

Aspecto: mascara de dotacion con anos de almacen y uso. La goma de butilo es negra y satinada, con el velo gris de
cera que le sale a la goma vieja en los huecos, brillo donde se la agarra (reborde del modulo, nariz, aros) y polvo
claro en los rincones. El modulo frontal y las hebillas son de plastico duro, mas negro y mas liso. Los oculares son
cristal ahumado con huellas y polvo. El filtro es un bote de aluminio pintado de verde oliva: la pintura salta en
los cantos y deja ver el metal, y lleva los rotulos estarcidos en crema. Las cintas son elastico negro tejido, con
el canutillo mas claro y el canto deshilachado. El busto es resina pintada de blanco roto, con roces.

Mascaras (Texturas/Bakes/Mascaras/, horneadas contra la parte de la mascara antes de unirla al busto): MK_ por
material y por pieza; ZN_Agarre (bote del filtro y toma de bebida) y ZN_Roce (reborde del modulo, cara del filtro,
nariz, aros); CP_Relieve_Canto / _Hueco, tejido de la cinta; CP_Manchas, CP_Rayado_Largo (vertical).
El set del busto no usa mascaras horneadas: solo generadores.
"""
from sp_receta import Receta

GOMA = ("Goma_Negra", "Aro", "Oreja", "Almohadilla", "Collar", "Bebida", "Busto")      # "Busto": caras interiores que dan al busto
DURO = ("Modulo", "Fonica", "Hebilla")


def goma(r):
    G = r.grupo("Goma", clases=GOMA)
    r.capa("Butilo negro", G, {"baseColor": "#0F0F10", "roughness": 0.46, "metallic": 0})
    f = r.capa("Goma: tono desigual", G, {"baseColor": "#19191A", "roughness": 0.56}, opac=0.4)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Goma: velo de cera en huecos", G, {"baseColor": "#5B5C5C", "roughness": 0.78}, opac=0.16)
    r.gen(f, "Dirt", {"dirt_level": 0.5, "dirt_contrast": 0.45, "grunge_amount": 0.75})
    f = r.capa("Goma: velo en manchas", G, {"baseColor": "#3A3B3C", "roughness": 0.68}, opac=0.1)
    r.grunge(f, "Grunge Stains Heavy", 3)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.4, 0.35)
    f = r.capa("Goma: escurridos", G, {"baseColor": "#242526", "roughness": 0.62}, opac=0.2)
    r.grunge(f, "Grunge Leak Small", 4)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Goma: brillo de agarre", G, {"baseColor": "#0E0E0F", "roughness": 0.26}, opac=0.6)
    r.mapa(f, "ZN_Roce")
    r.mapa(f, "ZN_Agarre", fusion="LinearDodge")
    r.grunge(f, "Grunge Fingerprints Smeared", 5, fusion="Multiply")
    r.escaneo(f, 0.45, 0.35)
    f = r.capa("Goma: canto pulido", G, {"baseColor": "#1B1B1C", "roughness": 0.3}, opac=0.45)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.32, "Wear_Contrast": 0.5, "Grunge_Amount": 0.7, "grunge_scale": 6})
    f = r.capa("Goma: rozaduras", G, {"baseColor": "#2C2C2D", "roughness": 0.7, "height": -0.003}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.07, 0.85)
    f = r.capa("Goma: polvo en rincones", G, {"baseColor": "#8A8372", "roughness": 0.95}, opac=0.1)
    r.gen(f, "Dirt", {"dirt_level": 0.36, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    r.capa("Aros: goma mas gris", G, {"baseColor": "#1B1C1D", "roughness": 0.52}, opac=0.5, clases=("Aro",))


def duro(r):
    P = r.grupo("Plastico duro", clases=DURO)
    r.capa("Plastico negro", P, {"baseColor": "#0F0F10", "roughness": 0.34, "metallic": 0})
    f = r.capa("Plastico: velo mate", P, {"baseColor": "#1C1C1D", "roughness": 0.55}, opac=0.5)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa("Plastico: canto blanquecino", P, {"baseColor": "#595957", "roughness": 0.5}, opac=0.3)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.3, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8})
    f = r.capa("Plastico: aranazos", P, {"baseColor": "#454543", "roughness": 0.6, "height": -0.003}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.08, 0.85)
    f = r.capa("Plastico: brillo de dedos", P, {"roughness": 0.2}, opac=0.5)
    r.mapa(f, "ZN_Roce")
    r.grunge(f, "Grunge Fingerprints Smeared", 6, fusion="Multiply")
    # el modulo es un pozo: el generador se satura dentro y lo rellena de beige si pasa de 0.2
    f = r.capa("Plastico: polvo en huecos", P, {"baseColor": "#8A8372", "roughness": 0.95}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.5, "grunge_amount": 0.85})


def lentes(r):
    L = r.grupo("Oculares", clases=("Lente",))
    r.capa("Cristal ahumado", L, {"baseColor": "#0B0A08", "roughness": 0.05, "metallic": 0})
    f = r.capa("Cristal: huellas", L, {"roughness": 0.24}, opac=0.5)
    r.grunge(f, "Grunge Fingerprints Smeared", 4)
    r.escaneo(f, 0.4, 0.4)
    f = r.capa("Cristal: polvo", L, {"baseColor": "#55524B", "roughness": 0.6}, opac=0.08)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Cristal: polvo junto al aro", L, {"baseColor": "#8A8372", "roughness": 0.9}, opac=0.3)
    r.gen(f, "Dirt", {"dirt_level": 0.12, "dirt_contrast": 0.5, "grunge_amount": 0.7})
    f = r.capa("Cristal: aranazos", L, {"baseColor": "#24231F", "roughness": 0.4}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.03, 0.9)


def filtro(r):
    A = r.grupo("Filtro", clases=("Filtro", "Tinta"))
    r.capa("Aluminio", A, {"baseColor": "#B9BABC", "roughness": 0.36, "metallic": 1})
    f = r.capa("Aluminio: oxido blanco", A, {"baseColor": "#9A9B9A", "roughness": 0.62}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 6)
    R = r.grupo("Pintura", dentro=A, clases=("Filtro", "Tinta"))
    r.gen(R, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.55, "Wear_Contrast": 0.75, "Grunge_Amount": 0.85, "grunge_scale": 7},
          fusion="Multiply")
    r.capa("Esmalte oliva", R, {"baseColor": "#4B5335", "roughness": 0.5, "metallic": 0})
    f = r.capa("Esmalte: tono desigual", R, {"baseColor": "#3D452B", "roughness": 0.58}, opac=0.5)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Esmalte: decolorado", R, {"baseColor": "#6A7150", "roughness": 0.62}, opac=0.4)
    r.grunge(f, "Clouds 2", 4)
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Esmalte: pulido de la mano", R, {"roughness": 0.3}, opac=0.55)
    r.mapa(f, "ZN_Agarre")
    r.grunge(f, "Grunge Fingerprints Smeared", 5, fusion="Multiply")
    r.capa("Rotulos estarcidos", R, {"baseColor": "#D6D1BE", "roughness": 0.55, "metallic": 0}, clases=("Tinta",))
    f = r.capa("Rotulos: tinta gastada", R, {"baseColor": "#4B5335", "roughness": 0.5}, opac=0.7, clases=("Tinta",))
    r.grunge(f, "Grunge Scratches Dirty", 8, fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Filtro: aranazos al metal", A, {"baseColor": "#C4C5C7", "roughness": 0.3, "metallic": 1}, opac=0.8)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.05, 0.9)
    f = r.capa("Filtro: mugre en ranuras", A, {"baseColor": "#1E1D17", "roughness": 0.85}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.42, "dirt_contrast": 0.55, "grunge_amount": 0.7})
    f = r.capa("Filtro: polvo", A, {"baseColor": "#8A8372", "roughness": 0.95}, opac=0.2)
    r.grunge(f, "Grunge Dusty Powder Soft", 5)
    r.escaneo(f, 0.4, 0.3)


def cintas(r):
    C = r.grupo("Cintas", clases=("Cinta",))
    r.capa("Elastico negro", C, {"baseColor": "#1A1A1C", "roughness": 0.82, "metallic": 0})
    f = r.capa("Cinta: canutillo claro", C, {"baseColor": "#37373A", "roughness": 0.7}, opac=0.6)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.5, 0.35)
    f = r.capa("Cinta: fondo del tejido", C, {"baseColor": "#09090A", "roughness": 0.9}, opac=0.6)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.55, 0.35)
    f = r.capa("Cinta: desteñida", C, {"baseColor": "#252524", "roughness": 0.88}, opac=0.3)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Cinta: pelusa y polvo", C, {"baseColor": "#7C776B", "roughness": 0.95}, opac=0.1)
    r.grunge(f, "Grunge Dusty Powder Soft", 9)
    r.escaneo(f, 0.42, 0.3)
    f = r.capa("Cinta: brillo junto a la hebilla", C, {"roughness": 0.5}, opac=0.5)
    r.mapa(f, "HL_Hebilla")


def mascara():
    r = Receta("LP_Mascara", "mascara NERVOK")
    goma(r)
    duro(r)
    lentes(r)
    filtro(r)
    cintas(r)
    S = r.grupo("Polvo global")
    f = r.capa("Polvo fino", S, {"baseColor": "#8E8777", "roughness": 0.95}, opac=0.05)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r


def busto():
    r = Receta("LP_Busto", "busto de exhibicion")
    B = r.grupo("Resina pintada")
    r.capa("Blanco roto", B, {"baseColor": "#D8D5CD", "roughness": 0.56, "metallic": 0})
    f = r.capa("Pintura: tono desigual", B, {"baseColor": "#C6C2B8", "roughness": 0.64}, opac=0.5)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Pintura: piel de naranja", B, {"height": 0.002, "roughness": 0.5}, opac=0.5)
    r.grunge(f, "Grunge Dusty Powder Soft", 18)
    f = r.capa("Roces grises", B, {"baseColor": "#8F8C86", "roughness": 0.7}, opac=0.5)
    r.grunge(f, "Grunge Scratches Dirty", 4)
    r.escaneo(f, 0.12, 0.7)
    f = r.capa("Desconchones en el canto", B, {"baseColor": "#A39C8C", "roughness": 0.8, "height": -0.004}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.22, "Wear_Contrast": 0.8, "Grunge_Amount": 0.9, "grunge_scale": 6})
    f = r.capa("Marcas de goma negra", B, {"baseColor": "#3A3A3A", "roughness": 0.6}, opac=0.35)
    r.grunge(f, "Grunge Leak Small", 3)
    r.escaneo(f, 0.2, 0.5)
    f = r.capa("Mugre en rincones", B, {"baseColor": "#6F6A5E", "roughness": 0.9}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    f = r.capa("Huellas", B, {"baseColor": "#B4AFA3", "roughness": 0.38}, opac=0.4)
    r.grunge(f, "Grunge Fingerprints Smeared", 3)
    r.escaneo(f, 0.4, 0.4)
    return r


def construir():
    return [mascara(), busto()]
