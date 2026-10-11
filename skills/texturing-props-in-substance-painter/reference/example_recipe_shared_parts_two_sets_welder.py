"""Look-dev de la soldadora MIG SOLDIK en Substance 3D Painter. Dos sets: la carcasa (chapa, marcos, puerta) y los
componentes (bobina, arrastre, mandos, conectores, pantalla).

    python ../_herramientas/sp.py rehacer Soldadora_MIG

Aspecto: soldadora USADA, de taller (Jorge, 2026-10-10: los props que siguen a la guitarra van usados). Chapa
pintada de verde azulado, mate y con el polvo gris del taller posado arriba; salpicaduras de soldadura (puntos
oscuros quemados) en la tapa y en el frente; cantos pelados al acero y pies rozados; asa con el plastico pulido por
la mano. Marcos de plastico gris oscuro con roces claros. Mandos con brillo de dedos; euroconector de laton
oscurecido; tomas Dinse con polvo; bobina de plastico negro con el hilo cobreado; rodillos de acero pulidos por el
hilo; pantalla con velo.

Mascaras (Texturas/Bakes/Mascaras/), por set y con prefijo: MK_C_* (Chapa, Marco, Puerta, Tinta_Blanca), MK_K_*
(Negro, Hilo, Buje, Acero, Mando, Euro, Dinse_Rojo, Dinse_Negro, Cristal, Interruptor, Prensa, Gas, Tinta_Roja).
Zonas ZN_C_Arriba, ZN_C_Asa, ZN_C_Pie, ZN_K_Dedos. Campos CP_*_C, CP_*_K.
"""
from sp_receta import Receta

POLVO = "#8C8880"            # polvo de taller: gris de amolar, no beige
ACERO = "#5A5653"
OXIDO = "#74401F"
VERDE, VERDE_CLARO = "#07454E", "#2C7A85"       # con #0C5F6B y las capas claras encima salia pastel
MUGRE = "#17130F"


def carcasa():
    r = Receta("LP_Carcasa", "carcasa SOLDIK")
    Z = r.grupo("Fondo")
    r.capa("Gris de fondo", Z, {"baseColor": "#1F2022", "roughness": 0.55, "metallic": 0})

    C = r.grupo("Chapa pintada", clases=("C_Chapa", "C_Puerta"))
    r.capa("Acero", C, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1})
    f = r.capa("Acero: oxido", C, {"baseColor": OXIDO, "roughness": 0.85}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.5, 0.4)
    P = r.grupo("Pintura verde azulada", dentro=C, clases=("C_Chapa", "C_Puerta"))
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.4, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 7}, fusion="Multiply")
    # roughness 0.5: la tapa publicada reventaba bajo la luz cenital
    r.capa("Esmalte", P, {"baseColor": VERDE, "roughness": 0.5, "metallic": 0, "height": 0.004})
    f = r.capa("Tono desigual", P, {"baseColor": VERDE_CLARO, "roughness": 0.6}, opac=0.15)
    r.mapa(f, "CP_Manchas_C")
    r.escaneo(f, 0.45, 0.3)
    f = r.capa("Mate del uso", P, {"roughness": 0.68}, opac=0.6)
    r.grunge(f, "Grunge Stains Heavy", 4)
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Aranazos claros", P, {"baseColor": VERDE_CLARO, "roughness": 0.6, "height": -0.002}, opac=0.55)
    r.grunge(f, "Grunge Scratches Fine", 4)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Aranazos de la tapa", P, {"baseColor": "#7FB3BA", "roughness": 0.62, "height": -0.003}, opac=0.7)
    r.grunge(f, "Grunge Scratches Dirty", 5)
    r.escaneo(f, 0.2, 0.8)
    r.mapa(f, "ZN_C_Arriba", fusion="Multiply")
    f = r.capa("Salpicaduras de soldadura", C, {"baseColor": "#1A1512", "roughness": 0.7, "metallic": 0, "height": 0.006}, opac=0.95)
    r.grunge(f, "BnW Spots 1", 18)
    r.escaneo(f, 0.05, 0.92)          # posicion mayor = mas blanco: con 0.9 la capa cubria toda la chapa (parda)
    r.mapa(f, "ZN_C_Arriba", fusion="Multiply")
    f = r.capa("Cerco quemado de las salpicaduras", C, {"baseColor": "#3A2A1A", "roughness": 0.75}, opac=0.5)
    r.grunge(f, "BnW Spots 1", 18)
    r.escaneo(f, 0.1, 0.6)
    r.mapa(f, "ZN_C_Arriba", fusion="Multiply")
    f = r.capa("Pies y cantos de abajo rozados", C, {"baseColor": ACERO, "roughness": 0.5, "metallic": 1, "height": -0.004}, opac=0.95)
    r.grunge(f, "Grunge Dirt", 7)
    r.escaneo(f, 0.4, 0.7)
    r.mapa(f, "ZN_C_Pie", fusion="Multiply")
    f = r.capa("Mugre en rincones", C, {"baseColor": MUGRE, "roughness": 0.8}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.25, "dirt_contrast": 0.55, "grunge_amount": 0.85})
    f = r.capa("Polvo de amolar posado", C, {"baseColor": "#5E5B56", "roughness": 0.92}, opac=0.16)
    r.grunge(f, "Clouds 2", 4)
    r.mapa(f, "ZN_C_Arriba", fusion="Multiply")
    f = r.capa("Polvo fino", C, {"baseColor": POLVO, "roughness": 0.92}, opac=0.07)
    r.grunge(f, "Clouds 2", 6)

    M = r.grupo("Marcos y asa", clases=("C_Marco", "C_Tinta_Blanca"))
    r.capa("Plastico gris oscuro", M, {"baseColor": "#1E2023", "roughness": 0.55, "metallic": 0})
    f = r.capa("Marco: grano", M, {"height": 0.002, "roughness": 0.62}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    r.capa("Rotulos blancos", M, {"baseColor": "#C9C9C6", "roughness": 0.5, "height": 0.0006}, clases=("C_Tinta_Blanca",))
    f = r.capa("Rotulos gastados", M, {"baseColor": "#26282B", "roughness": 0.55}, opac=0.6, clases=("C_Tinta_Blanca",))
    r.grunge(f, "Grunge Scratches Fine", 8)
    r.escaneo(f, 0.3, 0.6)
    f = r.capa("Marco: roces claros", M, {"baseColor": "#5E6064", "roughness": 0.66, "height": -0.002}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Marco: cantos gastados", M, {"baseColor": "#3D3F43", "roughness": 0.45}, opac=0.6)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.1, "Wear_Contrast": 0.8, "Grunge_Amount": 0.2, "grunge_scale": 7})
    f = r.capa("Asa pulida por la mano", M, {"baseColor": "#222427", "roughness": 0.28}, opac=0.8)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.5, 0.4)
    r.mapa(f, "ZN_C_Asa", fusion="Multiply")
    f = r.capa("Marco: polvo", M, {"baseColor": "#5E5B56", "roughness": 0.9}, opac=0.1)
    r.grunge(f, "Clouds 2", 7)
    _piezas(r, "C_")
    return r


def _piezas(r, p):
    """Mandos, conectores, bobina y pantalla. `p` = prefijo de las clases del set: estas piezas caen en los dos sets
    (el mapa de clases de la carcasa las ve como Negro, Rojo, Laton... y el de componentes, por pieza)."""
    c = lambda *n: tuple(p + x for x in n)

    N = r.grupo(p + "Plasticos negros", clases=c("Negro", "Buje", "Mando", "Dinse_Negro", "Prensa") if p == "K_" else c("Negro"))
    r.capa(p + "Plastico negro", N, {"baseColor": "#17171A", "roughness": 0.5, "metallic": 0})
    f = r.capa(p + "Negro: grano", N, {"height": 0.0015, "roughness": 0.58}, opac=0.8)
    r.grunge(f, "White Noise Fast", 1)
    f = r.capa(p + "Negro: gris de uso", N, {"baseColor": "#3A3B3F", "roughness": 0.68}, opac=0.14)
    r.grunge(f, "Clouds 2", 6)
    f = r.capa(p + "Mandos: brillo de dedos", N, {"baseColor": "#1C1C1F", "roughness": 0.26}, opac=0.7, clases=c("Mando") if p == "K_" else ())
    r.grunge(f, "Grunge Stains Heavy", 6)
    r.escaneo(f, 0.5, 0.4)
    f = r.capa(p + "Negro: polvo", N, {"baseColor": "#5E5B56", "roughness": 0.9}, opac=0.1)
    r.grunge(f, "Clouds 2", 8)

    H = r.grupo(p + "Hilo cobreado", clases=c("Hilo"))
    r.capa(p + "Acero cobreado", H, {"baseColor": "#B8743E", "roughness": 0.3, "metallic": 1})
    f = r.capa(p + "Hilo: espiras", H, {"baseColor": "#7A4A26", "roughness": 0.45, "height": -0.004}, opac=0.6)
    r.mapa(f, "CP_Junta_" + p[0])
    f = r.capa(p + "Hilo: oxido del cobre", H, {"baseColor": "#5E4A36", "roughness": 0.6}, opac=0.35)
    r.grunge(f, "Clouds 2", 8)
    r.escaneo(f, 0.55, 0.3)

    A = r.grupo(p + "Arrastre", clases=c("Acero"))
    r.capa(p + "Acero", A, {"baseColor": "#8F8E8B", "roughness": 0.3, "metallic": 1})
    f = r.capa(p + "Acero: velo", A, {"roughness": 0.5}, opac=0.6)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa(p + "Acero: polvo de cobre y grasa", A, {"baseColor": "#3A2B1E", "roughness": 0.6}, opac=0.5)
    r.grunge(f, "Grunge Stains Heavy", 7)
    r.escaneo(f, 0.42, 0.4)

    L = r.grupo(p + "Laton", clases=c("Euro", "Gas") if p == "K_" else c("Laton"))
    r.capa(p + "Laton", L, {"baseColor": "#A8843C", "roughness": 0.32, "metallic": 1})
    f = r.capa(p + "Laton: patina", L, {"baseColor": "#4E3B1C", "roughness": 0.62}, opac=0.65)
    r.grunge(f, "Clouds 2", 6)
    r.escaneo(f, 0.5, 0.3)
    f = r.capa(p + "Laton: contacto pulido", L, {"baseColor": "#C9A452", "roughness": 0.2, "metallic": 1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.6, "Grunge_Amount": 0.5, "grunge_scale": 6})

    R = r.grupo(p + "Rojos", clases=c("Dinse_Rojo", "Interruptor") if p == "K_" else c("Rojo"))
    r.capa(p + "Plastico rojo", R, {"baseColor": "#A51A14", "roughness": 0.4, "metallic": 0})
    f = r.capa(p + "Rojo: gastado", R, {"baseColor": "#C4564C", "roughness": 0.6}, opac=0.35)
    r.grunge(f, "Clouds 2", 8)
    f = r.capa(p + "Rojo: polvo", R, {"baseColor": POLVO, "roughness": 0.92}, opac=0.2)
    r.grunge(f, "Clouds 2", 9)

    V = r.grupo(p + "Pantalla", clases=c("Cristal", "Tinta_Roja"))
    r.capa(p + "Cristal ahumado", V, {"baseColor": "#0A0A0C", "roughness": 0.1, "metallic": 0})
    r.capa(p + "Lectura", V, {"baseColor": "#E8402C", "roughness": 0.3}, clases=c("Tinta_Roja"))
    f = r.capa(p + "Pantalla: velo", V, {"baseColor": "#3A3A3C", "roughness": 0.3}, opac=0.4)
    r.grunge(f, "Grunge Stains Heavy", 5)
    r.escaneo(f, 0.42, 0.4)




def componentes():
    r = Receta("LP_Componentes", "componentes SOLDIK")
    Z = r.grupo("Fondo K")
    r.capa("Negro de fondo K", Z, {"baseColor": "#151517", "roughness": 0.55, "metallic": 0})
    _piezas(r, "K_")
    # la chapa y los marcos que este set ve por detras de sus piezas
    X = r.grupo("K: chapa vista", clases=("K_Chapa",))
    r.capa("K: esmalte", X, {"baseColor": VERDE, "roughness": 0.55, "metallic": 0})
    Y = r.grupo("K: marco visto", clases=("K_Marco",))
    r.capa("K: plastico gris", Y, {"baseColor": "#26282B", "roughness": 0.55, "metallic": 0})
    return r


def construir():
    return [carcasa(), componentes()]
