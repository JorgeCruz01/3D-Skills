"""Look-dev del revolver .357 HARVEK ARMS en Substance 3D Painter.

    python ../_herramientas/sp.py importar Revolver_Accion_Simple Texturas/Fuente/Wood049/Wood049_2K-JPG_Color.jpg (+ Roughness, NormalGL)
    python ../_herramientas/sp.py rehacer Revolver_Accion_Simple vistas_sp.json

Aspecto: revolver de acero inoxidable satinado, de tiro, muy disparado y bien limpiado. Satinado a lo largo que se
pule a espejo en los cantos, en la boca y donde roza la funda; aros de carbonilla y tinte pardo de calor en la cara
delantera del tambor y alrededor del cono de forzamiento; la linea de arrastre del reten alrededor del tambor;
martillo y gatillo mas oscuros y pulidos por el dedo. Cachas de nogal al aceite con el picado labrado, oscuro, y
el medallon de laton.

Mascaras (Texturas/Bakes/Mascaras/): MK_ por material y por pieza (la clase `Pavonado` es aqui el ACERO INOXIDABLE:
el material del high poly conserva el nombre de la primera version); ZN_ zonas de uso (Mano, Boca, Fogueo, Apoyo);
ZN_Linea_Tambor, la linea de arrastre (`mascaras_extra.py`, del mapa de posicion); MK_Nogal_Picado, BD_ y PN_ del
panel de picado dibujado como curva (`sp_paneles.py`); CP_ ruido orientado al canon y, con `_Veta`, a la empunadura.
"""
from sp_receta import Receta

SET = "LP_Revolver"
INOX = ("Pavonado", "Tambor", "Varilla", "Acero_Claro", "Mandos")
VETA = {"mode": "Triplanar", "scale": 6.0, "rotation": 62}       # la veta, a lo largo de la empunadura


def acero(r):
    A = r.grupo("Inoxidable", clases=INOX)
    r.capa("Inox satinado", A, {"baseColor": "#A7A7A3", "roughness": 0.38, "metallic": 1})
    f = r.capa("Satinado: hilo", A, {"baseColor": "#B6B6B2", "roughness": 0.3}, opac=0.8)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.5, 0.35)
    f = r.capa("Satinado: velo mate", A, {"baseColor": "#8F8F8B", "roughness": 0.52}, opac=0.5)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.42, 0.3)
    r.capa("Tambor: algo mas pulido", A, {"roughness": 0.3}, opac=0.6, clases=("Tambor",))
    r.capa("Mandos: acero mas oscuro", A, {"baseColor": "#6F6F6E", "roughness": 0.34}, opac=0.85, clases=("Mandos",))
    r.capa("Tornilleria pulida", A, {"baseColor": "#B9B9B6", "roughness": 0.24}, opac=0.9, clases=("Acero_Claro", "Varilla"))
    # pulido de uso: cantos, boca y roce de funda
    f = r.capa("Cantos pulidos", A, {"baseColor": "#C9C9C6", "roughness": 0.16, "metallic": 1}, opac=0.85)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.34, "Wear_Contrast": 0.6, "Grunge_Amount": 0.6, "grunge_scale": 6})
    f = r.capa("Funda: roce brillante", A, {"baseColor": "#C4C4C1", "roughness": 0.2, "metallic": 1}, opac=0.75)
    r.mapa(f, "ZN_Boca")
    r.mapa(f, "ZN_Apoyo", fusion="LinearDodge")
    r.grunge(f, "Grunge Scratches Dirty", 6, fusion="Multiply")
    r.escaneo(f, 0.3, 0.5)
    f = r.capa("Mano: pulido por el dedo", A, {"baseColor": "#9A9A98", "roughness": 0.2, "metallic": 1}, opac=0.6, clases=("Mandos",))
    r.mapa(f, "ZN_Mano", fusion="Multiply")
    r.grunge(f, "Grunge Fingerprints Smeared", 7.0, fusion="Multiply")
    f = r.capa("Tambor: linea de arrastre", A, {"baseColor": "#D2D2CF", "roughness": 0.14, "metallic": 1, "height": -0.006}, opac=0.9)
    r.mapa(f, "ZN_Linea_Tambor")
    r.grunge(f, "Grunge Dirt", 9, fusion="Multiply", opac=0.5)
    f = r.capa("Aranazos largos", A, {"baseColor": "#D0D0CD", "roughness": 0.2, "height": -0.006}, opac=0.6)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.02, 0.9)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    f = r.capa("Aranazos finos al azar", A, {"baseColor": "#C2C2BF", "roughness": 0.26}, opac=0.5)
    r.grunge(f, "Grunge Scratches Fine", 5.0)
    r.escaneo(f, 0.1, 0.85)
    f = r.capa("Huellas y aceite", A, {"roughness": 0.2}, opac=0.45)
    r.grunge(f, "Grunge Fingerprints Smeared", 6)
    # fogueo: carbonilla y tinte de calor en la cara del tambor, el cono y bajo el puente
    f = r.capa("Fogueo: tinte pardo de calor", A, {"baseColor": "#6A5238", "roughness": 0.44}, opac=0.6)
    r.mapa(f, "ZN_Fogueo")
    r.grunge(f, "Clouds 2", 8, fusion="Multiply")
    r.escaneo(f, 0.5, 0.25)
    f = r.capa("Fogueo: carbonilla", A, {"baseColor": "#0E0D0C", "roughness": 0.8}, opac=0.8)
    r.mapa(f, "ZN_Fogueo")
    r.grunge(f, "Grunge Dusty Powder Soft", 9.0, fusion="Multiply")
    r.escaneo(f, 0.4, 0.3)
    f = r.capa("Boca: carbonilla", A, {"baseColor": "#0E0D0C", "roughness": 0.8}, opac=0.6)
    r.mapa(f, "ZN_Boca")
    r.grunge(f, "Grunge Dusty Powder Soft", 9.0, fusion="Multiply")
    r.escaneo(f, 0.3, 0.3)
    f = r.capa("Mugre en rincones", A, {"baseColor": "#1A1713", "roughness": 0.6}, opac=0.55)
    r.gen(f, "Dirt", {"dirt_level": 0.22, "dirt_contrast": 0.6, "grunge_amount": 0.8})


def madera(r):
    M = r.grupo("Nogal", clases=("Nogal", "Nogal_Picado"))
    tex = lambda m: {"resource": "Wood049_2K-JPG_" + m, "usage": "texture"}
    r.capa("Nogal base", M, {"baseColor": tex("Color"), "roughness": tex("Roughness"), "normal": tex("NormalGL"), "metallic": 0}, proy=VETA,
           opac={"normal": 0.1})
    r.capa("Nogal tono", M, {"baseColor": "#6E3A1E"}, opac=0.92, fusion="Multiply")
    f = r.capa("Veta oscura", M, {"baseColor": "#1E0D06"}, opac=0.45)
    r.mapa(f, "CP_Rayado_Largo_Veta")
    r.escaneo(f, 0.4, 0.25)
    f = r.capa("Aguas claras", M, {"baseColor": "#A85E28"}, opac=0.22)
    r.mapa(f, "CP_Manchas_Veta")
    r.escaneo(f, 0.42, 0.25)
    r.capa("Aceite satinado", M, {"roughness": 0.3}, opac=0.85)
    f = r.capa("Aceite: brillo de la mano", M, {"roughness": 0.18}, opac=0.6)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Fingerprints Smeared Wide", 4.0, fusion="Multiply")
    f = r.capa("Acabado gastado en cantos", M, {"baseColor": "#8A5830", "roughness": 0.5, "height": -0.008}, opac=0.5)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.2, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 8})
    f = r.capa("Mano: madera oscurecida", M, {"baseColor": "#27130A", "roughness": 0.24}, opac=0.4)
    r.mapa(f, "ZN_Mano")
    r.grunge(f, "Grunge Dirt", 4.0, fusion="Multiply")
    r.escaneo(f, 0.42, 0.35)
    f = r.capa("Aranazos finos", M, {"baseColor": "#B08357", "roughness": 0.5, "height": -0.005}, opac=0.4)
    r.grunge(f, "Grunge Scratches Fine", 3.5)
    r.escaneo(f, 0.04, 0.85)
    f = r.capa("Golpes", M, {"baseColor": "#24120A", "roughness": 0.5, "height": -0.03}, opac=0.6)
    r.grunge(f, "Grunge Scratches Rough", 4.0)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.escaneo(f, 0.2, 0.7)
    f = r.capa("Golpes de apoyo: madera cruda", M, {"baseColor": "#B58A5C", "roughness": 0.7, "height": -0.03}, opac=0.8)
    r.mapa(f, "ZN_Apoyo")
    r.grunge(f, "Grunge Scratches Rough", 5.0, fusion="Multiply")
    r.escaneo(f, 0.2, 0.75)
    # picado labrado: misma madera, mas oscura y mate, con el fondo sucio, la cresta pulida y su filete
    r.capa("Picado: madera sin aceite", M, {"baseColor": "#4A2010", "roughness": 0.48}, opac=0.6, clases=("Nogal_Picado",))
    f = r.capa("Picado: fondo sucio", M, {"baseColor": "#120805", "roughness": 0.75}, opac=0.85, clases=("Nogal_Picado",))
    r.mapa(f, "CP_Relieve_Hueco", fusion="Multiply")
    r.escaneo(f, 0.7, 0.4)
    f = r.capa("Picado: cresta pulida", M, {"baseColor": "#40200F", "roughness": 0.26}, opac=0.5, clases=("Nogal_Picado",))
    r.mapa(f, "CP_Relieve_Canto", fusion="Multiply")
    r.escaneo(f, 0.55, 0.4)
    f = r.capa("Picado: filete del borde", M, {"baseColor": "#1E0E07", "roughness": 0.55, "height": -0.03}, opac=0.7)
    r.mapa(f, "BD_Nogal_Picado")
    f = r.capa("Mugre en rincones", M, {"baseColor": "#170C06", "roughness": 0.7}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.4, "dirt_contrast": 0.5, "grunge_amount": 0.7})
    f = r.capa("Madera oscurecida junto al acero", M, {"baseColor": "#140A05", "roughness": 0.4}, opac=0.5)
    r.mapa(f, "HL_Laton")
    r.mapa(f, "HL_Acero_Claro", fusion="LinearDodge")


def resto(r):
    L = r.grupo("Laton", clases=("Laton",))
    r.capa("Laton", L, {"baseColor": "#C49E5A", "roughness": 0.26, "metallic": 1})
    f = r.capa("Laton: patina", L, {"baseColor": "#6A5230", "roughness": 0.6}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 12)
    f = r.capa("Laton: mugre en el relieve", L, {"baseColor": "#2A1F10", "roughness": 0.7}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.45, "dirt_contrast": 0.5, "grunge_amount": 0.7})
    P = r.grupo("Plomo", clases=("Plomo",))
    r.capa("Plomo", P, {"baseColor": "#5E5E60", "roughness": 0.5, "metallic": 1})
    f = r.capa("Plomo: oxido blanquecino", P, {"baseColor": "#8E8E8C", "roughness": 0.7}, opac=0.5)
    r.grunge(f, "Clouds 2", 14)
    N = r.grupo("Miras", clases=("Negro_Mate",))
    r.capa("Negro mate", N, {"baseColor": "#141416", "roughness": 0.5, "metallic": 1})
    f = r.capa("Negro: canto pelado", N, {"baseColor": "#A8A8A5", "roughness": 0.3, "metallic": 1}, opac=0.7)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.22, "Wear_Contrast": 0.8, "Grunge_Amount": 0.7, "grunge_scale": 8})
    R = r.grupo("Inserto rojo", clases=("Rojo_Mira",))
    r.capa("Plastico rojo", R, {"baseColor": "#B01A12", "roughness": 0.4, "metallic": 0})
    T = r.grupo("Marcajes", clases=("Tinta",))
    r.capa("Grabado", T, {"baseColor": "#3A3A39", "roughness": 0.5, "metallic": 1, "height": -0.02})


def construir():
    r = Receta(SET, "revolver HARVEK")
    acero(r)
    madera(r)
    resto(r)
    S = r.grupo("Suciedad global")
    f = r.capa("Polvo", S, {"baseColor": "#8C7F6C", "roughness": 0.85}, opac=0.06)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
