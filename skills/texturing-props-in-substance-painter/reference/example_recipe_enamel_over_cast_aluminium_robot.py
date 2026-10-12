"""Look-dev del brazo robotico KINMARQ en Substance 3D Painter. Dos sets (brazo, muneca) con los mismos materiales:
una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py rehacer Brazo_Robotico_6Ejes

Aspecto: robot USADO, de celula de fabrica con anos de turnos. Fundicion de aluminio con esmalte naranja semimate:
saltado al aluminio en los cantos, con roces oscuros de mangueras y golpes de utillaje, grasa parda que rezuma en
las juntas de cada eje y polvo de taller. Esmalte grafito texturado en base, muneca y tapas. Brida de acero con la
pelicula de aceite. Pinza de aluminio mecanizado, rayada donde agarra. Rotulos blancos algo gastados.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{B,M}_{Grafito, Naranja, Acero, Aluminio, Tinta_Blanca}. Campos CP_*_{B,M}.

El esmalte va a rugosidad 0.5: son cilindros anchos bajo luz cenital.
"""
from sp_receta import Receta

ALUMINIO = "#8C8E90"
GRASA = "#2A1E10"
POLVO = "#7C776E"


def _esmalte(r, p, nombre, cl, color, claro, oscuro, desgaste, tinta=None, grano=False):
    s = p[0]
    F = r.grupo(p + nombre + ": fundicion", clases=cl)
    r.capa(p + nombre + ": aluminio fundido", F, {"baseColor": ALUMINIO, "roughness": 0.5, "metallic": 1})
    P = r.grupo(p + nombre + ": esmalte", dentro=F, clases=cl)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": desgaste, "Wear_Contrast": 0.75, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    r.capa(p + nombre + ": color", P, {"baseColor": color, "roughness": 0.5, "metallic": 0, "height": 0.005})
    f = r.capa(p + nombre + ": piel", P, {"height": 0.002, "roughness": 0.56}, opac=0.7)
    r.grunge(f, "White Noise Fast" if grano else "Gaussian Noise", 1 if grano else 60)
    f = r.capa(p + nombre + ": tono desigual", P, {"baseColor": claro, "roughness": 0.55}, opac=0.16)
    r.mapa(f, "CP_Manchas_" + s)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa(p + nombre + ": brillo de limpieza", P, {"roughness": 0.3}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.45, 0.4)
    if tinta:
        r.capa(p + nombre + ": rotulos", P, {"baseColor": "#D2D2CD", "roughness": 0.5, "height": 0.0006}, clases=tinta)
        f = r.capa(p + nombre + ": rotulos gastados", P, {"baseColor": color, "roughness": 0.5}, opac=0.25, clases=tinta)
        r.grunge(f, "Grunge Scratches Fine", 8)
        r.escaneo(f, 0.3, 0.6)
    f = r.capa(p + nombre + ": roces oscuros", P, {"baseColor": oscuro, "roughness": 0.6, "height": -0.002}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + nombre + ": desconchones", F, {"baseColor": ALUMINIO, "roughness": 0.45, "metallic": 1, "height": -0.005}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 5)
    r.mapa(f, "CP_Manchas_" + s, fusion="Multiply")
    r.escaneo(f, 0.06, 0.9)
    f = r.capa(p + nombre + ": grasa en juntas", F, {"baseColor": GRASA, "roughness": 0.3}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.26, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa(p + nombre + ": motas", F, {"baseColor": GRASA, "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 6)
    r.escaneo(f, 0.05, 0.88)
    f = r.capa(p + nombre + ": polvo", F, {"baseColor": POLVO, "roughness": 0.92}, opac=0.08)
    r.grunge(f, "Clouds 2", 5)


def _brazo(r, p):
    c = lambda *n: tuple(p + x for x in n)
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#222325", "roughness": 0.55, "metallic": 0})

    _esmalte(r, p, "Naranja", c("Naranja", "Tinta_Blanca"), "#C4500C", "#D8742E", "#3A2414", 0.32, tinta=c("Tinta_Blanca"))
    _esmalte(r, p, "Grafito", c("Grafito"), "#1C1D20", "#34363A", "#0E0E0F", 0.28, grano=True)

    A = r.grupo(p + "Brida", clases=c("Acero"))
    r.capa(p + "Acero mecanizado", A, {"baseColor": "#7E7D7A", "roughness": 0.32, "metallic": 1})
    f = r.capa(p + "Acero: aceite", A, {"baseColor": "#5A4A30", "roughness": 0.2}, opac=0.45)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Acero: manchas", A, {"baseColor": "#3E3226", "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.25, 0.6)

    L = r.grupo(p + "Pinza", clases=c("Aluminio"))
    r.capa(p + "Aluminio mecanizado", L, {"baseColor": "#9A9C9E", "roughness": 0.36, "metallic": 1})
    f = r.capa(p + "Aluminio: rayas de agarre", L, {"baseColor": "#C0C2C4", "roughness": 0.28, "height": -0.002}, opac=0.6)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.25, 0.7)
    f = r.capa(p + "Aluminio: velo", L, {"baseColor": "#6E7072", "roughness": 0.52}, opac=0.45)
    r.grunge(f, "Clouds 2", 7)
    f = r.capa(p + "Aluminio: mugre", L, {"baseColor": GRASA, "roughness": 0.6, "metallic": 0}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 8)
    r.escaneo(f, 0.2, 0.6)
    return r


def construir():
    return [_brazo(Receta("LP_Brazo", "brazo KINMARQ"), "B_"),
            _brazo(Receta("LP_Muneca", "muneca KINMARQ"), "M_")]
