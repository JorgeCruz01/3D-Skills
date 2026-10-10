"""Look-dev de la guitarra BRISANDRO en Substance 3D Painter. Dos sets: el cuerpo, y el mastil con los herrajes.

    python ../_herramientas/sp.py importar Guitarra_Electrica Texturas/Fuente/Wood049/Wood049_2K-JPG_Color.jpg (+ Roughness, NormalGL)
    python ../_herramientas/sp.py rehacer Guitarra_Electrica

Aspecto: guitarra NUEVA, recien salida de fabrica (Jorge, 2026-10-10: la primera pasada la hacia usada, con la laca
gastada y el golpeador aranado, y no era lo pedido). Fresno con laca amarillo mantequilla de alto brillo y la veta
del fresno (escaneo CC0) a traves; arce con laca ambar; golpeador de baquelita negra, liso; cromo limpio; selletas
de laton nuevo. Sin desgaste, sin mugre, sin polvo. Lo unico que rompe la perfeccion es lo que tiene un objeto
nuevo de verdad: una variacion minima de brillo en la laca y en el cromo.

Mascaras (Texturas/Bakes/Mascaras/), horneadas contra una copia de la low poly con solo las caras de cada set:
- set del mastil: MK_ por material y pieza (MK_Cuerda sale de la propia low poly: `mascara_cuerdas.py`), CP_*.
- set del cuerpo: MK_C_*, CP_*_C.
"""
from sp_receta import Receta

VETA = {"mode": "Triplanar", "scale": 4.0, "rotation": 0}         # la veta, a lo largo de la guitarra
VETA_ARCE = {"mode": "Triplanar", "scale": 7.0, "rotation": 0}
tex = lambda m: {"resource": "Wood049_2K-JPG_" + m, "usage": "texture"}


def cromo(r, G):
    r.capa("Cromo", G, {"baseColor": "#DEDFE1", "roughness": 0.07, "metallic": 1})
    f = r.capa("Cromo: variacion minima de brillo", G, {"roughness": 0.13}, opac=0.4)
    r.grunge(f, "Clouds 2", 5)


def cuerpo():
    r = Receta("LP_Cuerpo", "cuerpo de fresno")
    W = r.grupo("Fresno lacado", clases=("C_Madera", "C_Otro"))
    r.capa("Laca mantequilla", W, {"baseColor": "#DFA038", "roughness": 0.1, "metallic": 0})
    r.capa("Fresno: escaneo", W, {"baseColor": tex("Color"), "normal": tex("NormalGL")}, proy=VETA, fusion={"baseColor": "Multiply"},
           opac={"baseColor": 0.6, "normal": 0.1})
    f = r.capa("Veta oscura", W, {"baseColor": "#7E4A10"}, opac=0.6)
    r.mapa(f, "CP_Rayado_Largo_C")
    r.escaneo(f, 0.42, 0.4)
    f = r.capa("Aguas claras", W, {"baseColor": "#EDBE5E"}, opac=0.1)
    r.mapa(f, "CP_Manchas_C")
    r.escaneo(f, 0.42, 0.25)
    f = r.capa("Laca: variacion minima de brillo", W, {"roughness": 0.15}, opac=0.4)
    r.grunge(f, "Clouds 2", 3)
    C = r.grupo("Herrajes del cuerpo", clases=("C_Cromo", "C_Tornillo"))
    cromo(r, C)
    return r


def mastil():
    r = Receta("LP_Mastil", "mastil y herrajes")
    A = r.grupo("Arce lacado", clases=("Arce", "Pala", "Cuerpo", "Tinta_Negra"))
    r.capa("Laca ambar", A, {"baseColor": "#DFA850", "roughness": 0.16, "metallic": 0})
    r.capa("Arce: escaneo", A, {"baseColor": tex("Color"), "normal": tex("NormalGL")}, proy=VETA_ARCE, fusion={"baseColor": "Multiply"},
           opac={"baseColor": 0.45, "normal": 0.05})
    f = r.capa("Arce: aguas", A, {"baseColor": "#EABF78"}, opac=0.12)
    r.mapa(f, "CP_Manchas")
    r.escaneo(f, 0.42, 0.25)
    r.capa("Rotulo y puntos bajo la laca", A, {"baseColor": "#0E0D0C"}, opac=0.97, clases=("Tinta_Negra",))
    f = r.capa("Laca: variacion minima de brillo", A, {"roughness": 0.2}, opac=0.4)
    r.grunge(f, "Clouds 2", 4)

    G = r.grupo("Golpeador", clases=("Golpeador",))
    r.capa("Baquelita negra", G, {"baseColor": "#0A0A0B", "roughness": 0.16, "metallic": 0})
    f = r.capa("Baquelita: variacion minima de brillo", G, {"roughness": 0.21}, opac=0.4)
    r.grunge(f, "Clouds 2", 4)

    C = r.grupo("Cromo", clases=("Cromo", "Clavija", "Tapa_Pastilla", "Tornillo", "Moleteado"))
    cromo(r, C)
    T = r.grupo("Trastes", clases=("Traste",))
    r.capa("Alpaca pulida", T, {"baseColor": "#D2CEC2", "roughness": 0.12, "metallic": 1})
    L = r.grupo("Laton", clases=("Laton",))
    r.capa("Laton nuevo", L, {"baseColor": "#C9A44C", "roughness": 0.2, "metallic": 1})
    f = r.capa("Laton: variacion minima de brillo", L, {"roughness": 0.28}, opac=0.4)
    r.grunge(f, "Clouds 2", 8)
    K = r.grupo("Cuerdas", clases=("Cuerda",))
    r.capa("Acero niquelado", K, {"baseColor": "#C4C3BE", "roughness": 0.22, "metallic": 1})
    H = r.grupo("Hueso", clases=("Hueso",))
    r.capa("Hueso", H, {"baseColor": "#E2D9BF", "roughness": 0.4, "metallic": 0})
    N = r.grupo("Plastico negro", clases=("Negro",))
    r.capa("Plastico negro", N, {"baseColor": "#0E0E0F", "roughness": 0.36, "metallic": 0})
    P = r.grupo("Polos", clases=("Polo",))
    r.capa("Acero del iman", P, {"baseColor": "#9A9996", "roughness": 0.3, "metallic": 1})
    return r


def construir():
    return [cuerpo(), mastil()]
