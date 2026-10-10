"""Look-dev del fusil de cerrojo TARNVOLD en Substance 3D Painter.

    python ../_herramientas/sp.py importar Fusil_Cerrojo Texturas/Fuente/Wood049/Wood049_2K-JPG_Color.jpg (+ Roughness, NormalGL)
    python ../_herramientas/sp.py rehacer Fusil_Cerrojo vistas_sp.json

Aspecto: fusil de caza cuidado, con temporadas de monte. Nogal barnizado, brillante, con el barniz rozado en los cantos
y mate donde apoya la mejilla; picado oscuro y pulido por la mano. Pavonado profundo que blanquea en la boca, en la
palanca del cerrojo y en los cantos del cajon. Visor de aluminio anodizado negro mate con el canto pelado a metal.

MK_Nogal_Picado, BD_ y PN_ salen de los paneles dibujados como curvas (`sp_paneles.py`), no de caras del high poly.
Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y por pieza; ZN_ zonas de uso (Mano, Mejilla, Boca, Accion,
Apoyo: `substance.zonas`); CP_ ruido orientado al canon a dos escalas; CP_Relieve_* crestas y fondos del picado y de la
cantonera, sacados de la normal de Blender (`substance.normal_hp(..., sin_grano=...)` + `sp.py normal`).
"""
from sp_receta import Receta

SET = "LP_Fusil"
PAVONADO = ("Cajon", "Canon", "Palanca", "Herrajes")
VETA = {"mode": "Triplanar", "scale": 3.0}       # la veta del escaneo corre a lo largo del eje X del arma


def acero(r):
    A = r.grupo("Acero", clases=PAVONADO + ("Acero_Pulido",))
    r.capa("Acero base", A, {"baseColor": "#B8B9BC", "roughness": 0.30, "metallic": 1})
    f = r.capa("Acero rectificado", A, {"baseColor": "#A3A4A8", "roughness": 0.46})
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.5, 0.5)

    P = r.grupo("Pavonado", dentro=A, clases=PAVONADO)
    r.gen(P, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.3, "Wear_Contrast": 0.75, "Grunge_Amount": 0.5, "grunge_scale": 3}, fusion="Multiply")
    r.capa("Pavon", P, {"baseColor": "#101217", "roughness": 0.3, "metallic": 1})
    f = r.capa("Pavon gastado a gris", P, {"baseColor": "#34343A", "roughness": 0.42}, opac=0.5)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.34, 0.3)
    r.grunge(f, "Grunge Dirt Scratched", 3, fusion="Multiply")
    f = r.capa("Pavon velo pardo", P, {"baseColor": "#2A211D", "roughness": 0.46}, opac=0.3)
    r.grunge(f, "Clouds 2", 2.5)
    f = r.capa("Aceite y huellas", P, {"roughness": 0.16}, opac=0.55)
    r.grunge(f, "Grunge Fingerprints Smeared", 2.5)
    f = r.capa("Mate de polvo", P, {"roughness": 0.55}, opac=0.35)
    r.grunge(f, "Grunge Dirt", 4)

    f = r.capa("Aranazos largos", A, {"baseColor": "#9A9BA0", "roughness": 0.34, "metallic": 1, "height": -0.008}, opac=0.7)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.018, 0.9)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    # lo que solo pasa en un sitio
    f = r.capa("Accion: palanca y ventana blanqueadas", A, {"baseColor": "#B4B5B8", "roughness": 0.26, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.6, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 8})
    r.mapa(f, "ZN_Accion", fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Accion: pomo pulido por la mano", A, {"baseColor": "#55565B", "roughness": 0.2, "metallic": 1}, opac=0.8, clases=("Palanca",))
    r.mapa(f, "ZN_Accion", fusion="Multiply")
    r.grunge(f, "Grunge Fingerprints Smeared", 4.0, fusion="Multiply")
    f = r.capa("Boca: corona blanqueada", A, {"baseColor": "#B4B5B8", "roughness": 0.3, "metallic": 1}, opac=0.95)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.6, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 10})
    r.mapa(f, "ZN_Boca", fusion="Multiply")
    r.escaneo(f, 0.18, 0.5)
    f = r.capa("Boca: hollin", A, {"baseColor": "#0B0B0B", "roughness": 0.85}, opac=0.6)
    r.mapa(f, "ZN_Boca")
    r.grunge(f, "Grunge Dusty Powder Soft", 3.0, fusion="Multiply")
    r.escaneo(f, 0.36, 0.3)
    f = r.capa("Apoyo: pavon comido", A, {"baseColor": "#8E8F93", "roughness": 0.38, "metallic": 1}, opac=0.8)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Dirty", 2.5, fusion="Multiply")
    r.escaneo(f, 0.24, 0.6)
    f = r.capa("Aranazos finos al azar", A, {"baseColor": "#6E6F74", "roughness": 0.5}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 2.2)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Picaduras de oxido", A, {"baseColor": "#4A2A16", "roughness": 0.9, "height": 0.004}, opac=0.4)
    r.grunge(f, "Grunge Rust Fine", 3.5)
    r.escaneo(f, 0.1, 0.8)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.capa("Cerrojo pulido", A, {"baseColor": "#9A9B9E", "roughness": 0.22, "metallic": 1}, clases=("Acero_Pulido",))
    f = r.capa("Cerrojo: rayas de correr", A, {"roughness": 0.38, "baseColor": "#B4B5B8"}, clases=("Acero_Pulido",))
    r.mapa(f, "CP_Rayado_Largo", fusion="Multiply")
    f = r.capa("Cerrojo: grasa", A, {"baseColor": "#2A2118", "roughness": 0.3}, opac=0.45, clases=("Acero_Pulido",))
    r.grunge(f, "Grunge Dirt", 3.0, fusion="Multiply")
    f = r.capa("Oxido en rincones", A, {"baseColor": "#3D2516", "roughness": 0.85}, opac=0.4)
    r.gen(f, "Dirt", {"dirt_level": 0.1, "dirt_contrast": 0.8, "grunge_amount": 0.95})
    f = r.capa("Polvo en huecos", A, {"baseColor": "#7C7468", "roughness": 0.9}, opac=0.35)
    r.gen(f, "Dirt", {"dirt_level": 0.26, "dirt_contrast": 0.5, "grunge_amount": 0.6})


def madera(r):
    M = r.grupo("Nogal", clases=("Nogal", "Nogal_Picado"))
    tex = lambda m: {"resource": "Wood049_2K-JPG_" + m, "usage": "texture"}
    r.capa("Nogal base", M, {"baseColor": tex("Color"), "roughness": tex("Roughness"), "normal": tex("NormalGL"), "metallic": 0}, proy=VETA,
           opac={"normal": 0.1})
    r.capa("Nogal tono rojizo", M, {"baseColor": "#7C3C1E"}, opac=0.92, fusion="Multiply")
    f = r.capa("Veta ancha oscura", M, {"baseColor": "#1E0D06"}, opac=0.5)
    r.mapa(f, "CP_Rayado_Largo_Veta")
    r.escaneo(f, 0.4, 0.25)
    f = r.capa("Aguas claras", M, {"baseColor": "#A85E28"}, opac=0.22)
    r.mapa(f, "CP_Manchas_Veta")
    r.escaneo(f, 0.42, 0.25)
    f = r.capa("Figura oscura", M, {"baseColor": "#2E1508"}, opac=0.32)
    r.mapa(f, "CP_Manchas_Veta")
    r.invertir(f)
    r.escaneo(f, 0.35, 0.3)
    # barniz brillante: la madera de un fusil de caza no es mate
    r.capa("Barniz", M, {"roughness": 0.16}, opac=0.9)
    f = r.capa("Barniz: velo de uso", M, {"roughness": 0.34}, opac=0.6)
    r.grunge(f, "Grunge Dirt", 1.6)
    f = r.capa("Barniz: huellas", M, {"roughness": 0.28}, opac=0.5)
    r.grunge(f, "Grunge Fingerprints Smeared Wide", 2.0)
    f = r.capa("Barniz rozado en cantos", M, {"baseColor": "#8A5830", "roughness": 0.5, "height": -0.008}, opac=0.45)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.16, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 6})
    f = r.capa("Mano: madera oscurecida", M, {"baseColor": "#27130A", "roughness": 0.22}, opac=0.45)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Fingerprints Smeared Wide", 1.5, fusion="Multiply")
    r.escaneo(f, 0.42, 0.35)
    f = r.capa("Mejilla: barniz mate", M, {"roughness": 0.4}, opac=0.3)
    r.mapa(f, "ZN_Mejilla")
    r.grunge(f, "Grunge Dirt", 1.3, fusion="Multiply")
    r.escaneo(f, 0.3, 0.35)
    f = r.capa("Aranazos finos", M, {"baseColor": "#B08357", "roughness": 0.5, "height": -0.005}, opac=0.4)
    r.grunge(f, "Grunge Scratches Fine", 1.4)
    r.escaneo(f, 0.04, 0.85)
    f = r.capa("Golpes", M, {"baseColor": "#24120A", "roughness": 0.5, "height": -0.03}, opac=0.6)
    r.grunge(f, "Grunge Scratches Rough", 1.6)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.2, 0.7)
    f = r.capa("Golpes de apoyo: madera cruda", M, {"baseColor": "#B58A5C", "roughness": 0.7, "height": -0.035}, opac=0.8)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Rough", 2.2, fusion="Multiply")
    r.escaneo(f, 0.2, 0.75)
    # picado: sin barniz, mas oscuro, con el fondo sucio y las crestas pulidas por la mano
    r.capa("Picado: madera sin barniz", M, {"baseColor": "#4A2010", "roughness": 0.48}, opac=0.6, clases=("Nogal_Picado",))
    f = r.capa("Picado: fondo sucio", M, {"baseColor": "#120805", "roughness": 0.75}, opac=0.85, clases=("Nogal_Picado",))
    r.mapa(f, "CP_Relieve_Hueco", fusion="Multiply")
    r.escaneo(f, 0.7, 0.4)
    f = r.capa("Picado: cresta pulida", M, {"baseColor": "#40200F", "roughness": 0.28}, opac=0.5, clases=("Nogal_Picado",))
    r.mapa(f, "CP_Relieve_Canto", fusion="Multiply")
    r.escaneo(f, 0.55, 0.4)
    f = r.capa("Picado: filete del borde", M, {"baseColor": "#1E0E07", "roughness": 0.55, "height": -0.03}, opac=0.7)
    r.mapa(f, "BD_Nogal_Picado")
    f = r.capa("Mugre en rincones", M, {"baseColor": "#170C06", "roughness": 0.7}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.42, "dirt_contrast": 0.5, "grunge_amount": 0.7})


def visor(r):
    V = r.grupo("Visor", clases=("Visor", "Anillas_Visor", "Plastico"))
    r.capa("Anodizado negro mate", V, {"baseColor": "#141416", "roughness": 0.44, "metallic": 1}, clases=("Visor", "Anillas_Visor"))
    r.capa("Plastico negro", V, {"baseColor": "#0F0F11", "roughness": 0.5, "metallic": 0}, clases=("Plastico",))
    f = r.capa("Anodizado: brillo de roce", V, {"baseColor": "#1B1B1E", "roughness": 0.3}, opac=0.6)
    r.grunge(f, "Grunge Fingerprints Smeared", 3.0)
    f = r.capa("Anodizado: canto pelado a aluminio", V, {"baseColor": "#C4C5C8", "roughness": 0.36, "metallic": 1}, opac=0.7, clases=("Visor", "Anillas_Visor"))
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.1, "Wear_Contrast": 0.8, "Grunge_Amount": 0.75, "grunge_scale": 8}, fusion="Multiply")
    f = r.capa("Anodizado: golpes de apoyo", V, {"baseColor": "#B9BABD", "roughness": 0.4, "metallic": 1}, opac=0.85, clases=("Visor", "Anillas_Visor"))
    r.mapa(f, "ZN_Apoyo", fusion="Multiply")
    r.grunge(f, "Grunge Scratches Dirty", 3.0, fusion="Multiply")
    r.escaneo(f, 0.2, 0.7)
    f = r.capa("Aranazos finos", V, {"baseColor": "#3A3A3E", "roughness": 0.52}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 2.6)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Polvo en huecos", V, {"baseColor": "#7C7468", "roughness": 0.9}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.34, "dirt_contrast": 0.5, "grunge_amount": 0.7})
    L = r.grupo("Lente", clases=("Lente",))
    r.capa("Vidrio tratado", L, {"baseColor": "#0A1622", "roughness": 0.05, "metallic": 0})
    f = r.capa("Tratamiento: reflejo violeta", L, {"baseColor": "#2A1838"}, opac=0.6)
    r.grunge(f, "Clouds 2", 1.5)
    f = r.capa("Lente: polvo y huellas", L, {"baseColor": "#5E5A54", "roughness": 0.5}, opac=0.3)
    r.grunge(f, "Grunge Fingerprints Smeared", 3.0)


def resto(r):
    G = r.grupo("Cantonera", clases=("Cantonera",))
    r.capa("Goma rojiza", G, {"baseColor": "#5E2B17", "roughness": 0.64, "metallic": 0})
    f = r.capa("Goma rozada", G, {"baseColor": "#7A4A34", "roughness": 0.55}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.4, "Wear_Contrast": 0.5, "Grunge_Amount": 0.8, "grunge_scale": 7})
    f = r.capa("Goma: polvo en el grano", G, {"baseColor": "#8A7C6A", "roughness": 0.92}, opac=0.6)
    r.mapa(f, "CP_Relieve_Hueco")
    r.escaneo(f, 0.6, 0.4)
    f = r.capa("Goma: tierra del suelo", G, {"baseColor": "#4A3A2A", "roughness": 0.9}, opac=0.6)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Dirt", 3.0, fusion="Multiply")
    S = r.grupo("Separador", clases=("Separador",))
    r.capa("Separador negro", S, {"baseColor": "#0C0C0C", "roughness": 0.4, "metallic": 0})
    T = r.grupo("Marcajes", clases=("Tinta",))
    r.capa("Grabado", T, {"baseColor": "#9C9DA2", "roughness": 0.4, "height": -0.02})


def construir():
    r = Receta(SET, "fusil TARNVOLD")
    acero(r)
    madera(r)
    visor(r)
    resto(r)
    S = r.grupo("Suciedad global")
    f = r.capa("Polvo", S, {"baseColor": "#8C7F6C", "roughness": 0.85}, opac=0.07)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
