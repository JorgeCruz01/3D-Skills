"""Look-dev del motor radial AERVOK R-7 en Substance 3D Painter. Tres sets (carter, soporte, cilindro) con los
mismos materiales: una sola funcion los pinta, con el prefijo de clases de cada set. Los siete cilindros comparten
UV (replicas): lo que se pinta en uno sale en todos, asi que ahi no hay manchas grandes con posicion propia.

    python ../_herramientas/sp.py rehacer Motor_Radial_7Cil

Aspecto: motor de aviacion USADO, desmontado y puesto en su banco de exposicion. Fundicion de aluminio gris con
flor de oxido blanco y aceite quemado pardo en los rincones; cilindros de acero pavonado con el calor marcado
(pardo, azulado) entre las aletas y los cantos gastados al acero; varillas de empuje y tubos de acero con pelicula
de aceite; anillo de encendido de cobre con patina; banco de chapa pintada en verde azulado, con desconchones,
goterones de aceite y los rotulos blancos.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{C,S,L}_{Aluminio, Soporte, Acero_Negro, Acero, Cobre, Tinta_Blanca}. Campos CP_*_{C,S,L}.
"""
from sp_receta import Receta

ACEITE = "#241808"
POLVO = "#7C776E"


def _motor(r, p):
    c = lambda *n: tuple(p + x for x in n)
    s = p[0]
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#2A2B2D", "roughness": 0.55, "metallic": 0})

    A = r.grupo(p + "Aluminio fundido", clases=c("Aluminio"))
    r.capa(p + "Aluminio", A, {"baseColor": "#7C7D7C", "roughness": 0.5, "metallic": 1})
    f = r.capa(p + "Aluminio: grano de fundicion", A, {"height": 0.004, "roughness": 0.58}, opac=0.8)
    r.grunge(f, "Gaussian Noise", 120)
    f = r.capa(p + "Aluminio: tono", A, {"baseColor": "#5E5F60", "roughness": 0.6}, opac=0.5)
    r.grunge(f, "Clouds 2", 5)
    f = r.capa(p + "Aluminio: flor blanca", A, {"baseColor": "#A8A9A4", "roughness": 0.8, "metallic": 0}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.12, 0.8)
    f = r.capa(p + "Aluminio: cantos pulidos", A, {"baseColor": "#B0B1B0", "roughness": 0.32, "metallic": 1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.25, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 8})
    f = r.capa(p + "Aluminio: aceite quemado", A, {"baseColor": ACEITE, "roughness": 0.4, "metallic": 0}, opac=0.75)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa(p + "Aluminio: chorretes", A, {"baseColor": ACEITE, "roughness": 0.25, "metallic": 0}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.3, 0.5)

    N = r.grupo(p + "Acero pavonado", clases=c("Acero_Negro"))
    r.capa(p + "Pavon", N, {"baseColor": "#1A1A1D", "roughness": 0.42, "metallic": 1})
    f = r.capa(p + "Pavon: calor pardo", N, {"baseColor": "#4A2E1A", "roughness": 0.55}, opac=0.6)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Pavon: calor azulado", N, {"baseColor": "#28324A", "roughness": 0.4}, opac=0.35)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.4, 0.4)
    f = r.capa(p + "Pavon: cantos al acero", N, {"baseColor": "#8A8986", "roughness": 0.34, "metallic": 1}, opac=0.8)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.28, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 8})
    f = r.capa(p + "Pavon: carbonilla", N, {"baseColor": "#0C0A08", "roughness": 0.8, "metallic": 0}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 9)          # entre aletas es todo hueco: Dirt saturaria
    r.escaneo(f, 0.35, 0.5)

    K = r.grupo(p + "Acero", clases=c("Acero"))
    r.capa(p + "Acero", K, {"baseColor": "#7E7D7A", "roughness": 0.3, "metallic": 1})
    f = r.capa(p + "Acero: aceite", K, {"baseColor": "#5A4A30", "roughness": 0.2}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Acero: manchas", K, {"baseColor": "#3E3226", "roughness": 0.6}, opac=0.45)
    r.grunge(f, "Grunge Dirt", 10)
    r.escaneo(f, 0.25, 0.6)

    U = r.grupo(p + "Cobre", clases=c("Cobre"))
    r.capa(p + "Cobre", U, {"baseColor": "#A8603A", "roughness": 0.36, "metallic": 1})
    f = r.capa(p + "Cobre: patina parda", U, {"baseColor": "#4A2E20", "roughness": 0.6}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Cobre: verdin", U, {"baseColor": "#4E7A66", "roughness": 0.8, "metallic": 0}, opac=0.45)
    r.grunge(f, "Grunge Dirt", 14)
    r.escaneo(f, 0.1, 0.8)

    B = r.grupo(p + "Banco", clases=c("Soporte", "Tinta_Blanca"))
    r.capa(p + "Banco: chapa", B, {"baseColor": "#4A433D", "roughness": 0.6, "metallic": 1})
    f = r.capa(p + "Banco: oxido", B, {"baseColor": "#6E3B1E", "roughness": 0.85, "metallic": 0}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.5, 0.4)
    P = r.grupo(p + "Banco: pintura", dentro=B, clases=c("Soporte", "Tinta_Blanca"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.36, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    r.capa(p + "Verde azulado", P, {"baseColor": "#08464F", "roughness": 0.5, "metallic": 0, "height": 0.005})
    f = r.capa(p + "Banco: piel", P, {"height": 0.002, "roughness": 0.56}, opac=0.7)
    r.grunge(f, "Gaussian Noise", 60)
    f = r.capa(p + "Banco: tono desigual", P, {"baseColor": "#2C7A85", "roughness": 0.55}, opac=0.15)
    r.mapa(f, "CP_Manchas_" + s)
    r.escaneo(f, 0.45, 0.3)
    r.capa(p + "Rotulos blancos", P, {"baseColor": "#CFCFCA", "roughness": 0.5, "height": 0.0006}, clases=c("Tinta_Blanca"))
    f = r.capa(p + "Banco: aranazos", P, {"baseColor": "#2C7A85", "roughness": 0.6, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + "Banco: goterones de aceite", B, {"baseColor": ACEITE, "roughness": 0.16, "metallic": 0}, opac=0.7)
    r.grunge(f, "Grunge Stains Heavy", 3)
    r.escaneo(f, 0.3, 0.45)
    f = r.capa(p + "Banco: polvo", B, {"baseColor": POLVO, "roughness": 0.92, "metallic": 0}, opac=0.1)
    r.grunge(f, "Clouds 2", 5)
    return r


def construir():
    return [_motor(Receta("LP_Carter", "carter AERVOK"), "C_"),
            _motor(Receta("LP_Soporte", "banco AERVOK"), "S_"),
            _motor(Receta("LP_Cilindro", "cilindro AERVOK"), "L_")]
