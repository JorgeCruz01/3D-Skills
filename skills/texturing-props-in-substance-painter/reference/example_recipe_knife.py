"""Look-dev del cuchillo SKARVOLD en Substance 3D Painter.

    python ../_herramientas/sp.py rehacer Cuchillo_Combate [vistas.json]

Aspecto: cuchillo de dotacion usado, no maltratado. El fosfatado se ha ido en las aristas y a
lo largo de la hoja, donde roza la funda; el cuero esta oscurecido por la grasa y rozado en lo
que sobresale; el puno, pulido por la mano.

Mascaras (Texturas/Bakes/Mascaras/, de `substance.py` + `sp_mascaras.py`):
  MK_<clase>   clases de material del high poly        HL_<clase>  cerco alrededor de una clase
  CP_Rayado_Largo / CP_Rayado_Ancho / CP_Manchas       ruido en espacio de objeto, orientado al eje del cuchillo
  CP_Junta / CP_Lamina                                 juntas y tono por arandela del puno
"""
from sp_receta import Receta, tri

SET = "LP_Cuchillo"
CUERO = ("Cuero_Funda", "Cuero_Estampa", "Cuero_Canto", "Cuero_Correa", "Letras")


def acero(r):
    A = r.grupo("Acero", clases=("Recubrimiento", "Acero_Filo", "Tinta"))
    r.capa("Acero base", A, {"baseColor": "#B5B6B9", "roughness": 0.32, "metallic": 1})
    f = r.capa("Acero rectificado", A, {"baseColor": "#A1A2A6", "roughness": 0.50})
    r.mapa(f, "CP_Rayado_Ancho")
    r.escaneo(f, 0.5, 0.55)
    f = r.capa("Acero patina", A, {"baseColor": "#6E6A66", "roughness": 0.58}, opac=0.5)
    r.grunge(f, "Grunge Dirt", 3)

    R = r.grupo("Recubrimiento fosfatado", dentro=A, clases=("Recubrimiento", "Tinta"))
    r.gen(R, "Metal Edge Wear", {"invert": 1, "Wear_Level": 0.42, "Wear_Contrast": 0.7, "Grunge_Amount": 0.8,
                                 "grunge_scale": 10}, fusion="Multiply")
    r.capa("Fosfato", R, {"baseColor": "#1F2023", "roughness": 0.54, "metallic": 0, "height": 0.015})
    f = r.capa("Fosfato polvo mate", R, {"baseColor": "#34353A", "roughness": 0.72}, opac=0.3)
    r.grunge(f, "Grunge Dirt Scratched", 3.5)
    f = r.capa("Fosfato brunido", R, {"baseColor": "#303134", "roughness": 0.40})
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.40, 0.35)
    r.grunge(f, "Grunge Scratches Rough", 2.5, fusion="Multiply")
    f = r.capa("Huellas y aceite", R, {"roughness": 0.30}, opac=0.55)
    r.grunge(f, "Grunge Fingerprints Smeared", 2.5)
    r.capa("Marcaje grabado", R, {"baseColor": "#9A9C9F", "roughness": 0.42, "height": -0.02}, clases=("Tinta",))

    # la funda raya la hoja a lo largo: el acero asoma en hilos finos, no en manchas
    f = r.capa("Aranazos de la funda", A, {"baseColor": "#A9AAAD", "roughness": 0.36, "metallic": 1, "height": -0.01},
               opac=0.85)
    r.mapa(f, "CP_Rayado_Largo")
    r.escaneo(f, 0.09, 0.9)
    r.grunge(f, "Grunge Dirt", 2.0, fusion="Multiply")
    r.mapa(f, "MK_Recubrimiento", fusion="Multiply")

    r.capa("Filo asentado", A, {"baseColor": "#CDCED0", "roughness": 0.22, "metallic": 1}, clases=("Acero_Filo",))
    f = r.capa("Filo rayas de piedra", A, {"roughness": 0.42}, clases=("Acero_Filo",))
    r.mapa(f, "CP_Rayado_Ancho", fusion="Multiply")
    f = r.capa("Oxido en rincones", A, {"baseColor": "#4A2C1B", "roughness": 0.85, "metallic": 0}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.12, "dirt_contrast": 0.8, "grunge_amount": 0.95})
    f = r.capa("Polvo en el vaceo", A, {"baseColor": "#857C6E", "roughness": 0.9, "metallic": 0}, opac=0.5)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.5, "grunge_amount": 0.6})


def funda(r):
    C = r.grupo("Cuero funda", clases=CUERO)
    r.capa("Cuero base", C, {"baseColor": "#84491F", "roughness": 0.48, "metallic": 0})
    r.capa("Cuero grano", C, {"height": "Grunge Leather"}, opac={"height": 0.06}, proy=tri(10))
    f = r.capa("Cuero tono oscuro", C, {"baseColor": "#45230F", "roughness": 0.44}, opac=0.6)
    r.grunge(f, "Grunge Leather Damaged", 2.5)
    f = r.capa("Cuero tono rojizo", C, {"baseColor": "#A85E22"}, opac=0.55)
    r.grunge(f, "Clouds 2", 2.0)
    f = r.capa("Cuero engrasado", C, {"baseColor": "#55290F", "roughness": 0.26}, opac=0.7)
    r.grunge(f, "Grunge Dirt", 1.8)
    f = r.capa("Manchas de agua", C, {"baseColor": "#2C190F", "roughness": 0.62}, opac=0.5)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.40, 0.3)
    r.capa("Estampado hundido", C, {"baseColor": "#33190F", "roughness": 0.44}, opac=0.85, clases=("Cuero_Estampa",))
    r.capa("Canto brunido", C, {"baseColor": "#3B2215", "roughness": 0.40}, opac=0.85, clases=("Cuero_Canto",))
    r.capa("Correa mas oscura", C, {"baseColor": "#4C2C1A", "roughness": 0.50}, opac=0.6, clases=("Cuero_Correa",))
    f = r.capa("Cuero junto a la costura", C, {"baseColor": "#2A170D", "roughness": 0.52}, opac=0.6)
    r.mapa(f, "HL_Hilo")
    f = r.capa("Roce en aristas", C, {"baseColor": "#A9825C", "roughness": 0.74, "height": -0.015})
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.30, "Wear_Contrast": 0.7, "Grunge_Amount": 0.9, "grunge_scale": 6})
    f = r.capa("Aranazos", C, {"baseColor": "#A8743F", "roughness": 0.66, "height": -0.02}, opac=0.5)
    r.grunge(f, "Grunge Scratches Rough", 2.2)
    r.mapa(f, "CP_Manchas", fusion="Multiply")
    r.capa("Letras rozadas", C, {"baseColor": "#B58C63", "roughness": 0.62}, opac=0.8, clases=("Letras",))
    f = r.capa("Mugre en cavidades", C, {"baseColor": "#1F1008", "roughness": 0.70}, opac=0.7)
    r.gen(f, "Dirt", {"dirt_level": 0.45, "dirt_contrast": 0.5, "grunge_amount": 0.8})
    f = r.capa("Verdin junto al laton", C, {"baseColor": "#4F6B57", "roughness": 0.82}, opac=0.45)
    r.mapa(f, "HL_Laton")
    r.grunge(f, "Grunge Dirt", 6, fusion="Multiply")
    f = r.capa("Cerco del broche", C, {"baseColor": "#22140C", "roughness": 0.45}, opac=0.7)
    r.mapa(f, "HL_Broche")


def puno(r):
    P = r.grupo("Puno", clases=("Cuero_Puno", "Ranura"))
    r.capa("Puno base", P, {"baseColor": "#6A3C1B", "roughness": 0.44, "metallic": 0})
    f = r.capa("Arandelas claras", P, {"baseColor": "#8E5526"}, opac=0.5)
    r.mapa(f, "CP_Lamina")
    f = r.capa("Arandelas oscuras", P, {"baseColor": "#3A1F0E"}, opac=0.6)
    r.mapa(f, "CP_Lamina")
    r.invertir(f)
    r.escaneo(f, 0.35, 0.5)
    r.capa("Fibra del canto", P, {"height": {"resource": "CP_Rayado_Ancho", "usage": "texture"}}, opac={"height": 0.005},
           proy={"mode": "UV"})
    f = r.capa("Juntas", P, {"baseColor": "#1E1109", "roughness": 0.75, "height": -0.03}, opac=0.6)
    r.mapa(f, "CP_Junta")
    f = r.capa("Puno pulido por la mano", P, {"baseColor": "#7A4A22", "roughness": 0.24}, opac=0.9)
    r.gen(f, "Metal Edge Wear", {"Wear_Level": 0.62, "Wear_Contrast": 0.3, "Grunge_Amount": 0.6, "grunge_scale": 5})
    f = r.capa("Puno sudor", P, {"baseColor": "#2A1A10", "roughness": 0.38}, opac=0.5)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.40, 0.3)
    r.capa("Ranuras", P, {"baseColor": "#140D09", "roughness": 0.82}, clases=("Ranura",))
    f = r.capa("Puno mugre", P, {"baseColor": "#160C06", "roughness": 0.8}, opac=0.6)
    r.gen(f, "Dirt", {"dirt_level": 0.5, "dirt_contrast": 0.5, "grunge_amount": 0.8})


def herrajes(r):
    H = r.grupo("Herrajes", clases=("Laton", "Broche"))
    r.capa("Laton", H, {"baseColor": "#BE9A5F", "roughness": 0.36, "metallic": 1})
    r.capa("Broche niquelado", H, {"baseColor": "#9A9B9D", "roughness": 0.30, "metallic": 1}, clases=("Broche",))
    f = r.capa("Herrajes rayado", H, {"roughness": 0.55}, opac=0.8)
    r.grunge(f, "Grunge Scratches Fine", 8)
    f = r.capa("Patina", H, {"baseColor": "#4A3A26", "roughness": 0.78, "metallic": 0}, opac=0.85)
    r.gen(f, "Dirt", {"dirt_level": 0.6, "dirt_contrast": 0.45, "grunge_amount": 0.85})
    T = r.grupo("Hilo", clases=("Hilo",))
    r.capa("Hilo encerado", T, {"baseColor": "#B3A587", "roughness": 0.74, "metallic": 0})
    f = r.capa("Hilo sucio", T, {"baseColor": "#5A4832"}, opac=0.7)
    r.grunge(f, "Grunge Dirt", 5)


def construir():
    r = Receta(SET, "cuchillo SKARVOLD")
    acero(r)
    funda(r)
    puno(r)
    herrajes(r)
    G = r.grupo("Suciedad global")
    f = r.capa("Polvo", G, {"baseColor": "#8C7F6C", "roughness": 0.85}, opac=0.10)
    r.gen(f, "Dirt", {"dirt_level": 0.3, "dirt_contrast": 0.6, "grunge_amount": 0.95})
    return r
