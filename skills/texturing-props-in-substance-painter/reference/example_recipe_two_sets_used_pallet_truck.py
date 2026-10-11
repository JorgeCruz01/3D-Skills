"""Look-dev de la transpaleta PALZUK en Substance 3D Painter. Dos sets: el chasis soldado y la mecanica.

    python ../_herramientas/sp.py rehacer Transpaleta_Manual

Aspecto: transpaleta USADA, anos de almacen (Jorge, 2026-10-10: los props que siguen a la guitarra van usados).
Chasis de chapa pintado de naranja: los palets arrastran sobre el lomo de las horquillas y dejan rayas largas hasta
el acero, las puntas estan peladas de entrar a golpes en los palets, el talon y el pie de la placa llevan golpes,
el acero que asoma ya esta pardo y la mugre negra de goma y polvo se queda en los rincones y alrededor de la bomba.
Mecanica: bomba y timon de negro con la pintura comida donde agarra la mano, aceite que suda de la bomba, vastago
cromado con pelicula de aceite, ruedas de poliuretano sucias y con cortes, rodillos de nailon grises de suelo.

Mascaras (Texturas/Bakes/Mascaras/), horneadas contra una copia de la low poly con solo las caras de cada set:
- chasis: MK_C_Pintura, MK_C_Tinta, MK_C_Otro; ZN_C_Lomo (donde arrastra el palet), ZN_C_Puntas, ZN_C_Talon, ZN_C_Bomba, ZN_C_Rodillos; CP_*_C (eje Y).
- mecanica: MK_ por material y pieza (Bomba, Timon, Negro = llantas, Poliuretano, Nailon, Acero, Balancin, Cromo,
  Palanca); ZN_Mano (lazo del timon), ZN_Fuga (cabeza de la bomba), ZN_Pie, ZN_Tubo_Bajo; CP_* (eje del timon).
"""
from sp_receta import Receta

POLVO = "#9C958A"
ACERO = "#5A544F"            # chapa que asoma, ya parda
OXIDO = "#6E3B1E"
NARANJA, NARANJA_CLARO = "#D2560B", "#E88A3C"
MUGRE = "#16120E"


def chasis():
    r = Receta("LP_Chasis", "chasis PALZUK")
    F = r.grupo("Chapa", clases=("C_Pintura", "C_Tinta", "C_Otro"))
    r.capa("Acero", F, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1})
    f = r.capa("Acero: oxido", F, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.7)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.45, 0.4)

    P = r.grupo("Pintura naranja", dentro=F, clases=("C_Pintura", "C_Tinta", "C_Otro"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.55, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8}, fusion="Multiply")
    r.capa("Esmalte naranja", P, {"baseColor": NARANJA, "roughness": 0.38, "metallic": 0, "height": 0.005})
    f = r.capa("Tono desigual", P, {"baseColor": NARANJA_CLARO, "roughness": 0.5}, opac=0.3)
    r.mapa(f, "CP_Manchas_C")
    r.escaneo(f, 0.45, 0.3)
    r.capa("Rotulos", P, {"baseColor": "#141312", "roughness": 0.5}, clases=("C_Tinta",))
    f = r.capa("Rotulos gastados", P, {"baseColor": NARANJA, "roughness": 0.45}, opac=0.8, clases=("C_Tinta",))
    r.grunge(f, "Grunge Scratches Dirty", 10)
    r.escaneo(f, 0.3, 0.6)
    f = r.capa("Brillo comido", P, {"roughness": 0.62}, opac=0.7)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Roces claros en el lomo", P, {"baseColor": NARANJA_CLARO, "roughness": 0.6, "height": -0.002}, opac=0.45)
    r.mapa(f, "CP_Rayado_Largo_C")
    r.mapa(f, "ZN_C_Lomo", fusion="Multiply")
    r.escaneo(f, 0.4, 0.5)

    # las rayas largas solo existen donde arrastra el palet: el lomo de las horquillas. En toda la chapa daban un
    # atigrado que no es de nada (primera pasada)
    f = r.capa("Rayas de palet hasta el acero", F, {"baseColor": "#8C8781", "roughness": 0.4, "metallic": 1, "height": -0.004}, opac=0.9)
    r.mapa(f, "CP_Rayado_Largo_C")
    r.mapa(f, "CP_Manchas_C", fusion="Multiply")
    r.escaneo(f, 0.2, 0.8)
    r.mapa(f, "ZN_C_Lomo", fusion="Multiply")              # la zona, DESPUES del umbral: antes, el producto no lo pasaba
    f = r.capa("Puntas peladas", F, {"baseColor": "#8C8781", "roughness": 0.36, "metallic": 1, "height": -0.005}, opac=0.95)
    r.mapa(f, "ZN_C_Puntas")
    r.grunge(f, "Grunge Dirt", 9, fusion="Multiply")
    r.escaneo(f, 0.42, 0.7)
    f = r.capa("Golpes en talon y placa", F, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1, "height": -0.006}, opac=0.95)
    r.mapa(f, "ZN_C_Talon")
    r.grunge(f, "Grunge Dirt", 7, fusion="Multiply")
    r.escaneo(f, 0.36, 0.75)
    f = r.capa("Desconchones sueltos", F, {"baseColor": ACERO, "roughness": 0.55, "metallic": 1, "height": -0.005}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 6)
    r.mapa(f, "CP_Manchas_C", fusion="Multiply")
    r.escaneo(f, 0.12, 0.85)
    f = r.capa("Oxido que mancha", F, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.mapa(f, "CP_Manchas_C", fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Mugre en rincones", F, {"baseColor": MUGRE, "roughness": 0.75}, opac=0.75)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Grasa junto a la bomba", F, {"baseColor": "#120E0A", "roughness": 0.3}, opac=0.6)
    r.mapa(f, "ZN_C_Bomba")
    r.grunge(f, "Grunge Stains Heavy", 5, fusion="Multiply")
    r.escaneo(f, 0.55, 0.4)
    f = r.capa("Negro de goma junto a los rodillos", F, {"baseColor": MUGRE, "roughness": 0.7}, opac=0.5)
    r.mapa(f, "ZN_C_Rodillos")
    r.grunge(f, "Grunge Dirt", 6, fusion="Multiply")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Polvo posado", F, {"baseColor": POLVO, "roughness": 0.95}, opac=0.16)
    r.grunge(f, "Grunge Dusty Powder Soft", 7)
    r.escaneo(f, 0.42, 0.3)
    return r


def _negro(r, G, pre, mk):
    r.capa(pre + ": acero", G, {"baseColor": ACERO, "roughness": 0.45, "metallic": 1})
    P = r.grupo(pre + ": pintura negra", dentro=G)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.5, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8}, fusion="Multiply")
    r.mapa(P, mk, fusion="LinearDodge", opac=0.55)        # un tubo de 32 mm es "todo canto" para el generador
    r.capa(pre + ": esmalte negro", P, {"baseColor": "#17181A", "roughness": 0.42, "metallic": 0, "height": 0.004})
    f = r.capa(pre + ": brillo comido", P, {"baseColor": "#26262A", "roughness": 0.62}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa(pre + ": aranazos", P, {"baseColor": "#55565A", "roughness": 0.55}, opac=0.5)
    r.grunge(f, "Grunge Scratches Dirty", 7)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.12, 0.85)


def mecanica():
    r = Receta("LP_Mecanica", "mecanica PALZUK")

    T = r.grupo("Timon", clases=("Timon",))
    _negro(r, T, "Timon", "MK_Timon")
    f = r.capa("Lazo pulido por la mano", T, {"baseColor": "#8E8A84", "roughness": 0.28, "metallic": 1, "height": -0.004}, opac=0.95)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Stains Heavy", 6, fusion="Multiply")
    r.escaneo(f, 0.6, 0.5)
    f = r.capa("Timon: desconchones abajo", T, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1, "height": -0.004}, opac=0.95)
    r.mapa(f, "ZN_Tubo_Bajo")
    r.grunge(f, "Grunge Dirt", 8, fusion="Multiply")
    r.escaneo(f, 0.36, 0.75)
    f = r.capa("Timon: oxido", T, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 9)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)

    B = r.grupo("Bomba", clases=("Bomba",))
    _negro(r, B, "Bomba", "MK_Bomba")
    f = r.capa("Bomba: aceite que suda", B, {"baseColor": "#0C0A08", "roughness": 0.16}, opac=0.75)
    r.mapa(f, "ZN_Fuga")
    r.mapa(f, "CP_Rayado_Largo", fusion="LinearDodge", opac=0.35)
    r.grunge(f, "Grunge Stains Heavy", 5, fusion="Multiply")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Bomba: mugre pegada al aceite", B, {"baseColor": "#2A231B", "roughness": 0.8}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.85})

    L = r.grupo("Llantas", clases=("Negro",))
    _negro(r, L, "Llantas", "MK_Negro")
    f = r.capa("Llantas: polvo de suelo", L, {"baseColor": POLVO, "roughness": 0.95}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.45, "dirt_contrast": 0.5, "grunge_amount": 0.8})

    U = r.grupo("Poliuretano", clases=("Poliuretano",))
    r.capa("Poliuretano ambar", U, {"baseColor": "#C7862A", "roughness": 0.46, "metallic": 0})
    f = r.capa("PU: sucio de suelo", U, {"baseColor": "#4A443C", "roughness": 0.8}, opac=0.6)       # mas y parecia madera
    r.grunge(f, "Grunge Dusty Powder Soft", 6)
    r.escaneo(f, 0.52, 0.3)
    f = r.capa("PU: cortes y picaduras", U, {"baseColor": "#D29A52", "roughness": 0.7, "height": -0.006}, opac=0.8)
    r.grunge(f, "Grunge Scratches Dirty", 9)
    r.escaneo(f, 0.14, 0.85)
    f = r.capa("PU: polvo", U, {"baseColor": POLVO, "roughness": 0.95}, opac=0.3)
    r.grunge(f, "Grunge Dusty Powder Soft", 8)

    Ny = r.grupo("Nailon", clases=("Nailon",))
    r.capa("Nailon crudo", Ny, {"baseColor": "#B9B39F", "roughness": 0.5, "metallic": 0})
    f = r.capa("Nailon: gris de suelo", Ny, {"baseColor": "#3B372F", "roughness": 0.8}, opac=0.8)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.55, 0.35)
    f = r.capa("Nailon: picaduras", Ny, {"baseColor": "#D8D3C2", "roughness": 0.65, "height": -0.005}, opac=0.7)
    r.grunge(f, "Grunge Scratches Dirty", 9)
    r.escaneo(f, 0.12, 0.85)

    A = r.grupo("Acero desnudo", clases=("Acero", "Balancin"))
    r.capa("Acero laminado", A, {"baseColor": "#6F6C68", "roughness": 0.42, "metallic": 1})
    f = r.capa("Acero: velo", A, {"roughness": 0.6}, opac=0.6)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa("Acero: oxido", A, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.65)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.4, 0.5)
    f = r.capa("Acero: mugre negra", A, {"baseColor": MUGRE, "roughness": 0.7}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.8})

    C = r.grupo("Cromo", clases=("Cromo",))
    r.capa("Cromo duro", C, {"baseColor": "#D5D6D8", "roughness": 0.1, "metallic": 1})
    f = r.capa("Cromo: pelicula de aceite", C, {"baseColor": "#8E7B5A", "roughness": 0.28}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa("Cromo: polvo pegado", C, {"baseColor": "#3A3229", "roughness": 0.8}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.5, "grunge_amount": 0.8})

    Pa = r.grupo("Palanca", clases=("Palanca", "Pintura"))
    r.capa("Palanca: acero", Pa, {"baseColor": ACERO, "roughness": 0.45, "metallic": 1})
    Pp = r.grupo("Palanca: pintura", dentro=Pa)
    r.gen(Pp, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.6, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8}, fusion="Multiply")
    r.mapa(Pp, "MK_Palanca", fusion="LinearDodge", opac=0.6)
    r.capa("Palanca: esmalte naranja", Pp, {"baseColor": NARANJA, "roughness": 0.4, "metallic": 0, "height": 0.004})
    f = r.capa("Palanca: sobada", Pp, {"baseColor": "#7A3A12", "roughness": 0.3}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)

    G2 = r.grupo("Polvo global")
    f = r.capa("Polvo fino", G2, {"baseColor": POLVO, "roughness": 0.95}, opac=0.08)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r


def construir():
    return [chasis(), mecanica()]
