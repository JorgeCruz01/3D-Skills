"""Look-dev del casco de seguridad BRUNDEK en Substance 3D Painter. Dos sets: el casco con sus accesorios y el visor.

    python ../_herramientas/sp.py rehacer Casco_Seguridad

Aspecto: casco USADO, de obra (Jorge, 2026-10-10: los props que siguen a la guitarra van usados). La carcasa es
polietileno amarillo teñido en masa: no se desconcha, se RAYA. Las rayas son mas claras y mates que el plastico (el
polimero blanquea donde se estira), se concentran en la coronilla y en el canto del ala, y la mugre de las manos
queda en el ala y en la nuca, que es por donde se coge. Polvo de obra en la banda, en las ranuras y en los rincones.
Rotulos de tampografia medio borrados. Copas de las orejeras de ABS negro con roces grises; almohadillas de vinilo
con polvo en los pliegues; arnes de polietileno crudo ya gris; banda de sudor oscurecida en la frente; cintas
sucias; alambre de las horquillas con el zincado mate. Visor de policarbonato con rayas finas, velo y polvo abajo.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material (Carcasa, Arnes, Sudor, Plastico_Negro, Cinta, Copa,
Almohadilla, Alambre, Tinta); ZN_Cima, ZN_Ala, ZN_Nuca, ZN_Frente, ZN_Copa; CP_* (eje Y). Visor: ZN_V_Bajo,
ZN_V_Mano, CP_*_V. En Blender el color base del visor tine la transmision.
"""
from sp_receta import Receta

POLVO = "#B0A794"
AMARILLO, AMARILLO_CLARO = "#E0A106", "#F1CE62"
MUGRE = "#2A2219"


def casco():
    r = Receta("LP_Casco", "casco BRUNDEK")

    C = r.grupo("Carcasa", clases=("Carcasa", "Tinta"))
    r.capa("Polietileno amarillo", C, {"baseColor": AMARILLO, "roughness": 0.34, "metallic": 0})
    f = r.capa("Tono desigual", C, {"baseColor": "#C98B05", "roughness": 0.42}, opac=0.25)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    r.capa("Rotulos", C, {"baseColor": "#151413", "roughness": 0.5}, clases=("Tinta",))
    f = r.capa("Rotulos medio borrados", C, {"baseColor": AMARILLO, "roughness": 0.4}, opac=0.85, clases=("Tinta",))
    r.grunge(f, "Grunge Scratches Dirty", 8)
    r.escaneo(f, 0.36, 0.6)
    f = r.capa("Brillo comido", C, {"roughness": 0.58}, opac=0.75)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Rayas finas por todo", C, {"baseColor": AMARILLO_CLARO, "roughness": 0.62, "height": -0.002}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Rayas de la coronilla", C, {"baseColor": "#F4DA8A", "roughness": 0.7, "height": -0.004}, opac=0.85)
    r.grunge(f, "Grunge Scratches Dirty", 5)
    r.escaneo(f, 0.22, 0.8)
    r.mapa(f, "ZN_Cima", fusion="Multiply")
    f = r.capa("Cantos blanqueados", C, {"baseColor": "#F2D680", "roughness": 0.66}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.32, "Wear_Contrast": 0.6, "Grunge_Amount": 0.85, "grunge_scale": 6})
    f = r.capa("Mugre de las manos", C, {"baseColor": MUGRE, "roughness": 0.62}, opac=0.55)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.42, 0.4)
    r.mapa(f, "ZN_Ala", fusion="Multiply")
    r.mapa(f, "ZN_Nuca", fusion="LinearDodge", opac=0.5)
    f = r.capa("Mugre en rincones y ranuras", C, {"baseColor": "#3A2E20", "roughness": 0.8}, opac=0.55)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Polvo de obra", C, {"baseColor": POLVO, "roughness": 0.95}, opac=0.3)
    r.grunge(f, "Grunge Dusty Powder Soft", 4)
    r.escaneo(f, 0.45, 0.3)

    N = r.grupo("Plastico negro", clases=("Plastico_Negro", "Copa", "Visor"))       # Visor: el aro de la careta visto a traves del visor
    r.capa("ABS negro", N, {"baseColor": "#141416", "roughness": 0.4, "metallic": 0})
    f = r.capa("Negro: brillo desigual", N, {"roughness": 0.6}, opac=0.7)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.42, 0.4)
    # `Grunge Scratches Dirty` umbralizado a 0.14 no da rayas: da manchas (las copas salian salpicadas). Rayas finas.
    f = r.capa("Negro: roces grises", N, {"baseColor": "#5C5C5E", "roughness": 0.66, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Copa: rozada", N, {"baseColor": "#4A4A4C", "roughness": 0.7}, opac=0.45, clases=("Copa",))
    r.grunge(f, "Clouds 2", 6)
    r.escaneo(f, 0.55, 0.4)
    r.mapa(f, "ZN_Copa", fusion="Multiply")
    f = r.capa("Negro: cantos gastados", N, {"baseColor": "#4A4A4C", "roughness": 0.55}, opac=0.6)
    # en una copa lisa y abombada el generador de cantos con mucho grunge no encuentra cantos y reparte manchas
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.1, "Wear_Contrast": 0.8, "Grunge_Amount": 0.25, "grunge_scale": 7})
    # polvo claro umbralizado (Dirt o `Grunge Dusty Powder Soft`, que llevan el mismo grunge) sobre negro liso se lee como
    # salpicaduras de pintura: tres pasadas iguales hasta medirlo. Sobre negro, un velo sin umbral y poco
    f = r.capa("Negro: polvo", N, {"baseColor": "#6E685C", "roughness": 0.9}, opac=0.12)
    r.grunge(f, "Clouds 2", 9)

    A = r.grupo("Almohadilla", clases=("Almohadilla",))
    r.capa("Vinilo negro", A, {"baseColor": "#1A1A1C", "roughness": 0.5, "metallic": 0})
    f = r.capa("Vinilo: brillo de uso", A, {"roughness": 0.32}, opac=0.5)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa("Vinilo: polvo en pliegues", A, {"baseColor": POLVO, "roughness": 0.95}, opac=0.45)
    r.grunge(f, "Grunge Dusty Powder Soft", 6)
    r.escaneo(f, 0.4, 0.3)

    H = r.grupo("Arnes", clases=("Arnes",))
    r.capa("Polietileno crudo", H, {"baseColor": "#BDBBB2", "roughness": 0.5, "metallic": 0})
    f = r.capa("Arnes: gris de uso", H, {"baseColor": "#5B554B", "roughness": 0.7}, opac=0.55)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.45, 0.35)
    f = r.capa("Arnes: mugre", H, {"baseColor": MUGRE, "roughness": 0.8}, opac=0.3)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.3, 0.5)

    S = r.grupo("Banda de sudor", clases=("Sudor",))
    r.capa("Rizo gris azulado", S, {"baseColor": "#3D4350", "roughness": 0.95, "metallic": 0})
    f = r.capa("Sudor: pelusa", S, {"baseColor": "#5A6070", "roughness": 0.95, "height": 0.003}, opac=0.6)
    r.grunge(f, "Grunge Dusty Powder Soft", 14)
    f = r.capa("Sudor: cerco de la frente", S, {"baseColor": "#20201F", "roughness": 0.8}, opac=0.75)
    r.grunge(f, "Clouds 2", 5)
    r.escaneo(f, 0.6, 0.3)
    r.mapa(f, "ZN_Frente", fusion="Multiply")
    f = r.capa("Sudor: sal", S, {"baseColor": "#8C8F92", "roughness": 0.9}, opac=0.3)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.3, 0.5)

    T = r.grupo("Cintas", clases=("Cinta",))
    r.capa("Cinta de poliester", T, {"baseColor": "#8C8A80", "roughness": 0.9, "metallic": 0})
    f = r.capa("Cinta: sucia", T, {"baseColor": "#3C362C", "roughness": 0.9}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.5, 0.35)

    W = r.grupo("Alambre", clases=("Alambre",))
    r.capa("Acero zincado", W, {"baseColor": "#9A9DA0", "roughness": 0.4, "metallic": 1})
    f = r.capa("Alambre: mate", W, {"baseColor": "#77797B", "roughness": 0.66}, opac=0.6)
    r.grunge(f, "Clouds 2", 10)
    f = r.capa("Alambre: oxido", W, {"baseColor": "#5E3319", "roughness": 0.85}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.25, 0.6)

    G2 = r.grupo("Polvo global")
    f = r.capa("Polvo fino", G2, {"baseColor": POLVO, "roughness": 0.95}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r


def visor():
    r = Receta("LP_Visor", "visor de policarbonato")
    V = r.grupo("Policarbonato")
    r.capa("Policarbonato", V, {"baseColor": "#EEF2F3", "roughness": 0.05, "metallic": 0})
    f = r.capa("Velo", V, {"baseColor": "#DCDDD8", "roughness": 0.24}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 3)
    r.escaneo(f, 0.42, 0.35)
    f = r.capa("Rayas finas", V, {"baseColor": "#D2D3D0", "roughness": 0.4}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.12, 0.85)
    f = r.capa("Rayas de limpiarlo", V, {"baseColor": "#D0D1CE", "roughness": 0.36}, opac=0.5)
    r.mapa(f, "CP_Rayado_Largo_V")
    r.mapa(f, "CP_Manchas_V", fusion="Multiply")
    r.escaneo(f, 0.25, 0.7)
    f = r.capa("Dedos en los cantos", V, {"baseColor": "#D8D7D0", "roughness": 0.26}, opac=0.3)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.4, 0.4)
    r.mapa(f, "ZN_V_Mano", fusion="Multiply")
    f = r.capa("Polvo abajo", V, {"baseColor": "#BDB6A4", "roughness": 0.55}, opac=0.55)
    r.grunge(f, "Grunge Dusty Powder Soft", 3)
    r.escaneo(f, 0.4, 0.3)
    r.mapa(f, "ZN_V_Bajo", fusion="Multiply")
    return r


def construir():
    return [casco(), visor()]
