"""Look-dev del farol de queroseno LUMBREK en Substance 3D Painter. Dos sets: la chapa con sus herrajes y el globo.

    python ../_herramientas/sp.py rehacer Farol_Queroseno

Aspecto: farol USADO, anos de cuadra y de cobertizo (Jorge, 2026-10-10: los props que siguen a la guitarra van
usados). Esmalte verde azulado sobre chapa: saltado en los cantos de las estampaciones y en el aro de la base, que
es lo que se arrastra y se golpea, con el oxido ya instalado; la camara y el sombrerete, quemados por el calor
(esmalte mate y pardo) y negros de hollin en la salida de humos; cercos de queroseno alrededor del tapon y del
quemador. Laton del quemador y del tapon oscurecido, con cardenillo en los rincones y hollin en la cupula. Alambre
galvanizado gris y mate, con puntos de oxido. Mecha carbonizada en la punta. Globo con velo de hollin arriba,
polvo y cercos de dedos.

Mascaras (Texturas/Bakes/Mascaras/), horneadas contra una copia de la low poly con solo las caras de cada set:
- chapa: MK_Esmalte, MK_Laton (quemador), MK_Tapon, MK_Zinc, MK_Mecha, MK_Tinta_Negra; ZN_Hollin (sombrerete),
  ZN_Calor (camara y chimenea), ZN_Queroseno (tapon y asiento del quemador), ZN_Suelo (aro de la base),
  ZN_Mecha_Punta; CP_* a lo largo de Z.
- globo: ZN_G_Hollin (arriba), ZN_G_Base; CP_*_G. Sin clases: es una sola pieza. En Blender el color base tine la
  transmision: lo que aqui se oscurece, alli ahuma el vidrio.
"""
from sp_receta import Receta

POLVO = "#A29A8C"
CHAPA = "#514A44"
OXIDO = "#74401F"
VERDE, VERDE_CLARO = "#083E48", "#2C6E78"
HOLLIN = "#0B0A09"


def chapa():
    r = Receta("LP_Farol", "farol LUMBREK")

    F = r.grupo("Chapa esmaltada", clases=("Esmalte", "Vidrio"))
    r.capa("Chapa", F, {"baseColor": CHAPA, "roughness": 0.55, "metallic": 1})
    f = r.capa("Chapa: oxido", F, {"baseColor": OXIDO, "roughness": 0.88}, opac=0.85)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.55, 0.4)

    P = r.grupo("Esmalte", dentro=F, clases=("Esmalte", "Vidrio"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.5, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 5}, fusion="Multiply")
    r.capa("Esmalte verde azulado", P, {"baseColor": VERDE, "roughness": 0.3, "metallic": 0, "height": 0.004})
    f = r.capa("Tono desigual", P, {"baseColor": VERDE_CLARO, "roughness": 0.42}, opac=0.18)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Brillo comido", P, {"roughness": 0.56}, opac=0.7)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Quemado por el calor", P, {"baseColor": "#3A3A2C", "roughness": 0.72}, opac=0.8)
    r.grunge(f, "Clouds 2", 4)
    r.escaneo(f, 0.6, 0.35)
    r.mapa(f, "ZN_Calor", fusion="Multiply")
    f = r.capa("Aranazos claros", P, {"baseColor": VERDE_CLARO, "roughness": 0.5, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Dirty", 5)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)

    f = r.capa("Aro de la base pelado", F, {"baseColor": CHAPA, "roughness": 0.55, "metallic": 1, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.4, 0.75)
    r.mapa(f, "ZN_Suelo", fusion="Multiply")
    f = r.capa("Desconchones sueltos", F, {"baseColor": OXIDO, "roughness": 0.85, "metallic": 0, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 4)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Chorretones de oxido", F, {"baseColor": OXIDO, "roughness": 0.82}, opac=0.55)
    r.mapa(f, "CP_Rayado_Largo")
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.32, 0.5)
    f = r.capa("Oxido en rincones", F, {"baseColor": "#5C3018", "roughness": 0.88}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Cercos de queroseno", F, {"baseColor": "#2B2110", "roughness": 0.22}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.4, 0.4)
    r.mapa(f, "ZN_Queroseno", fusion="Multiply")
    f = r.capa("Hollin en la salida de humos", F, {"baseColor": HOLLIN, "roughness": 0.92}, opac=0.9)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.7, 0.3)
    r.mapa(f, "ZN_Hollin", fusion="Multiply")
    f = r.capa("Polvo posado", F, {"baseColor": POLVO, "roughness": 0.95}, opac=0.16)
    r.grunge(f, "Grunge Dusty Powder Soft", 4)
    r.escaneo(f, 0.42, 0.3)

    L = r.grupo("Laton", clases=("Laton", "Tapon", "Tinta_Negra"))
    r.capa("Laton", L, {"baseColor": "#A8843C", "roughness": 0.32, "metallic": 1})
    f = r.capa("Laton: patina oscura", L, {"baseColor": "#4E3B1C", "roughness": 0.62}, opac=0.75)
    r.grunge(f, "Clouds 2", 5)
    r.escaneo(f, 0.5, 0.3)
    # dentro del globo la oclusion es total y el generador Dirt lo llenaba entero: cupula verde palido (primera pasada)
    f = r.capa("Laton: cardenillo", L, {"baseColor": "#3E7A66", "roughness": 0.88}, opac=0.3)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.22, 0.6)
    f = r.capa("Laton: cantos pulidos por los dedos", L, {"baseColor": "#C9A452", "roughness": 0.2, "metallic": 1}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 6})
    f = r.capa("Laton: hollin de la llama", L, {"baseColor": HOLLIN, "roughness": 0.9}, opac=0.8, clases=("Laton",))
    r.mapa(f, "ZN_Mecha_Punta")
    r.capa("Rotulo grabado", L, {"baseColor": "#2A2010", "roughness": 0.6, "height": -0.003}, opac=0.9, clases=("Tinta_Negra",))

    Z = r.grupo("Alambre galvanizado", clases=("Zinc",))
    r.capa("Galvanizado", Z, {"baseColor": "#74777A", "roughness": 0.5, "metallic": 1})
    f = r.capa("Zinc: velo gris", Z, {"baseColor": "#9A9C9B", "roughness": 0.72}, opac=0.35)
    r.grunge(f, "Clouds 2", 10)
    f = r.capa("Zinc: oxido", Z, {"baseColor": "#5E3319", "roughness": 0.85}, opac=0.8)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.3, 0.6)

    M = r.grupo("Mecha", clases=("Mecha",))
    r.capa("Algodon", M, {"baseColor": "#B9AF94", "roughness": 0.95, "metallic": 0})
    f = r.capa("Mecha: empapada", M, {"baseColor": "#7A6B45", "roughness": 0.7}, opac=0.6)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa("Mecha: carbonizada", M, {"baseColor": HOLLIN, "roughness": 0.95}, opac=0.95)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.35, 0.3)

    G2 = r.grupo("Polvo global")
    f = r.capa("Polvo fino", G2, {"baseColor": POLVO, "roughness": 0.95}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r


def globo():
    r = Receta("LP_Globo", "globo de vidrio")
    V = r.grupo("Vidrio")
    r.capa("Vidrio", V, {"baseColor": "#EEF3F1", "roughness": 0.04, "metallic": 0})
    f = r.capa("Velo de polvo", V, {"baseColor": "#D9D6CC", "roughness": 0.32}, opac=0.5)
    r.grunge(f, "Grunge Dusty Powder Soft", 3)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Cercos y dedos", V, {"roughness": 0.22}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 3)
    r.escaneo(f, 0.4, 0.4)
    f = r.capa("Hollin arriba", V, {"baseColor": "#8A8172", "roughness": 0.34}, opac=0.55)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.65, 0.3)
    r.mapa(f, "ZN_G_Hollin", fusion="Multiply")
    f = r.capa("Polvo abajo", V, {"baseColor": "#C9C3B4", "roughness": 0.5}, opac=0.5)
    r.mapa(f, "ZN_G_Base")
    return r


def construir():
    return [chapa(), globo()]
