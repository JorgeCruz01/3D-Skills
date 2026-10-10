"""Look-dev del subfusil compacto VOSTREL en Substance 3D Painter.

    python ../_herramientas/sp.py importar Subfusil_Compacto Texturas/Fuente/Wood049/Wood049_2K-JPG_Color.jpg (+ Roughness, NormalGL)
    python ../_herramientas/sp.py rehacer Subfusil_Compacto vistas_sp.json

Aspecto: arma de dotacion con muchos anos de funda y de armero. Chapa estampada pavonada, gris negra, comida a acero en
los cantos, en las crestas de los nervios y alrededor del tirador; armazon mas oscuro; cargador mas gris y rayado a lo
alto de meterlo y sacarlo; varilla de la culata rozada donde apoya. Empunadura de haya barnizada, amarilla, con el
barniz gastado en las crestas de los surcos y oscurecida por la mano.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y por pieza; ZN_ zonas de uso (Mano, Boca, Accion, Apoyo);
CP_Rayado_Largo a lo largo del canon; CP_*_Veta con el eje VERTICAL (veta de la empunadura y rayado del cargador);
CP_Relieve_* crestas y fondos del relieve (nervios, ranura, cajeados, surcos), de la normal de Blender.
"""
from sp_receta import Receta

SET = "LP_Subfusil"
PAVONADO = ("Chapa", "Armazon", "Cargador", "Canon", "Mandos", "Herrajes", "Varilla", "Reten")
VETA = {"mode": "Triplanar", "scale": 5.0, "rotation": 90}


def acero(r):
    A = r.grupo("Acero", clases=PAVONADO + ("Acero_Rozado",))
    r.capa("Acero base", A, {"baseColor": "#B4B5B8", "roughness": 0.32, "metallic": 1})
    f = r.capa("Acero rectificado", A, {"baseColor": "#9E9FA3", "roughness": 0.48})
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.5, 0.5)

    P = r.grupo("Pavonado", dentro=A, clases=PAVONADO)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.3, "Wear_Contrast": 0.7, "Grunge_Amount": 0.4, "grunge_scale": 4}, fusion="Multiply")
    # una varilla de 5 mm es "toda canto" para el generador: se le devuelve la mayor parte del pavon
    r.mapa(P, "MK_Varilla", fusion="LinearDodge", opac=0.7)
    r.capa("Pavon", P, {"baseColor": "#17191C", "roughness": 0.4, "metallic": 1})
    r.capa("Chapa: pavon mas gris y mate", P, {"baseColor": "#24272A", "roughness": 0.48}, opac=0.85, clases=("Chapa",))
    r.capa("Cargador: fosfatado gris", P, {"baseColor": "#2E3130", "roughness": 0.52}, opac=0.9, clases=("Cargador",))
    r.capa("Varilla: pavon negro", P, {"baseColor": "#121315", "roughness": 0.36}, opac=0.8, clases=("Varilla",))
    f = r.capa("Pavon gastado a gris", P, {"baseColor": "#3C3D40", "roughness": 0.46}, opac=0.6)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.4, 0.3)
    r.grunge(f, "Grunge Dirt Scratched", 6, fusion="Multiply")
    f = r.capa("Pavon velo pardo", P, {"baseColor": "#2E2620", "roughness": 0.5}, opac=0.35)
    r.grunge(f, "Clouds 2", 5)
    f = r.capa("Aceite y huellas", P, {"roughness": 0.2}, opac=0.55)
    r.grunge(f, "Grunge Fingerprints Smeared", 6)
    f = r.capa("Mate de polvo", P, {"roughness": 0.62}, opac=0.4)
    r.grunge(f, "Grunge Dirt", 8)

    # relieve estampado: crestas de los nervios y cantos de ranura y cajeados comidos a acero; fondo sucio
    f = r.capa("Relieve: cresta comida", A, {"baseColor": "#A9AAAE", "roughness": 0.3, "metallic": 1}, opac=0.8)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.45, 0.5)
    r.grunge(f, "Grunge Dirt", 5, fusion="Multiply")
    f = r.capa("Relieve: fondo con grasa", A, {"baseColor": "#0C0B0A", "roughness": 0.34}, opac=0.75)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.55, 0.4)
    f = r.capa("Aranazos largos", A, {"baseColor": "#9A9BA0", "roughness": 0.34, "metallic": 1, "height": -0.008}, opac=0.75)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.02, 0.9)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    f = r.capa("Cargador: rayas de meterlo y sacarlo", A, {"baseColor": "#9C9DA1", "roughness": 0.36, "metallic": 1}, opac=0.55, clases=("Cargador",))
    r.mapa(f, "CP_Rayado_Largo_Veta", fusion="Multiply")
    r.escaneo(f, 0.06, 0.85)
    # lo que solo pasa en un sitio
    f = r.capa("Accion: tirador y ranura blanqueados", A, {"baseColor": "#B4B5B8", "roughness": 0.26, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.65, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 8})
    r.mapa(f, "ZN_Accion", fusion="Multiply")
    r.escaneo(f, 0.32, 0.5)
    f = r.capa("Mano: pavon pulido", A, {"baseColor": "#47484C", "roughness": 0.24, "metallic": 1}, opac=0.6, clases=("Cargador", "Mandos", "Herrajes"))
    r.mapa(f, "ZN_Mano", fusion="Multiply")
    r.grunge(f, "Grunge Fingerprints Smeared", 6.0, fusion="Multiply")
    f = r.capa("Boca: corona blanqueada", A, {"baseColor": "#B4B5B8", "roughness": 0.3, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.6, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 10})
    r.mapa(f, "ZN_Boca", fusion="Multiply")
    r.escaneo(f, 0.2, 0.5)
    f = r.capa("Boca: hollin", A, {"baseColor": "#0B0B0B", "roughness": 0.85}, opac=0.6)
    r.mapa(f, "ZN_Boca")
    r.grunge(f, "Grunge Dusty Powder Soft", 6.0, fusion="Multiply")
    r.escaneo(f, 0.36, 0.3)
    f = r.capa("Apoyo: pavon comido", A, {"baseColor": "#8E8F93", "roughness": 0.38, "metallic": 1}, opac=0.85)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Dirty", 5, fusion="Multiply")
    r.escaneo(f, 0.26, 0.6)
    f = r.capa("Aranazos finos al azar", A, {"baseColor": "#6E6F74", "roughness": 0.5}, opac=0.55)
    r.grunge(f, "Grunge Scratches Fine", 4.5)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Picaduras de oxido", A, {"baseColor": "#4A2A16", "roughness": 0.9, "height": 0.004}, opac=0.45)
    r.grunge(f, "Grunge Rust Fine", 7)
    r.escaneo(f, 0.1, 0.8)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    # reten del cargador: una pala plana dentro del cajeado. Su mascara, su filete y su normal plana salen del panel
    # dibujado (`sp_paneles.py --aplanar`): horneado tal cual, el borde salia en dientes de sierra
    r.capa("Reten: pala pavonada", A, {"baseColor": "#1D1F22", "roughness": 0.42, "metallic": 1}, clases=("Reten",))
    f = r.capa("Reten: pulido por el dedo", A, {"baseColor": "#5A5B5F", "roughness": 0.26, "metallic": 1}, opac=0.7, clases=("Reten",))
    r.grunge(f, "Grunge Fingerprints Smeared", 9.0, fusion="Multiply")
    f = r.capa("Reten: rayas", A, {"baseColor": "#8E8F93", "roughness": 0.34, "metallic": 1}, opac=0.6, clases=("Reten",))
    r.mapa(f, "CP_Rayado_Largo", fusion="Multiply")
    r.escaneo(f, 0.08, 0.9)
    f = r.capa("Reten: holgura en sombra", A, {"baseColor": "#070707", "roughness": 0.5, "height": -0.03}, opac=0.95)
    r.mapa(f, "BD_Reten")
    # interior de la ranura y de la ventana: acero rozado por el cierre
    r.capa("Acero rozado", A, {"baseColor": "#8C8D90", "roughness": 0.36, "metallic": 1}, clases=("Acero_Rozado",))
    f = r.capa("Acero rozado: rayas", A, {"baseColor": "#B2B3B6", "roughness": 0.28}, clases=("Acero_Rozado",))
    r.mapa(f, "CP_Rayado_Largo", fusion="Multiply")
    f = r.capa("Acero rozado: grasa", A, {"baseColor": "#17120D", "roughness": 0.3}, opac=0.55, clases=("Acero_Rozado",))
    r.grunge(f, "Grunge Dirt", 6.0, fusion="Multiply")
    f = r.capa("Oxido en rincones", A, {"baseColor": "#3D2516", "roughness": 0.85}, opac=0.2)        # a 0.45 llenaba de pardo el cajeado del reten
    r.gen(f, "Dirt", {"dirt_level": 0.06, "dirt_contrast": 0.8, "grunge_amount": 0.95})
    f = r.capa("Polvo en huecos", A, {"baseColor": "#4E4840", "roughness": 0.85}, opac=0.22)       # a 0.4 y claro, el cajeado del reten salia como una losa beige
    r.gen(f, "Dirt", {"dirt_level": 0.2, "dirt_contrast": 0.5, "grunge_amount": 0.6})


def madera(r):
    M = r.grupo("Haya", clases=("Haya",))
    tex = lambda m: {"resource": "Wood049_2K-JPG_" + m, "usage": "texture"}
    r.capa("Haya base", M, {"baseColor": tex("Color"), "roughness": tex("Roughness"), "normal": tex("NormalGL"), "metallic": 0}, proy=VETA,
           opac={"normal": 0.1})
    r.capa("Haya: barniz amarillo", M, {"baseColor": "#D9972F"}, opac=0.9, fusion="Multiply")
    f = r.capa("Veta oscura", M, {"baseColor": "#5A2F0C"}, opac=0.35)
    r.mapa(f, "CP_Rayado_Largo_Veta")
    r.escaneo(f, 0.4, 0.25)
    f = r.capa("Aguas claras", M, {"baseColor": "#E8B45C"}, opac=0.25)
    r.mapa(f, "CP_Manchas_Veta")
    r.escaneo(f, 0.42, 0.25)
    r.capa("Barniz", M, {"roughness": 0.18}, opac=0.9)
    f = r.capa("Barniz: velo de uso", M, {"roughness": 0.36}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 4)
    f = r.capa("Barniz saltado en cantos", M, {"baseColor": "#C9A066", "roughness": 0.6, "height": -0.008}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.24, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8})
    f = r.capa("Surcos: cresta sin barniz", M, {"baseColor": "#B98B4E", "roughness": 0.55}, opac=0.6)
    r.mapa(f, "CP_Relieve_Canto")
    r.escaneo(f, 0.5, 0.4)
    f = r.capa("Mano: madera oscurecida", M, {"baseColor": "#4A2A10", "roughness": 0.24}, opac=0.55)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Fingerprints Smeared Wide", 3, fusion="Multiply")
    r.escaneo(f, 0.45, 0.35)
    f = r.capa("Surcos: fondo con mugre", M, {"baseColor": "#24140A", "roughness": 0.7}, opac=0.85)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.6, 0.4)
    f = r.capa("Aranazos finos", M, {"baseColor": "#E3BE80", "roughness": 0.5, "height": -0.005}, opac=0.4)
    r.grunge(f, "Grunge Scratches Fine", 3)
    r.escaneo(f, 0.04, 0.85)
    f = r.capa("Golpes", M, {"baseColor": "#3A2210", "roughness": 0.5, "height": -0.03}, opac=0.65)
    r.grunge(f, "Grunge Scratches Rough", 3.5)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.22, 0.7)
    f = r.capa("Mugre en rincones", M, {"baseColor": "#22140A", "roughness": 0.7}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.7})


def resto(r):
    T = r.grupo("Testigo", clases=("Testigo",))
    r.capa("Pintura roja", T, {"baseColor": "#8E1712", "roughness": 0.4, "metallic": 0})
    f = r.capa("Pintura roja saltada", T, {"baseColor": "#3A3B3E", "roughness": 0.4}, opac=0.8)
    r.grunge(f, "Grunge Scratches Dirty", 8)
    r.escaneo(f, 0.25, 0.7)
    K = r.grupo("Marcajes", clases=("Tinta",))
    r.capa("Grabado relleno de blanco", K, {"baseColor": "#CFCDC2", "roughness": 0.55, "metallic": 0, "height": -0.015})
    f = r.capa("Blanco perdido", K, {"baseColor": "#3A3B3E", "roughness": 0.42, "metallic": 1}, opac=0.85)
    r.grunge(f, "Grunge Dirt", 9)
    r.escaneo(f, 0.3, 0.6)


def construir():
    r = Receta(SET, "subfusil VOSTREL")
    acero(r)
    madera(r)
    resto(r)
    S = r.grupo("Suciedad global")
    f = r.capa("Polvo", S, {"baseColor": "#8C7F6C", "roughness": 0.85}, opac=0.08)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
