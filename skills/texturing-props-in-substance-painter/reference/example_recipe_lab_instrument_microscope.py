"""Look-dev del microscopio metalografico LUMEQA NM-310 en Substance 3D Painter. Dos sets (estativo, optica) con los
mismos materiales: una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py rehacer Microscopio_Metalografico

Aspecto: instrumento de laboratorio USADO, cuidado pero con anos: no un taller. Esmalte blanco roto, algo
amarilleado y con sombra de manos; esmalte grafito texturado con brillo donde se apoya la mano y la platina rayada
por las probetas; plasticos negros de mandos y oculares con brillo de dedos; objetivos cromados con velo y huellas,
anillos de color segun el aumento (5x rojo, 10x amarillo, 20x verde, 50x azul); lentes oscuras; probeta de acero
pulido a espejo; polvo fino en los rincones.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{E,O}_{Blanco, Grafito, Negro, Cromo, Vidrio, Muestra, Anillo_5x, Anillo_10x, Anillo_20x, Anillo_50x,
Tinta_Negra, Tinta_Blanca}. Zona ZN_E_Platina. Campos CP_*_{E,O}.

Luces quemadas: el blanco es un blanco roto (#B4B1A6) con rugosidad 0.45, para que la luz cenital no lo reviente.
"""
from sp_receta import Receta

POLVO = "#7A766E"
ANILLOS = {"5x": "#B4201A", "10x": "#C9A21A", "20x": "#2F8A3A", "50x": "#3C7FC0"}


def _esmalte(r, p, nombre, cl, color, claro, oscuro, rug, tinta=None, color_tinta=None, grano=False):
    s = p[0]
    G = r.grupo(p + nombre, clases=cl)
    r.capa(p + nombre + ": base", G, {"baseColor": color, "roughness": rug, "metallic": 0})
    f = r.capa(p + nombre + ": piel", G, {"height": 0.002 if grano else 0.001, "roughness": rug + 0.08}, opac=0.7)
    r.grunge(f, "White Noise Fast" if grano else "Gaussian Noise", 1 if grano else 70)
    f = r.capa(p + nombre + ": tono desigual", G, {"baseColor": oscuro, "roughness": rug + 0.05}, opac=0.3)
    r.grunge(f, "Clouds 2", 3)
    f = r.capa(p + nombre + ": sombra de manos", G, {"baseColor": oscuro, "roughness": rug - 0.16}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)
    if tinta:
        r.capa(p + nombre + ": rotulos", G, {"baseColor": color_tinta, "roughness": 0.5}, clases=tinta)
    f = r.capa(p + nombre + ": aranazos", G, {"baseColor": claro, "roughness": rug + 0.12, "height": -0.0015}, opac=0.45)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.08, 0.88)
    f = r.capa(p + nombre + ": cantos rozados", G, {"baseColor": claro, "roughness": rug + 0.1}, opac=0.45)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.14, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8, "grunge_scale": 8})
    f = r.capa(p + nombre + ": polvo en rincones", G, {"baseColor": POLVO, "roughness": 0.92}, opac=0.35)
    r.gen(f, "Dirt", {"dirt_level": 0.16, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    return G


def _micro(r, p, platina=False):
    c = lambda *n: tuple(p + x for x in n)
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#1C1C1E", "roughness": 0.5, "metallic": 0})

    _esmalte(r, p, "Esmalte blanco", c("Blanco", "Tinta_Negra"), "#B4B1A6", "#C4C1B8", "#9A9070", 0.45, c("Tinta_Negra"), "#1A1A1A")
    G = _esmalte(r, p, "Esmalte grafito", c("Grafito", "Tinta_Blanca"), "#1F2124", "#4A4C50", "#141517", 0.5, c("Tinta_Blanca"), "#C9C9C6", grano=True)
    if platina:
        f = r.capa(p + "Platina rayada por las probetas", G, {"baseColor": "#6A6C70", "roughness": 0.36, "metallic": 1, "height": -0.002}, opac=0.8)
        r.grunge(f, "Grunge Scratches Fine", 4)
        r.escaneo(f, 0.25, 0.7)
        r.mapa(f, "ZN_E_Platina", fusion="Multiply")
    _esmalte(r, p, "Plastico negro", c("Negro"), "#131314", "#2E2E30", "#0C0C0D", 0.4, grano=True)

    K = r.grupo(p + "Cromo", clases=c("Cromo"))
    r.capa(p + "Cromo satinado", K, {"baseColor": "#B8B9BB", "roughness": 0.24, "metallic": 1})
    f = r.capa(p + "Cromo: velo", K, {"baseColor": "#909192", "roughness": 0.42}, opac=0.5)
    r.grunge(f, "Clouds 2", 7)
    f = r.capa(p + "Cromo: huellas", K, {"baseColor": "#7C7A76", "roughness": 0.5}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.45, 0.4)

    for k, col in ANILLOS.items():
        A = r.grupo(p + "Anillo " + k, clases=c("Anillo_" + k))
        r.capa(p + "Anillo %s: laca" % k, A, {"baseColor": col, "roughness": 0.4, "metallic": 0})
        f = r.capa(p + "Anillo %s: gastado" % k, A, {"baseColor": "#8A8A88", "roughness": 0.5}, opac=0.3)
        r.grunge(f, "Grunge Scratches Fine", 8)
        r.escaneo(f, 0.3, 0.6)

    V = r.grupo(p + "Vidrio", clases=c("Vidrio"))
    r.capa(p + "Lente", V, {"baseColor": "#0A0C14", "roughness": 0.06, "metallic": 0})

    M = r.grupo(p + "Probeta", clases=c("Muestra"))
    r.capa(p + "Acero pulido a espejo", M, {"baseColor": "#B0AFAC", "roughness": 0.12, "metallic": 1})
    f = r.capa(p + "Probeta: ataque quimico", M, {"baseColor": "#7E7A70", "roughness": 0.3}, opac=0.5)
    r.grunge(f, "Clouds 2", 12)

    if p == "O_":
        # el high poly del ocular no tiene pieza dentro de la copa: el horneado de clases, desde ahi, acababa en el
        # cabezal blanco. Zona esferica que fuerza goma negra MATE: el aro claro que quedaba despues no era color,
        # era el reflejo especular del foco en una cara plana (textura medida: negra).
        Q = r.grupo(p + "Copas de los oculares")
        r.mapa(Q, "ZN_O_Copas")
        r.escaneo(Q, 0.92, 0.9)           # la zona cae suave: en el borde de la copa vale 0.17; con 0.5 quedaba fuera
        r.capa(p + "Copa: goma negra", Q, {"baseColor": "#0C0C0D", "roughness": 0.95, "metallic": 0})   # plana y de cara a la luz: a 0.55 devolvia el foco entero
    return r


def construir():
    return [_micro(Receta("LP_Estativo", "estativo LUMEQA"), "E_", platina=True),
            _micro(Receta("LP_Optica", "optica LUMEQA"), "O_")]
