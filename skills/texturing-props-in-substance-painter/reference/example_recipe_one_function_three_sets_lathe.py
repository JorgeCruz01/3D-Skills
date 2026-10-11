"""Look-dev del torno de banco FERDUX en Substance 3D Painter. Tres sets (bancada, carro, mandos) con los mismos
materiales: una sola funcion los pinta, con el prefijo de clases de cada set.

    python ../_herramientas/sp.py rehacer Torno_Banco

Aspecto: torno USADO, de taller (Jorge, 2026-10-10: los props que siguen a la guitarra van usados). Fundicion con
esmalte verde azulado: saltado en los cantos, con el hierro debajo, y oscurecido por la taladrina y el aceite donde
escurre. Guias y piezas rectificadas: acero brillante con pelicula de aceite, rayas a lo largo de la bancada (el
carro va y viene) y manchas pardas. Plato, garras, torreta y cuchilla pavonados, con el pavon gastado al acero en
los cantos. Bandeja de chapa negra con cercos de aceite y polvo de viruta. Mandos de baquelita negra con brillo de
dedos; seta roja; rotulos gastados.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo (`substance.por_set` + `sp_mascaras_sets.py`):
MK_{B,C,M}_{Esmalte, Chapa_Negra, Rectificado, Acero_Oscuro, Negro, Rojo, Tinta_Blanca}. Zonas ZN_B_Bandeja,
ZN_B_Plato. Campos CP_*_{B,C,M} (eje X: a lo largo de la bancada).
"""
from sp_receta import Receta

HIERRO = "#4A433D"
OXIDO = "#6E3B1E"
VERDE, VERDE_CLARO = "#08464F", "#2C7A85"
ACEITE = "#1A1309"
POLVO = "#6A655E"


def _torno(r, p, zonas=False):
    c = lambda *n: tuple(p + x for x in n)
    s = p[0]
    Z = r.grupo(p + "Fondo")
    r.capa(p + "Gris de fondo", Z, {"baseColor": "#1E1F21", "roughness": 0.5, "metallic": 0})

    F = r.grupo(p + "Fundicion esmaltada", clases=c("Esmalte"))
    r.capa(p + "Hierro fundido", F, {"baseColor": HIERRO, "roughness": 0.6, "metallic": 1})
    f = r.capa(p + "Hierro: oxido", F, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.5, 0.4)
    P = r.grupo(p + "Esmalte", dentro=F, clases=c("Esmalte"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.42, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    r.capa(p + "Verde azulado", P, {"baseColor": VERDE, "roughness": 0.4, "metallic": 0, "height": 0.005})
    f = r.capa(p + "Piel de naranja del esmalte", P, {"height": 0.002, "roughness": 0.46}, opac=0.7)
    r.grunge(f, "Gaussian Noise", 60)
    f = r.capa(p + "Tono desigual", P, {"baseColor": VERDE_CLARO, "roughness": 0.5}, opac=0.14)
    r.mapa(f, "CP_Manchas_" + s)
    r.escaneo(f, 0.45, 0.3)
    f = r.capa(p + "Oscurecido por la taladrina", P, {"baseColor": "#062E34", "roughness": 0.28}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa(p + "Aranazos claros", P, {"baseColor": VERDE_CLARO, "roughness": 0.55, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + "Desconchones al hierro", F, {"baseColor": HIERRO, "roughness": 0.6, "metallic": 1, "height": -0.005}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 5)
    r.mapa(f, "CP_Manchas_" + s, fusion="Multiply")
    r.escaneo(f, 0.1, 0.85)
    f = r.capa(p + "Aceite y viruta en rincones", F, {"baseColor": ACEITE, "roughness": 0.35}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.55, "grunge_amount": 0.85})

    G = r.grupo(p + "Rectificado", clases=c("Rectificado"))
    r.capa(p + "Acero rectificado", G, {"baseColor": "#7E7D7A", "roughness": 0.3, "metallic": 1})
    f = r.capa(p + "Rayas del carro", G, {"baseColor": "#9A9996", "roughness": 0.4, "height": -0.002}, opac=0.5)
    r.mapa(f, "CP_Rayado_Largo_" + s)
    r.escaneo(f, 0.4, 0.5)
    f = r.capa(p + "Pelicula de aceite", G, {"baseColor": "#5A4A30", "roughness": 0.18}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.45, 0.4)
    f = r.capa(p + "Manchas pardas", G, {"baseColor": "#5A3A22", "roughness": 0.6}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 8)
    r.mapa(f, "CP_Manchas_" + s, fusion="Multiply")
    r.escaneo(f, 0.2, 0.6)
    f = r.capa(p + "Rectificado: mugre en rincones", G, {"baseColor": ACEITE, "roughness": 0.45}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.55, "grunge_amount": 0.85})

    A = r.grupo(p + "Pavonado", clases=c("Acero_Oscuro"))
    r.capa(p + "Acero pavonado", A, {"baseColor": "#1B1C20", "roughness": 0.36, "metallic": 1})
    f = r.capa(p + "Pavon: velo", A, {"baseColor": "#26272B", "roughness": 0.5}, opac=0.6)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Pavon gastado en los cantos", A, {"baseColor": "#8A8986", "roughness": 0.3, "metallic": 1}, opac=0.85)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.35, "Wear_Contrast": 0.7, "Grunge_Amount": 0.7, "grunge_scale": 7})
    f = r.capa(p + "Pavon: aceite", A, {"baseColor": "#0F0C08", "roughness": 0.2}, opac=0.4)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.42, 0.4)

    C = r.grupo(p + "Chapa negra", clases=c("Chapa_Negra", "Tinta_Blanca"))
    r.capa(p + "Chapa: acero", C, {"baseColor": HIERRO, "roughness": 0.55, "metallic": 1})
    Q = r.grupo(p + "Chapa: pintura negra", dentro=C, clases=c("Chapa_Negra", "Tinta_Blanca"))
    r.gen(Q, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.35, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    r.capa(p + "Negro texturado", Q, {"baseColor": "#17181A", "roughness": 0.5, "metallic": 0, "height": 0.004})
    f = r.capa(p + "Negro: grano", Q, {"height": 0.002, "roughness": 0.58}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    r.capa(p + "Rotulos blancos", Q, {"baseColor": "#C9C9C6", "roughness": 0.5, "height": 0.0006}, clases=c("Tinta_Blanca"))
    f = r.capa(p + "Rotulos gastados", Q, {"baseColor": "#17181A", "roughness": 0.55}, opac=0.6, clases=c("Tinta_Blanca"))
    r.grunge(f, "Grunge Scratches Fine", 8)
    r.escaneo(f, 0.3, 0.6)
    if zonas:
        f = r.capa(p + "Cercos de aceite en la bandeja", C, {"baseColor": "#3A2A14", "roughness": 0.12}, opac=0.8)
        r.grunge(f, "Grunge Stains Heavy", 3)
        r.escaneo(f, 0.4, 0.35)
        r.mapa(f, "ZN_B_Bandeja", fusion="Multiply")
        f = r.capa(p + "Polvo de viruta", C, {"baseColor": "#8A8782", "roughness": 0.5, "metallic": 1, "height": 0.003}, opac=0.8)
        r.grunge(f, "Grunge Dirt", 9)          # BnW Spots 1 a escala 30 dejaba una reticula regular de puntos
        r.escaneo(f, 0.12, 0.85)
        r.mapa(f, "ZN_B_Bandeja", fusion="Multiply")
    f = r.capa(p + "Chapa: polvo", C, {"baseColor": POLVO, "roughness": 0.9}, opac=0.1)
    r.grunge(f, "Clouds 2", 6)

    N = r.grupo(p + "Baquelita", clases=c("Negro"))
    r.capa(p + "Baquelita negra", N, {"baseColor": "#141416", "roughness": 0.34, "metallic": 0})
    f = r.capa(p + "Baquelita: brillo de dedos", N, {"baseColor": "#1A1A1D", "roughness": 0.2}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.5, 0.4)
    f = r.capa(p + "Baquelita: mate", N, {"roughness": 0.5}, opac=0.4)
    r.grunge(f, "Clouds 2", 7)

    R = r.grupo(p + "Seta de paro", clases=c("Rojo"))
    r.capa(p + "Plastico rojo", R, {"baseColor": "#A8160F", "roughness": 0.32, "metallic": 0})
    f = r.capa(p + "Rojo: gastado", R, {"baseColor": "#C4564C", "roughness": 0.5}, opac=0.3)
    r.grunge(f, "Clouds 2", 8)
    return r


def construir():
    return [_torno(Receta("LP_Bancada", "bancada FERDUX"), "B_", zonas=True),
            _torno(Receta("LP_Carro", "carro FERDUX"), "C_"),
            _torno(Receta("LP_Mandos", "mandos FERDUX"), "M_")]
