"""Look-dev de la camara de cine CINVARO K-16 en Substance 3D Painter. Dos sets (cuerpo, optica) con los mismos
materiales: una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py rehacer Camara_Cine_16mm

Aspecto: camara USADA, de los anos cincuenta, cuidada pero con rodaje. Esmalte negro semimate saltado al laton en
los cantos y donde se agarra; cuero negro de grano fino, brunido y mas liso donde apoya la mano; cromo con velo,
picaduras y huellas; barriles de los objetivos negros con el laton asomando en los cantos; goma del ocular mate y
polvorienta; vidrio oscuro con tratamiento violeta; rotulos grabados y rellenos, algo gastados.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{U,O}_{Esmalte, Cuero, Cromo, Barril, Vidrio, Goma, Tinta_Blanca, Tinta_Roja}. Zona ZN_U_Mano. Campos CP_*_{U,O}.

Luces quemadas: el cromo publicado reventaba en la vista frontal; aqui el cromo sube a rugosidad 0.22 con velo.
"""
from sp_receta import Receta

LATON = "#8E6A2C"
NEGRO = "#111113"
POLVO = "#6A655E"


def _camara(r, p, mano=False):
    c = lambda *n: tuple(p + x for x in n)
    s = p[0]
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Negro de fondo", Z, {"baseColor": NEGRO, "roughness": 0.5, "metallic": 0})

    for nombre, cl, desgaste in (("Esmalte", c("Esmalte", "Tinta_Blanca", "Tinta_Roja"), 0.3), ("Barril", c("Barril"), 0.26)):
        E = r.grupo(p + nombre + ": laton", clases=cl)
        r.capa(p + nombre + ": laton desnudo", E, {"baseColor": LATON, "roughness": 0.38, "metallic": 1})
        f = r.capa(p + nombre + ": laton oscurecido", E, {"baseColor": "#4A3A1C", "roughness": 0.6}, opac=0.6)
        r.grunge(f, "Grunge Dirt", 8)
        r.escaneo(f, 0.45, 0.4)
        P = r.grupo(p + nombre + ": pintura", dentro=E, clases=cl)
        r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": desgaste, "Wear_Contrast": 0.75, "Grunge_Amount": 0.85, "grunge_scale": 8}, fusion="Multiply")
        r.capa(p + nombre + ": negro semimate", P, {"baseColor": NEGRO, "roughness": 0.36, "metallic": 0, "height": 0.004})
        f = r.capa(p + nombre + ": piel del esmalte", P, {"height": 0.0015, "roughness": 0.42}, opac=0.6)
        r.grunge(f, "Gaussian Noise", 80)
        f = r.capa(p + nombre + ": brunido", P, {"baseColor": "#1A1A1D", "roughness": 0.22}, opac=0.6)
        r.grunge(f, "Grunge Stains Heavy", 5)
        r.escaneo(f, 0.45, 0.4)
        f = r.capa(p + nombre + ": aranazos", P, {"baseColor": "#3A3A3D", "roughness": 0.5, "height": -0.0015}, opac=0.5)
        r.grunge(f, "Grunge Scratches Fine", 5)
        r.escaneo(f, 0.1, 0.85)
        if nombre == "Esmalte":
            r.capa(p + "Rotulos blancos", P, {"baseColor": "#C9C7BE", "roughness": 0.5, "height": -0.001}, clases=c("Tinta_Blanca"))
            r.capa(p + "Rotulos rojos", P, {"baseColor": "#B02A1C", "roughness": 0.5, "height": -0.001}, clases=c("Tinta_Roja"))
            f = r.capa(p + "Rotulos gastados", P, {"baseColor": NEGRO, "roughness": 0.45}, opac=0.5, clases=c("Tinta_Blanca", "Tinta_Roja"))
            r.grunge(f, "Grunge Scratches Fine", 9)
            r.escaneo(f, 0.3, 0.6)
        f = r.capa(p + nombre + ": desconchones", E, {"baseColor": LATON, "roughness": 0.4, "metallic": 1, "height": -0.004}, opac=0.95)
        r.grunge(f, "Grunge Dirt", 5)
        r.mapa(f, "CP_Manchas_" + s, fusion="Multiply")
        r.escaneo(f, 0.07, 0.9)
        f = r.capa(p + nombre + ": polvo en rincones", E, {"baseColor": POLVO, "roughness": 0.9}, opac=0.4)
        r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.55, "grunge_amount": 0.85})

    L = r.grupo(p + "Cuero", clases=c("Cuero"))
    r.capa(p + "Cuero negro", L, {"baseColor": "#0F0E0D", "roughness": 0.55, "metallic": 0})
    f = r.capa(p + "Cuero: grano", L, {"height": 0.03, "roughness": 0.7, "baseColor": "#070707"}, opac=0.9)
    r.grunge(f, "Cells 1", 24)
    f = r.capa(p + "Cuero: tono pardo", L, {"baseColor": "#2A2520", "roughness": 0.6}, opac=0.14)
    r.grunge(f, "Clouds 2", 5)
    f = r.capa(p + "Cuero: brunido por la mano", L, {"baseColor": "#1C1A18", "roughness": 0.3, "height": -0.004}, opac=0.75)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.5, 0.4)
    if mano:
        r.mapa(f, "ZN_U_Mano", fusion="Multiply")
    f = r.capa(p + "Cuero: cantos rozados", L, {"baseColor": "#3A322C", "roughness": 0.7}, opac=0.45)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.22, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8})
    f = r.capa(p + "Cuero: polvo en el grano", L, {"baseColor": POLVO, "roughness": 0.9}, opac=0.05)
    r.grunge(f, "Clouds 2", 7)

    K = r.grupo(p + "Cromo", clases=c("Cromo"))
    r.capa(p + "Cromo", K, {"baseColor": "#B4B5B7", "roughness": 0.22, "metallic": 1})
    f = r.capa(p + "Cromo: velo", K, {"baseColor": "#8C8C8C", "roughness": 0.42}, opac=0.6)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Cromo: huellas", K, {"roughness": 0.5, "baseColor": "#7C7A76"}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Cromo: picaduras", K, {"baseColor": "#3A2E22", "roughness": 0.75, "metallic": 0, "height": -0.003}, opac=0.9)
    r.grunge(f, "Grunge Dirt", 12)
    r.escaneo(f, 0.07, 0.9)
    f = r.capa(p + "Cromo: mugre en rincones", K, {"baseColor": "#1A1612", "roughness": 0.7, "metallic": 0}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.85})

    G = r.grupo(p + "Goma", clases=c("Goma"))
    r.capa(p + "Goma negra", G, {"baseColor": "#161616", "roughness": 0.75, "metallic": 0})
    f = r.capa(p + "Goma: reseca", G, {"baseColor": "#3A3835", "roughness": 0.9}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)

    V = r.grupo(p + "Vidrio", clases=c("Vidrio"))
    r.capa(p + "Vidrio tratado", V, {"baseColor": "#0C0A1E", "roughness": 0.06, "metallic": 0})
    f = r.capa(p + "Vidrio: polvo", V, {"baseColor": POLVO, "roughness": 0.3}, opac=0.04)
    r.grunge(f, "Clouds 2", 9)
    return r


def construir():
    return [_camara(Receta("LP_Cuerpo", "cuerpo CINVARO"), "U_", mano=True),
            _camara(Receta("LP_Optica", "optica CINVARO"), "O_")]
