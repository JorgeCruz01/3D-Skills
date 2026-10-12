"""Look-dev del extintor de polvo IGNIFEX de 6 kg en Substance 3D Painter. Dos sets (botella, cabezal) con los
mismos materiales: una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py importar Extintor_Polvo_6kg Texturas/Bakes/ETIQUETA.png
    python ../_herramientas/sp.py rehacer Extintor_Polvo_6kg

Aspecto: extintor USADO, colgado anos en una nave. Esmalte rojo de horno, semibrillante, con el brillo comido a
manchas; saltado a la imprimacion gris y al acero en el aro del pie (se arrastra y se apoya), en el cordon y en el
hombro; aranazos finos de moverlo; polvo posado en el hombro. Etiqueta de vinilo impreso (horneada desde Blender al
espacio UV: `ETIQUETA`), algo amarilleada, rozada y con mugre en el borde. Valvula de aluminio fundido, mate y con
flor blanca; palancas de chapa cincada, pulidas donde aprieta la mano y con el cincado gastado en los cantos;
manometro de laton con patina y su esfera impresa; manguera de goma mate, reseca y con polvo; ferulas de aluminio;
boquilla y abrazadera de plastico negro, la boquilla con polvo extintor palido en la boca; precinto amarillo.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{B,C}_{Rojo, Etiqueta, Aluminio, Chapa, Laton, Goma, Plastico_Negro, Precinto, Dial_Blanco, Dial_Verde,
Dial_Rojo, Tinta_Negra}. Zonas ZN_B_Pie, ZN_B_Hombro, ZN_C_Mano, ZN_C_Boquilla. Campos CP_*_{B,C}.
"""
from sp_receta import Receta

IMPRIMACION = "#7C7D7A"
ACERO = "#55524E"
ROJO, ROJO_CLARO, ROJO_OSC = "#8A0C0E", "#A82420", "#5E090B"       # RAL 3000 y sus dos vecinos
POLVO = "#7C776E"
MUGRE = "#2A241C"
ETQ = {"resource": "ETIQUETA", "usage": "texture"}


def _negro(r, p, nombre, cl, color, rug, s, polvo=0.14):
    G = r.grupo(p + nombre, clases=cl)
    r.capa(p + nombre + ": base", G, {"baseColor": color, "roughness": rug, "metallic": 0})
    f = r.capa(p + nombre + ": grano", G, {"height": 0.0015, "roughness": rug + 0.08}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa(p + nombre + ": brillo desigual", G, {"roughness": rug - 0.18}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + nombre + ": roces", G, {"baseColor": "#3A3A3C", "roughness": rug + 0.12, "height": -0.0015}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + nombre + ": polvo", G, {"baseColor": POLVO, "roughness": 0.9}, opac=polvo)
    r.grunge(f, "Clouds 2", 6)
    return G


def _extintor(r, p):
    c = lambda *n: tuple(p + x for x in n)
    s = p[0]
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#2A2A2C", "roughness": 0.55, "metallic": 0})

    # ---------------------------------------------------------------- botella esmaltada
    B = r.grupo(p + "Botella", clases=c("Rojo", "Etiqueta"))
    r.capa(p + "Acero", B, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1})
    f = r.capa(p + "Acero: oxido", B, {"baseColor": "#6E3B1E", "roughness": 0.85, "metallic": 0}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.5, 0.4)
    I = r.grupo(p + "Imprimacion", dentro=B, clases=c("Rojo", "Etiqueta"))
    r.gen(I, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.22, "Wear_Contrast": 0.8, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    r.capa(p + "Imprimacion gris", I, {"baseColor": IMPRIMACION, "roughness": 0.7, "metallic": 0, "height": 0.003})
    E = r.grupo(p + "Esmalte", dentro=B, clases=c("Rojo", "Etiqueta"))
    r.gen(E, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.36, "Wear_Contrast": 0.8, "Grunge_Amount": 0.9, "grunge_scale": 6}, fusion="Multiply")
    r.capa(p + "Rojo de horno", E, {"baseColor": ROJO, "roughness": 0.34, "metallic": 0, "height": 0.006})
    f = r.capa(p + "Piel de naranja", E, {"height": 0.002, "roughness": 0.4}, opac=0.6)
    r.grunge(f, "Gaussian Noise", 70)
    f = r.capa(p + "Tono desigual", E, {"baseColor": ROJO_CLARO, "roughness": 0.42}, opac=0.10)
    r.mapa(f, "CP_Manchas_" + s)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa(p + "Brillo comido", E, {"baseColor": ROJO_OSC, "roughness": 0.58}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa(p + "Aranazos", E, {"baseColor": ROJO_CLARO, "roughness": 0.55, "height": -0.002}, opac=0.45)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.1, 0.85)
    # la etiqueta va pegada sobre el esmalte
    T = r.grupo(p + "Etiqueta", dentro=B, clases=c("Etiqueta"))
    r.capa(p + "Vinilo impreso", T, {"baseColor": ETQ, "roughness": 0.42, "metallic": 0, "height": 0.004}, proy={"mode": "UV"})
    f = r.capa(p + "Etiqueta: amarilleada", T, {"baseColor": "#C9B77A", "roughness": 0.5}, opac=0.22, fusion={"baseColor": "Multiply"})
    r.grunge(f, "Clouds 2", 3)
    f = r.capa(p + "Etiqueta: rozada", T, {"baseColor": "#D8D6CE", "roughness": 0.62}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + "Etiqueta: mugre", T, {"baseColor": MUGRE, "roughness": 0.7}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 5)
    r.escaneo(f, 0.07, 0.88)
    # golpes y desconchones localizados: el pie y el hombro
    f = r.capa(p + "Desconchones del pie", B, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1, "height": -0.006}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.42, 0.7)
    r.mapa(f, "ZN_B_Pie", fusion="Multiply")
    f = r.capa(p + "Desconchones sueltos", B, {"baseColor": IMPRIMACION, "roughness": 0.7, "metallic": 0, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 5)
    r.mapa(f, "CP_Manchas_" + s, fusion="Multiply")
    r.escaneo(f, 0.05, 0.9)
    f = r.capa(p + "Polvo en el hombro", B, {"baseColor": POLVO, "roughness": 0.92}, opac=0.45)
    r.grunge(f, "Clouds 2", 5)
    r.mapa(f, "ZN_B_Hombro", fusion="Multiply")
    f = r.capa(p + "Mugre en rincones", B, {"baseColor": MUGRE, "roughness": 0.7}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.18, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    f = r.capa(p + "Velo de polvo", B, {"baseColor": POLVO, "roughness": 0.9}, opac=0.035)
    r.grunge(f, "Clouds 2", 4)

    # ---------------------------------------------------------------- aluminio fundido y ferulas
    A = r.grupo(p + "Aluminio", clases=c("Aluminio"))
    r.capa(p + "Aluminio fundido", A, {"baseColor": "#8A8B8B", "roughness": 0.48, "metallic": 1})
    f = r.capa(p + "Aluminio: grano", A, {"height": 0.003, "roughness": 0.56}, opac=0.8)
    r.grunge(f, "Gaussian Noise", 140)
    f = r.capa(p + "Aluminio: tono", A, {"baseColor": "#6A6B6C", "roughness": 0.6}, opac=0.45)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Aluminio: flor blanca", A, {"baseColor": "#B0B1AC", "roughness": 0.8, "metallic": 0}, opac=0.45)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.1, 0.8)
    f = r.capa(p + "Aluminio: cantos", A, {"baseColor": "#B8B9BA", "roughness": 0.3, "metallic": 1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.22, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 8})
    f = r.capa(p + "Aluminio: mugre", A, {"baseColor": MUGRE, "roughness": 0.7, "metallic": 0}, opac=0.55)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.22, 0.6)

    # ---------------------------------------------------------------- chapa cincada: palancas, pasador, pivote
    K = r.grupo(p + "Chapa cincada", clases=c("Chapa"))
    r.capa(p + "Acero bajo el cinc", K, {"baseColor": "#4E4B47", "roughness": 0.5, "metallic": 1})
    Zc = r.grupo(p + "Cincado", dentro=K, clases=c("Chapa"))
    r.gen(Zc, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.3, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8}, fusion="Multiply")
    r.mapa(Zc, "MK_" + p + "Chapa", fusion="LinearDodge", opac=0.6)        # chapa de 1.6 mm: para el generador es toda canto
    r.capa(p + "Cinc", Zc, {"baseColor": "#A8ABAE", "roughness": 0.3, "metallic": 1})
    f = r.capa(p + "Cinc: velo", Zc, {"baseColor": "#8A8D90", "roughness": 0.48}, opac=0.55)
    r.grunge(f, "Clouds 2", 7)
    f = r.capa(p + "Cinc: oxido blanco", Zc, {"baseColor": "#B8B9B4", "roughness": 0.8, "metallic": 0}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.08, 0.85)
    f = r.capa(p + "Pulido por la mano", K, {"baseColor": "#B4B6B8", "roughness": 0.18, "metallic": 1}, opac=0.8)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.6, 0.4)
    r.mapa(f, "ZN_C_Mano", fusion="Multiply")
    f = r.capa(p + "Chapa: oxido en cantos", K, {"baseColor": "#6E3B1E", "roughness": 0.85, "metallic": 0}, opac=0.45)
    r.grunge(f, "Grunge Dirt", 11)
    r.escaneo(f, 0.1, 0.8)
    f = r.capa(p + "Chapa: mugre", K, {"baseColor": MUGRE, "roughness": 0.7, "metallic": 0}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.18, 0.6)

    # ---------------------------------------------------------------- manometro
    L = r.grupo(p + "Laton", clases=c("Laton"))
    r.capa(p + "Laton", L, {"baseColor": "#9A7A3A", "roughness": 0.32, "metallic": 1})
    f = r.capa(p + "Laton: patina", L, {"baseColor": "#4A3A1E", "roughness": 0.6}, opac=0.55)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Laton: cantos pulidos", L, {"baseColor": "#C2A25A", "roughness": 0.22, "metallic": 1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.25, "Wear_Contrast": 0.7, "Grunge_Amount": 0.6, "grunge_scale": 8})
    D = r.grupo(p + "Esfera", clases=c("Dial_Blanco", "Dial_Verde", "Dial_Rojo", "Tinta_Negra"))
    r.capa(p + "Esfera: papel", D, {"baseColor": "#D2D0C4", "roughness": 0.16, "metallic": 0})
    r.capa(p + "Esfera: verde", D, {"baseColor": "#1F8A3A", "roughness": 0.16}, clases=c("Dial_Verde"))
    r.capa(p + "Esfera: rojo", D, {"baseColor": "#B4201A", "roughness": 0.16}, clases=c("Dial_Rojo"))
    r.capa(p + "Esfera: tinta", D, {"baseColor": "#141416", "roughness": 0.16}, clases=c("Tinta_Negra"))
    f = r.capa(p + "Esfera: amarilleada", D, {"baseColor": "#B8A468", "roughness": 0.2}, opac=0.25, fusion={"baseColor": "Multiply"})
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Esfera: polvo en el cristal", D, {"baseColor": POLVO, "roughness": 0.45}, opac=0.12)
    r.grunge(f, "Clouds 2", 9)

    # ---------------------------------------------------------------- goma, plasticos y precinto
    G = _negro(r, p, "Goma", c("Goma"), "#131313", 0.72, s, polvo=0.1)
    f = r.capa(p + "Goma: reseca", G, {"baseColor": "#3A3835", "roughness": 0.9}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.3, 0.5)
    P = _negro(r, p, "Plastico negro", c("Plastico_Negro"), "#141415", 0.5, s)
    f = r.capa(p + "Polvo extintor en la boca", P, {"baseColor": "#CFC7A8", "roughness": 0.95, "height": 0.002}, opac=0.75)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.5, 0.5)
    r.mapa(f, "ZN_C_Boquilla", fusion="Multiply")
    S = r.grupo(p + "Precinto", clases=c("Precinto"))
    r.capa(p + "Plastico amarillo", S, {"baseColor": "#D2A018", "roughness": 0.42, "metallic": 0})
    f = r.capa(p + "Precinto: sucio", S, {"baseColor": "#7A5A12", "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)
    return r


def construir():
    return [_extintor(Receta("LP_Botella", "botella IGNIFEX"), "B_"),
            _extintor(Receta("LP_Cabezal", "cabezal IGNIFEX"), "C_")]
