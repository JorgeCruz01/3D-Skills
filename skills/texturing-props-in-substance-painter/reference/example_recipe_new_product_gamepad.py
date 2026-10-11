"""Look-dev del mando ZALVEK en Substance 3D Painter.

    python ../_herramientas/sp.py proyecto Mando_Consola LP_Mando --extrusion 0.012
    python ../_herramientas/sp.py normal   Mando_Consola LP_Mando       (el punteado del dorso y del panel es relieve de material)
    python ../_herramientas/sp.py rehacer  Mando_Consola

Aspecto: mando NUEVO, recien sacado de la caja, y fotorrealista (Jorge, 2026-10-11). Sin desgaste, sin mugre, sin
polvo, sin huellas. Lo que lo hace creible no es la suciedad sino que CADA plastico tenga su acabado, como en
`Referencias/ref_frente_amos.jpg`:
- carcasa de la cara: negro mate con grano fino de electroerosion (relieve de micras y rugosidad que no es plana);
- dorso y empunaduras: el mismo negro con punteado fino (viene del high poly, por la normal de Blender);
- discos de la cruceta y de los botones, bisel del panel y botones: negro piano, casi espejo;
- panel tactil: satinado con su trama de puntos; cruceta, gatillos y botones superiores: satinado mas brillante;
- setas de las palancas: goma mate con grano;
- numeros de los botones en color, tampografia gris clara, barra de luz blanca azulada, tornillos pavonados.
La unica imperfeccion es la de un objeto nuevo de verdad: la rugosidad varia un poco de un punto a otro.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y pieza (Carcasa, Carcasa_Dorso, Carcasa_Brillo, Panel,
Panel_Bisel, Tecla, Negro_Brillo, Central, Pildora, Goma, Gatillo, Luz, Acero_Negro, Hueco, Tinta_Clara, Num_1..4).
"""
from sp_receta import Receta

NEGRO = "#1B1B1D"            # ABS negro: con #29292B el mando salia gris bajo el estudio
PIANO = "#0A0A0C"


def _variacion(r, G, nombre, rough, escala=3, opac=0.5):
    f = r.capa(nombre + ": rugosidad que no es plana", G, {"roughness": rough}, opac=opac)
    r.grunge(f, "Clouds 2", escala)
    return f


def construir():
    r = Receta("LP_Mando", "mando ZALVEK")

    # Fondo sin mascara: las mascaras de clase van suavizadas y en la frontera entre dos clases ninguna llega a 1.
    # Sin esto asomaba el gris por defecto de Painter: un filo claro alrededor de cada disco y a lo largo de la junta.
    Z = r.grupo("Fondo")
    r.capa("Negro de fondo", Z, {"baseColor": "#141416", "roughness": 0.4, "metallic": 0})

    C = r.grupo("Carcasa, cara", clases=("Carcasa",))
    r.capa("ABS negro mate", C, {"baseColor": NEGRO, "roughness": 0.46, "metallic": 0})
    # el grano de electroerosion mide decimas de milimetro: `Gaussian Noise` a escala 32 daba bultos de 1.5 mm y la
    # carcasa parecia cuero. Ruido al tamano del texel (0.06 mm) y una segunda octava algo mayor
    f = r.capa("Grano de electroerosion", C, {"height": 0.003, "roughness": 0.54}, opac=0.9)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa("Grano: segunda octava", C, {"height": 0.002, "roughness": 0.42}, opac=0.6)
    r.grunge(f, "Gaussian Noise", 220)
    _variacion(r, C, "Cara", 0.5, 3, 0.45)

    D = r.grupo("Carcasa, dorso", clases=("Carcasa_Dorso",))
    r.capa("ABS negro punteado", D, {"baseColor": "#19191B", "roughness": 0.5, "metallic": 0})
    f = r.capa("Dorso: grano", D, {"height": 0.002, "roughness": 0.56}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa("Dorso: crestas del punteado, mas lisas", D, {"roughness": 0.4, "baseColor": "#202022"}, opac=0.6)
    r.mapa(f, "CP_Relieve_Canto")
    _variacion(r, D, "Dorso", 0.55, 3, 0.4)

    B = r.grupo("Negro piano", clases=("Carcasa_Brillo", "Panel_Bisel", "Negro_Brillo", "Central"))
    r.capa("Negro piano", B, {"baseColor": PIANO, "roughness": 0.11, "metallic": 0})
    _variacion(r, B, "Piano", 0.15, 4, 0.35)
    f = r.capa("Piano: microrrayas de fabrica", B, {"roughness": 0.16}, opac=0.25)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.08, 0.9)

    P = r.grupo("Panel tactil", clases=("Panel",))
    r.capa("Policarbonato satinado", P, {"baseColor": "#131315", "roughness": 0.36, "metallic": 0})
    f = r.capa("Panel: grano fino", P, {"height": 0.0012, "roughness": 0.42}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    _variacion(r, P, "Panel", 0.42, 4, 0.35)

    T = r.grupo("Cruceta y pildoras", clases=("Tecla", "Pildora"))
    r.capa("ABS satinado", T, {"baseColor": "#101012", "roughness": 0.28, "metallic": 0})
    f = r.capa("Satinado: grano", T, {"height": 0.0008, "roughness": 0.34}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    _variacion(r, T, "Satinado", 0.3, 4, 0.4)

    G = r.grupo("Gatillos y botones superiores", clases=("Gatillo",))
    r.capa("ABS semibrillo", G, {"baseColor": "#0F0F11", "roughness": 0.3, "metallic": 0})
    f = r.capa("Gatillo: grano", G, {"height": 0.0006, "roughness": 0.36}, opac=0.6)
    r.grunge(f, "White Noise Fast", 1)
    _variacion(r, G, "Gatillo", 0.36, 3, 0.4)

    S = r.grupo("Setas de las palancas", clases=("Goma",))
    r.capa("Goma negra", S, {"baseColor": "#171718", "roughness": 0.74, "metallic": 0})
    f = r.capa("Goma: grano", S, {"height": 0.004, "roughness": 0.82}, opac=0.9)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa("Goma: poro", S, {"height": -0.002, "roughness": 0.66}, opac=0.6)
    r.grunge(f, "Gaussian Noise", 180)
    _variacion(r, S, "Goma", 0.7, 3, 0.35)

    N = r.grupo("Numeros de los botones", clases=("Num_1", "Num_2", "Num_3", "Num_4"))
    r.capa("Tampografia bajo barniz", N, {"baseColor": "#B8B8BC", "roughness": 0.18, "metallic": 0})
    for k, color in enumerate(("#3CC7B4", "#E38FC8", "#E4584B", "#7FA8EA"), 1):
        r.capa("Numero %d" % k, N, {"baseColor": color}, clases=("Num_%d" % k,))

    I = r.grupo("Tampografia", clases=("Tinta_Clara",))
    r.capa("Tinta gris clara", I, {"baseColor": "#B4B4B8", "roughness": 0.42, "metallic": 0, "height": 0.0006})

    L = r.grupo("Barra de luz", clases=("Luz",))
    r.capa("Policarbonato difusor", L, {"baseColor": "#B4C8DC", "roughness": 0.14, "metallic": 0})
    _variacion(r, L, "Luz", 0.3, 4, 0.3)

    M = r.grupo("Tornillos y conectores", clases=("Acero_Negro",))
    r.capa("Acero pavonado", M, {"baseColor": "#34343A", "roughness": 0.34, "metallic": 1})
    _variacion(r, M, "Acero", 0.45, 6, 0.4)

    # sombra de contacto en lo hondo (rejilla del altavoz, pozos de las palancas, conectores, junta): negro sobre
    # negro, no es mugre. Sin ella los agujeros del altavoz se leian como bultos
    K = r.grupo("Fondo del altavoz", clases=("Hueco",))
    r.capa("Negro del hueco", K, {"baseColor": "#020202", "roughness": 0.8, "metallic": 0, "height": -0.02})

    H = r.grupo("Huecos")
    f = r.capa("Sombra en lo hondo", H, {"baseColor": "#040405", "roughness": 0.6}, opac=0.85)
    r.gen(f, "Dirt", {"dirt_level": 0.22, "dirt_contrast": 0.7, "grunge_amount": 0.0})
    return r
