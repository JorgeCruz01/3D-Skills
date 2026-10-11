"""Look-dev del grupo electrogeno VOLKAM en Substance 3D Painter. Tres sets: bastidor (jaula y deposito), motor
(motor, alternador, filtro, silenciador, silentblocks) y panel (panel con sus mandos, tirador, tapon de aceite, bujia).

    python ../_herramientas/sp.py rehacer Grupo_Electrogeno

Aspecto: grupo USADO, de obra y de alquiler (Jorge, 2026-10-10: los props que siguen a la guitarra van usados).
Jaula de tubo pintada de negro, pelada al acero donde se agarra para moverla y donde apoya, con oxido en las
soldaduras. Deposito naranja de chapa embutida: mate y descolorido por el sol, con cercos de gasolina alrededor de
la boca y desconchones en el canto de la pestana. Motor de aluminio fundido gris, oscurecido por el aceite y el
polvo pegado; cilindro y escape tostados por el calor; silenciador de chapa pavonada por el calor y con oxido.
Alternador pintado de negro, con polvo en las aletas. Plasticos negros mates y con polvo; panel con los rotulos
gastados y brillo de dedos junto a los mandos.

Mascaras (Texturas/Bakes/Mascaras/), horneadas contra una copia de la low poly con solo las caras de cada set y
renombradas con el prefijo del set: MK_B_* (Tubo, Goma, Deposito, Tapon, Nivel, Tinta_Negra), MK_M_* (Fundicion,
Negro, Alternador, Filtro, Silenciador, Goma), MK_P_* (Panel, Toma, Tirador, Bujia, Voltimetro, Magneto,
Tapon_Aceite, Interruptor, Borne, Tinta_Blanca). Zonas ZN_B_Arriba, ZN_B_Suelo, ZN_B_Boca; ZN_M_Escape, ZN_M_Aceite,
ZN_M_Calor; ZN_P_Dedos, ZN_P_Tirador. Campos CP_*_B, CP_*_M, CP_*_P.
"""
from sp_receta import Receta

POLVO = "#A1998A"
ACERO = "#57514C"
OXIDO = "#74401F"
NARANJA, NARANJA_CLARO = "#C9520C", "#DE8A48"
MUGRE = "#18130E"


def _negro_pintado(r, G, pre, mk, clases):
    r.capa(pre + ": acero", G, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1})
    f = r.capa(pre + ": oxido", G, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.7)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.5, 0.4)
    # el grupo de pintura lleva SU mascara de clase: sin ella el desgaste de cantos multiplica sobre una mascara
    # vacia y la pintura queda a cero (primera pasada: deposito y tubos, todo oxido)
    P = r.grupo(pre + ": pintura negra", dentro=G, clases=clases)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.3, "Wear_Contrast": 0.75, "Grunge_Amount": 0.85, "grunge_scale": 8}, fusion="Multiply")
    r.mapa(P, mk, fusion="LinearDodge", opac=0.88)          # un tubo es "todo canto" para el generador
    r.capa(pre + ": esmalte negro", P, {"baseColor": "#151517", "roughness": 0.4, "metallic": 0, "height": 0.004})
    f = r.capa(pre + ": brillo comido", P, {"baseColor": "#222225", "roughness": 0.64}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa(pre + ": aranazos", P, {"baseColor": "#4E4F53", "roughness": 0.55}, opac=0.45)
    r.grunge(f, "Grunge Scratches Fine", 6)
    r.escaneo(f, 0.1, 0.85)
    return P


def bastidor():
    r = Receta("LP_Bastidor", "bastidor y deposito")
    Z = r.grupo("Fondo")
    r.capa("Negro de fondo", Z, {"baseColor": "#141416", "roughness": 0.5, "metallic": 0})

    T = r.grupo("Jaula de tubo", clases=("B_Tubo",))
    _negro_pintado(r, T, "Tubo", "MK_B_Tubo", ("B_Tubo",))
    f = r.capa("Tubo: pelado donde se agarra", T, {"baseColor": "#7B7670", "roughness": 0.36, "metallic": 1, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.42, 0.7)
    r.mapa(f, "ZN_B_Arriba", fusion="Multiply")
    f = r.capa("Tubo: rozado donde apoya", T, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.4, 0.7)
    r.mapa(f, "ZN_B_Suelo", fusion="Multiply")
    f = r.capa("Tubo: oxido en soldaduras", T, {"baseColor": "#5E3319", "roughness": 0.88}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.9})
    f = r.capa("Tubo: polvo", T, {"baseColor": "#7A7468", "roughness": 0.92}, opac=0.2)
    r.grunge(f, "Clouds 2", 5)

    D = r.grupo("Deposito", clases=("B_Deposito", "B_Tinta_Negra"))
    r.capa("Chapa", D, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1})
    f = r.capa("Chapa: oxido", D, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.8)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.5, 0.4)
    P = r.grupo("Esmalte naranja", dentro=D, clases=("B_Deposito", "B_Tinta_Negra"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.4, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 6}, fusion="Multiply")
    # roughness 0.5 y no 0.3: el deposito publicado tenia la tapa quemada (una mancha del 0.74 % a L > 250)
    r.capa("Naranja", P, {"baseColor": NARANJA, "roughness": 0.5, "metallic": 0, "height": 0.004})
    f = r.capa("Descolorido por el sol", P, {"baseColor": NARANJA_CLARO, "roughness": 0.66}, opac=0.45)
    r.mapa(f, "CP_Manchas_B")
    r.escaneo(f, 0.45, 0.3)
    r.capa("Rotulos del deposito", P, {"baseColor": "#151413", "roughness": 0.5}, clases=("B_Tinta_Negra",))
    f = r.capa("Rotulos gastados", P, {"baseColor": NARANJA, "roughness": 0.55}, opac=0.8, clases=("B_Tinta_Negra",))
    r.grunge(f, "Grunge Scratches Fine", 8)
    r.escaneo(f, 0.3, 0.6)
    f = r.capa("Mate del uso", P, {"roughness": 0.7}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Aranazos claros", P, {"baseColor": NARANJA_CLARO, "roughness": 0.6, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Desconchones", D, {"baseColor": OXIDO, "roughness": 0.85, "metallic": 0, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 5)
    r.mapa(f, "CP_Manchas_B", fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Cercos de gasolina", D, {"baseColor": "#5A2E0C", "roughness": 0.3}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    r.mapa(f, "ZN_B_Boca", fusion="Multiply")
    f = r.capa("Mugre en la pestana", D, {"baseColor": MUGRE, "roughness": 0.8}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Polvo posado", D, {"baseColor": POLVO, "roughness": 0.95}, opac=0.25)
    r.grunge(f, "Grunge Dusty Powder Soft", 4)
    r.escaneo(f, 0.42, 0.3)

    N = r.grupo("Tapon y tacos", clases=("B_Tapon", "B_Goma"))
    r.capa("Plastico negro", N, {"baseColor": "#17171A", "roughness": 0.55, "metallic": 0})
    f = r.capa("Negro: gris de uso", N, {"baseColor": "#4A4844", "roughness": 0.75}, opac=0.4)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa("Negro: polvo", N, {"baseColor": "#6E685C", "roughness": 0.9}, opac=0.2)
    r.grunge(f, "Clouds 2", 9)

    V = r.grupo("Nivel", clases=("B_Nivel",))
    r.capa("Plastico blanco amarillento", V, {"baseColor": "#CFC6A8", "roughness": 0.4, "metallic": 0})
    f = r.capa("Nivel: sucio", V, {"baseColor": "#5B4A2C", "roughness": 0.7}, opac=0.4)
    r.grunge(f, "Grunge Stains Heavy", 8)
    r.escaneo(f, 0.45, 0.4)
    return r


def motor():
    r = Receta("LP_Motor", "motor y alternador")
    Z = r.grupo("Fondo")
    r.capa("Gris de fondo", Z, {"baseColor": "#2A2826", "roughness": 0.6, "metallic": 0})

    F = r.grupo("Fundicion de aluminio", clases=("M_Fundicion",))
    r.capa("Aluminio fundido", F, {"baseColor": "#8E8D8A", "roughness": 0.5, "metallic": 1})
    f = r.capa("Aluminio: piel de fundicion", F, {"height": 0.004, "roughness": 0.6}, opac=0.8)
    r.grunge(f, "Gaussian Noise", 90)
    f = r.capa("Aluminio: oxido blanco", F, {"baseColor": "#B7B6B0", "roughness": 0.75}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)
    r.escaneo(f, 0.55, 0.3)
    f = r.capa("Tostado por el calor", F, {"baseColor": "#5A4A38", "roughness": 0.66}, opac=0.7)
    r.grunge(f, "Clouds 2", 4)
    r.escaneo(f, 0.6, 0.35)
    r.mapa(f, "ZN_M_Calor", fusion="Multiply")
    f = r.capa("Aceite que suda", F, {"baseColor": "#17110A", "roughness": 0.22}, opac=0.75)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)
    r.mapa(f, "ZN_M_Aceite", fusion="Multiply")
    f = r.capa("Mugre pegada", F, {"baseColor": "#2B241B", "roughness": 0.85}, opac=0.65)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    f = r.capa("Polvo", F, {"baseColor": POLVO, "roughness": 0.95}, opac=0.2)
    r.grunge(f, "Grunge Dusty Powder Soft", 5)
    r.escaneo(f, 0.42, 0.3)

    A = r.grupo("Alternador y carcasas pintadas", clases=("M_Alternador", "M_Negro"))
    _negro_pintado(r, A, "Alternador", "MK_M_Alternador", ("M_Alternador", "M_Negro"))
    # polvo claro umbralizado sobre negro se lee como granito (leccion del casco): velo sin umbral
    f = r.capa("Alternador: polvo en las aletas", A, {"baseColor": "#7A7468", "roughness": 0.92}, opac=0.3)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa("Alternador: desconchones", A, {"baseColor": OXIDO, "roughness": 0.85, "height": -0.003}, opac=0.9)
    r.grunge(f, "Grunge Dirt", 6)
    r.mapa(f, "CP_Manchas_M", fusion="Multiply")
    r.escaneo(f, 0.14, 0.85)

    K = r.grupo("Filtro de aire", clases=("M_Filtro",))
    r.capa("Plastico negro", K, {"baseColor": "#18181A", "roughness": 0.55, "metallic": 0})
    f = r.capa("Filtro: grano", K, {"height": 0.002, "roughness": 0.62}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa("Filtro: gris de uso", K, {"baseColor": "#4A4844", "roughness": 0.75}, opac=0.4)
    r.grunge(f, "Clouds 2", 5)
    f = r.capa("Filtro: polvo", K, {"baseColor": "#6E685C", "roughness": 0.9}, opac=0.25)
    r.grunge(f, "Clouds 2", 9)

    S = r.grupo("Silenciador", clases=("M_Silenciador",))
    r.capa("Chapa de acero", S, {"baseColor": "#5B5855", "roughness": 0.45, "metallic": 1})
    f = r.capa("Pavonado del calor", S, {"baseColor": "#3B3147", "roughness": 0.5, "metallic": 1}, opac=0.7)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.5, 0.3)
    f = r.capa("Tostado", S, {"baseColor": "#6B4A2A", "roughness": 0.6, "metallic": 1}, opac=0.6)
    r.grunge(f, "Clouds 2", 5)
    r.escaneo(f, 0.55, 0.3)
    f = r.capa("Silenciador: oxido", S, {"baseColor": OXIDO, "roughness": 0.9, "metallic": 0}, opac=0.85)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.42, 0.5)
    f = r.capa("Hollin en la salida", S, {"baseColor": "#0B0A09", "roughness": 0.92, "metallic": 0}, opac=0.8)
    r.grunge(f, "Clouds 2", 3)
    r.escaneo(f, 0.7, 0.3)
    r.mapa(f, "ZN_M_Escape", fusion="Multiply")

    G = r.grupo("Silentblocks", clases=("M_Goma",))
    r.capa("Goma negra", G, {"baseColor": "#161617", "roughness": 0.75, "metallic": 0})
    f = r.capa("Goma: polvo", G, {"baseColor": "#6E685C", "roughness": 0.9}, opac=0.3)
    r.grunge(f, "Clouds 2", 8)
    return r


def panel():
    r = Receta("LP_Panel", "panel y mandos")
    Z = r.grupo("Fondo")
    r.capa("Negro de fondo", Z, {"baseColor": "#151517", "roughness": 0.55, "metallic": 0})

    P = r.grupo("Panel y plasticos negros", clases=("P_Panel", "P_Toma", "P_Tirador", "P_Tinta_Blanca"))
    r.capa("Plastico negro", P, {"baseColor": "#17171A", "roughness": 0.52, "metallic": 0})
    f = r.capa("Panel: grano", P, {"height": 0.002, "roughness": 0.6}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    r.capa("Rotulos blancos", P, {"baseColor": "#C9C9C6", "roughness": 0.5, "height": 0.0006}, clases=("P_Tinta_Blanca",))
    f = r.capa("Rotulos gastados", P, {"baseColor": "#17171A", "roughness": 0.55}, opac=0.7, clases=("P_Tinta_Blanca",))
    r.grunge(f, "Grunge Scratches Fine", 8)
    r.escaneo(f, 0.3, 0.6)
    f = r.capa("Brillo de dedos", P, {"baseColor": "#1D1D20", "roughness": 0.3}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.42, 0.4)
    r.mapa(f, "ZN_P_Dedos", fusion="Multiply")
    r.mapa(f, "ZN_P_Tirador", fusion="LinearDodge", opac=0.8)
    f = r.capa("Panel: aranazos", P, {"baseColor": "#4E4F53", "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Panel: polvo", P, {"baseColor": "#6E685C", "roughness": 0.9}, opac=0.22)
    r.grunge(f, "Clouds 2", 9)

    B = r.grupo("Blancos", clases=("P_Voltimetro", "P_Magneto", "P_Bujia"))
    r.capa("Plastico blanco", B, {"baseColor": "#C8C6BC", "roughness": 0.4, "metallic": 0})
    f = r.capa("Blanco: amarillea", B, {"baseColor": "#B9A878", "roughness": 0.5}, opac=0.4)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa("Blanco: sucio", B, {"baseColor": "#4A4034", "roughness": 0.75}, opac=0.4)
    r.grunge(f, "Grunge Stains Heavy", 8)
    r.escaneo(f, 0.42, 0.4)

    I = r.grupo("Interruptor", clases=("P_Interruptor",))
    r.capa("Plastico rojo", I, {"baseColor": "#A51A14", "roughness": 0.35, "metallic": 0})
    f = r.capa("Rojo: gastado", I, {"baseColor": "#C4564C", "roughness": 0.55}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)

    Y = r.grupo("Tapon de aceite", clases=("P_Tapon_Aceite",))
    r.capa("Plastico amarillo", Y, {"baseColor": "#C79A12", "roughness": 0.4, "metallic": 0})
    f = r.capa("Amarillo: aceite y mugre", Y, {"baseColor": "#2B1F0C", "roughness": 0.35}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.45, 0.4)

    L = r.grupo("Borne de tierra", clases=("P_Borne",))
    r.capa("Laton", L, {"baseColor": "#A8843C", "roughness": 0.34, "metallic": 1})
    f = r.capa("Laton: patina", L, {"baseColor": "#4E3B1C", "roughness": 0.62}, opac=0.6)
    r.grunge(f, "Clouds 2", 8)
    return r


def construir():
    return [bastidor(), motor(), panel()]
