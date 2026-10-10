"""Look-dev de la mochila KORVANT en Substance 3D Painter.

    python ../_herramientas/sp.py rehacer Mochila_Tactica

Aspecto: mochila de asalto de cordura coyote con un par de temporadas de uso. La tela conserva el tejido horneado
(relieve del high poly) y gana lo que una tela usada tiene: hilo mas claro en las crestas y mas oscuro en el fondo
de la trama, decoloracion por sol arriba y en la cara de los bolsillos, tierra seca en el tercio de abajo, roce
blanquecino en las esquinas, manchas de sudor y grasa en la espalda, hombreras y asa. La cincha y los ribetes son
de nailon oliva, mas oscuros que la tela, con el canto deshilachado mas claro; el plastico de las hebillas es
negro satinado con el canto blanquecino del roce; la cremallera es de espiral negra con cursores de zamak pintado.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y por pieza; ZN_ zonas (Mano, Suelo, Espalda, Sol, Roce);
CP_Relieve_Canto / _Hueco, crestas y fondos del tejido horneado; CP_Manchas y CP_Rayado_Largo en vertical (el agua
y la tierra escurren hacia abajo).
"""
from sp_receta import Receta

SET = "LP_Mochila"
TELA = ("Cordura", "Velcro")
ACOLCHADO = ("Hombreras", "Malla")
NAILON = ("Cincha", "Ribete", "Asa", "Cinta_Cremallera", "Cordon")
DUROS = ("Plastico",)


def tela(r):
    T = r.grupo("Cordura", clases=TELA)
    r.capa("Cordura coyote", T, {"baseColor": "#8A6744", "roughness": 0.82, "metallic": 0})
    f = r.capa("Trama: hilo claro en la cresta", T, {"baseColor": "#A8855C", "roughness": 0.74}, opac=0.55)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.5, 0.35)
    f = r.capa("Trama: fondo oscuro", T, {"baseColor": "#4E3824", "roughness": 0.9}, opac=0.6)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.55, 0.35)
    f = r.capa("Tinte desigual", T, {"baseColor": "#735232"}, opac=0.45)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Sol: decoloracion", T, {"baseColor": "#B39A78", "roughness": 0.86}, opac=0.5)
    r.mapa(f, "ZN_Sol")
    r.grunge(f, "Clouds 2", 3, fusion="Multiply")
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Roce en esquinas: hilo pelado", T, {"baseColor": "#C2AD8E", "roughness": 0.7, "height": 0.004}, opac=0.6)
    r.mapa(f, "ZN_Roce")
    r.grunge(f, "Grunge Scratches Dirty", 6, fusion="Multiply")
    r.escaneo(f, 0.35, 0.4)
    f = r.capa("Pliegues: canto gastado", T, {"baseColor": "#A88C66", "roughness": 0.76}, opac=0.4)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.3, "Wear_Contrast": 0.5, "Grunge_Amount": 0.9, "grunge_scale": 6})
    f = r.capa("Suciedad en pliegues y costuras", T, {"baseColor": "#3A2A1A", "roughness": 0.9}, opac=0.55)
    r.gen(f, "Dirt", {"dirt_level": 0.42, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    f = r.capa("Espalda: sudor y grasa", T, {"baseColor": "#4A3622", "roughness": 0.6}, opac=0.4)
    r.mapa(f, "ZN_Espalda")
    r.grunge(f, "Grunge Stains Heavy", 3, fusion="Multiply")
    r.escaneo(f, 0.4, 0.35)
    f = r.capa("Tierra seca abajo", T, {"baseColor": "#9C8468", "roughness": 0.95}, opac=0.6)
    r.mapa(f, "ZN_Suelo")
    r.grunge(f, "Grunge Dusty Powder Soft", 5, fusion="Multiply")
    r.escaneo(f, 0.38, 0.35)
    f = r.capa("Salpicaduras de barro", T, {"baseColor": "#5A4530", "roughness": 0.92, "height": 0.006}, opac=0.6)
    r.mapa(f, "ZN_Suelo")
    r.grunge(f, "Grunge Dirt", 7, fusion="Multiply")
    r.escaneo(f, 0.6, 0.3)
    f = r.capa("Manchas de agua", T, {"baseColor": "#5E4429", "roughness": 0.7}, opac=0.4)
    r.grunge(f, "Grunge Leak Small", 4)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.55, 0.3)
    V = r.grupo("Velcro", clases=("Velcro",))
    r.capa("Velcro: lazo oliva", V, {"baseColor": "#55523C", "roughness": 0.95}, opac=0.9)
    f = r.capa("Velcro: pelusa", V, {"baseColor": "#9A957E", "roughness": 0.95}, opac=0.3)
    r.grunge(f, "Grunge Dusty Powder Soft", 12)


def acolchado(r):
    A = r.grupo("Acolchado", clases=ACOLCHADO)
    r.capa("Malla acolchada", A, {"baseColor": "#3B3A2E", "roughness": 0.9, "metallic": 0})
    f = r.capa("Malla: hilo claro", A, {"baseColor": "#5E5C48", "roughness": 0.82}, opac=0.6)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.5, 0.35)
    f = r.capa("Malla: fondo", A, {"baseColor": "#17160F", "roughness": 0.95}, opac=0.7)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.55, 0.35)
    f = r.capa("Sudor: sal y brillo", A, {"baseColor": "#6A6756", "roughness": 0.6}, opac=0.4)
    r.mapa(f, "ZN_Mano")
    r.mapa(f, "ZN_Espalda", fusion="LinearDodge")
    r.grunge(f, "Grunge Stains Heavy", 4, fusion="Multiply")
    r.escaneo(f, 0.4, 0.35)
    f = r.capa("Mugre en pespuntes", A, {"baseColor": "#12110C", "roughness": 0.9}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.7})


def nailon(r):
    N = r.grupo("Nailon", clases=NAILON)
    r.capa("Cincha oliva", N, {"baseColor": "#3F4130", "roughness": 0.7, "metallic": 0})
    f = r.capa("Cincha: canutillo claro", N, {"baseColor": "#5C5F47", "roughness": 0.6}, opac=0.6)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.5, 0.35)
    f = r.capa("Cincha: fondo del canutillo", N, {"baseColor": "#1E2016", "roughness": 0.85}, opac=0.6)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.55, 0.35)
    # solo en cincha y asa: para el generador, una cinta de cremallera de 5 mm o un ribete de 4 son todo canto
    f = r.capa("Canto deshilachado", N, {"baseColor": "#7A7C62", "roughness": 0.85}, opac=0.2, clases=("Cincha", "Asa"))
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.2, "Wear_Contrast": 0.6, "Grunge_Amount": 0.9, "grunge_scale": 8})
    f = r.capa("Brillo de uso", N, {"roughness": 0.42}, opac=0.5)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Fingerprints Smeared", 5, fusion="Multiply")
    f = r.capa("Polvo en la cincha", N, {"baseColor": "#8C7C64", "roughness": 0.95}, opac=0.3)
    r.mapa(f, "ZN_Suelo")
    r.mapa(f, "ZN_Sol", fusion="LinearDodge")
    r.grunge(f, "Grunge Dusty Powder Soft", 8, fusion="Multiply")
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Mugre en rincones", N, {"baseColor": "#17150E", "roughness": 0.9}, opac=0.45)
    r.gen(f, "Dirt", {"dirt_level": 0.35, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    r.capa("Ribete: algo mas oscuro", N, {"baseColor": "#2E3023"}, opac=0.5, clases=("Ribete", "Cinta_Cremallera"))
    r.capa("Cinta de cremallera: negra", N, {"baseColor": "#161714", "roughness": 0.7}, opac=0.9, clases=("Cinta_Cremallera",))
    r.capa("Cordon: negro", N, {"baseColor": "#1B1B19", "roughness": 0.75}, opac=0.9, clases=("Cordon",))
    H = r.grupo("Hilo", clases=("Hilo",))
    r.capa("Pespunte crudo", H, {"baseColor": "#B9AE93", "roughness": 0.8, "metallic": 0})
    f = r.capa("Pespunte sucio", H, {"baseColor": "#6E6450", "roughness": 0.9}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 10)


def duros(r):
    P = r.grupo("Plastico", clases=DUROS)
    r.capa("Acetal negro", P, {"baseColor": "#1A1A19", "roughness": 0.42, "metallic": 0})
    f = r.capa("Plastico: velo mate", P, {"baseColor": "#232321", "roughness": 0.58}, opac=0.5)
    r.grunge(f, "Clouds 2", 10)
    f = r.capa("Plastico: canto blanquecino", P, {"baseColor": "#55554F", "roughness": 0.5}, opac=0.3)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.3, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8})
    f = r.capa("Plastico: aranazos", P, {"baseColor": "#4A4A46", "roughness": 0.6, "height": -0.004}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Plastico: polvo en huecos", P, {"baseColor": "#8C7C64", "roughness": 0.95}, opac=0.22)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    Z = r.grupo("Cremallera", clases=("Cremallera",))
    r.capa("Espiral negra", Z, {"baseColor": "#121211", "roughness": 0.62, "metallic": 0})   # satinada: brillante refleja el ciclorama y sale gris
    f = r.capa("Espiral: brillo en la cresta", Z, {"baseColor": "#222220", "roughness": 0.5}, opac=0.3)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.6, "Grunge_Amount": 0.5, "grunge_scale": 8})
    f = r.capa("Espiral: polvo", Z, {"baseColor": "#8C7C64", "roughness": 0.95}, opac=0.15)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    C = r.grupo("Cursor", clases=("Cursor",))
    r.capa("Zamak pintado de negro", C, {"baseColor": "#161617", "roughness": 0.45, "metallic": 1})
    f = r.capa("Cursor: metal en el canto", C, {"baseColor": "#A9A7A0", "roughness": 0.3, "metallic": 1}, opac=0.85)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.7, "Grunge_Amount": 0.6, "grunge_scale": 8})
    G = r.grupo("Goma", clases=("Parche", "Tirador"))
    r.capa("PVC gris oscuro", G, {"baseColor": "#2A2B28", "roughness": 0.55, "metallic": 0})
    f = r.capa("Goma: polvo", G, {"baseColor": "#8C7C64", "roughness": 0.95}, opac=0.25)
    r.gen(f, "Dirt", {"dirt_level": 0.45, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    f = r.capa("Goma: brillo de roce", G, {"roughness": 0.35}, opac=0.5)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.3, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 8})
    L = r.grupo("Rotulos", clases=("Tinta_Clara",))
    r.capa("Letras en relieve", L, {"baseColor": "#C9C5B6", "roughness": 0.5, "metallic": 0})
    f = r.capa("Letras: mugre", L, {"baseColor": "#5A5446", "roughness": 0.8}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 14)


def construir():
    r = Receta(SET, "mochila KORVANT")
    tela(r)
    acolchado(r)
    nailon(r)
    duros(r)
    S = r.grupo("Polvo global")
    f = r.capa("Polvo fino", S, {"baseColor": "#9A8A70", "roughness": 0.95}, opac=0.1)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
