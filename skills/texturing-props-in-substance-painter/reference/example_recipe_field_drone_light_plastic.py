"""Look-dev del dron de inspeccion TREVAQ en Substance 3D Painter. Dos sets (fuselaje, rotores) con los mismos
materiales: una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py rehacer Dron_Inspeccion

Aspecto: dron USADO, de trabajo en campo. Carcasa de plastico gris claro con grano de inyeccion, roces y aranazos
de transporte, polvo de tierra pegado en las patas y en la panza; plastico grafito con velo de polvo; helices con
el borde picado y las puntas naranjas saltadas; motores de aluminio anodizado con polvo en las ranuras; cupula del
GPS blanca algo amarilleada; lentes oscuras; rotulos algo gastados.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{F,R}_{Carcasa, Grafito, Vidrio, Aluminio, Naranja, Blanco, Tinta_Blanca, Tinta_Verde, Tinta_Negra}.
Zonas ZN_F_Patas, ZN_R_Patas (tierra donde aterriza). Campos CP_*_{F,R}.

Rugosidades de 0.5 para arriba en los plasticos: son superficies anchas de cara a la luz cenital.
"""
from sp_receta import Receta

TIERRA = "#6E5E48"
POLVO = "#7C776E"


def _plastico(r, p, nombre, cl, color, claro, rug, tintas=()):
    G = r.grupo(p + nombre, clases=cl)
    r.capa(p + nombre + ": base", G, {"baseColor": color, "roughness": rug, "metallic": 0})
    f = r.capa(p + nombre + ": grano de inyeccion", G, {"height": 0.0015, "roughness": rug + 0.08}, opac=0.7)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa(p + nombre + ": brillo de manos", G, {"roughness": rug - 0.2}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)
    for clase, col in tintas:
        r.capa(p + nombre + ": rotulo " + clase, G, {"baseColor": col, "roughness": 0.5}, clases=(p + clase,))
    f = r.capa(p + nombre + ": aranazos", G, {"baseColor": claro, "roughness": rug + 0.12, "height": -0.002}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.13, 0.85)
    f = r.capa(p + nombre + ": cantos rozados", G, {"baseColor": claro, "roughness": rug + 0.1}, opac=0.55)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.2, "Wear_Contrast": 0.7, "Grunge_Amount": 0.85, "grunge_scale": 8})
    f = r.capa(p + nombre + ": polvo en rincones", G, {"baseColor": TIERRA, "roughness": 0.92}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.24, "dirt_contrast": 0.5, "grunge_amount": 0.85})
    f = r.capa(p + nombre + ": mugre de campo", G, {"baseColor": "#4E483E", "roughness": 0.85}, opac=0.35)
    r.grunge(f, "Grunge Dirt", 4)
    r.escaneo(f, 0.06, 0.85)        # con 0.3 la mugre cubria todo y el plastico parecia piedra
    f = r.capa(p + nombre + ": velo de polvo", G, {"baseColor": POLVO, "roughness": 0.9}, opac=0.1)
    r.grunge(f, "Clouds 2", 5)
    f = r.capa(p + nombre + ": tierra del aterrizaje", G, {"baseColor": TIERRA, "roughness": 0.95, "height": 0.002}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.6, 0.4)
    r.mapa(f, "ZN_%s_Patas" % p[0], fusion="Multiply")
    return G


def _dron(r, p):
    c = lambda *n: tuple(p + x for x in n)
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#2A2B2D", "roughness": 0.55, "metallic": 0})

    _plastico(r, p, "Carcasa", c("Carcasa", "Tinta_Negra", "Tinta_Verde"), "#8E9394", "#5E6264", 0.52,
              (("Tinta_Negra", "#1A1B1C"), ("Tinta_Verde", "#1F8A4A")))
    _plastico(r, p, "Grafito", c("Grafito", "Tinta_Blanca"), "#1D1F22", "#4A4D52", 0.55, (("Tinta_Blanca", "#C9C9C6"),))
    _plastico(r, p, "Punta naranja", c("Naranja"), "#D8601A", "#3A3C40", 0.5)
    _plastico(r, p, "Cupula", c("Blanco"), "#B9B7AC", "#A39A78", 0.5)

    A = r.grupo(p + "Aluminio", clases=c("Aluminio"))
    r.capa(p + "Aluminio anodizado", A, {"baseColor": "#5E6670", "roughness": 0.36, "metallic": 1})
    f = r.capa(p + "Aluminio: velo", A, {"baseColor": "#787C82", "roughness": 0.5}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa(p + "Aluminio: cantos al metal", A, {"baseColor": "#B4B6B8", "roughness": 0.3, "metallic": 1}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.25, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 8})
    f = r.capa(p + "Aluminio: polvo en ranuras", A, {"baseColor": TIERRA, "roughness": 0.92, "metallic": 0}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.3, 0.5)

    V = r.grupo(p + "Vidrio", clases=c("Vidrio"))
    r.capa(p + "Lente", V, {"baseColor": "#07080C", "roughness": 0.08, "metallic": 0})
    f = r.capa(p + "Lente: polvo", V, {"baseColor": POLVO, "roughness": 0.4}, opac=0.05)
    r.grunge(f, "Clouds 2", 9)
    return r


def construir():
    return [_dron(Receta("LP_Fuselaje", "fuselaje TREVAQ"), "F_"),
            _dron(Receta("LP_Rotores", "rotores TREVAQ"), "R_")]
