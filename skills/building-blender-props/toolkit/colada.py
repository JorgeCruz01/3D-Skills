"""Piezas coladas o inyectadas: una piel continua con radios, mecanizada o
desmoldeada despues. Generaliza lo que se puso a punto en la valvula.

Orden fijo: colada en grueso -> cortes -> remallado fino. El remallado final va
despues del corte a proposito: cortar la piel ya terminada deja astillas en todo
el contorno (medido en la valvula: 151 caras sobre 100:1 y 4 aristas abiertas).
Asi la malla queda uniforme y estanca, y los cantos cortados salen con ~0.5 mm de
radio, como una pieza desbarbada o un canto de molde.
"""
import bmesh
import bpy
from mathutils.bvhtree import BVHTree

import formas as F

_HUELLAS = {}      # nombre de pieza -> {nombre de cortador: BVH}


def colar(nombre, solidos, cortes=(), textos=(), voxel=0.6e-3, fino=0.45e-3, suavizado=8, suavizado_fino=2,
          solver="MANIFOLD", exactos=()):
    """Devuelve el objeto `nombre`. Guarda la huella de cada cortador para poder
    asignar despues materiales a las caras que toco (`pintar`)."""
    ob = F.fundir(nombre, list(solidos), voxel, suavizado=suavizado)
    huellas = {}
    for c in cortes:
        base = c.name.split(".")[0]
        bm = bmesh.new()
        bm.from_mesh(c.data)
        if base in huellas:
            # varios cortadores con el mismo nombre: se acumulan en una sola huella
            huellas[base][1].from_mesh(c.data)
            bm.free()
        else:
            huellas[base] = [None, bm]
    for base, par in huellas.items():
        par[0] = BVHTree.FromBMesh(par[1])
        par[1].free()
    _HUELLAS[nombre] = {k: v[0] for k, v in huellas.items()}
    if exactos:
        # volumenes mecanizados de la misma pieza (guias, mesas, colas de milano): se unen DESPUES de
        # suavizar la fundicion, para que los acuerdos generosos de esta no los derritan
        F.mecanizar(ob, list(exactos), solver=solver, operacion="UNION")
    if cortes:
        F.mecanizar(ob, list(cortes), solver=solver)
    ob = F.fundir(nombre, [ob] + list(textos), fino, suavizado=suavizado_fino)
    return F.sombrear(ob, 40)


def pintar(objeto, reglas, dist=None, fino=0.45e-3):
    """Asigna indice de material por cercania a los cortadores.
    `reglas` = [(indice, (nombres de cortador...)), ...], en orden de prioridad.
    Las caras que no tocan ninguno quedan en el indice 0."""
    ob = bpy.data.objects[objeto] if isinstance(objeto, str) else objeto
    huellas = _HUELLAS.get(ob.name, {})
    d = dist or fino * 1.5
    cuenta = {}
    for p in ob.data.polygons:
        p.material_index = 0
        for indice, nombres in reglas:
            if any(n in huellas and huellas[n].find_nearest(p.center, d)[0] is not None for n in nombres):
                p.material_index = indice
                cuenta[indice] = cuenta.get(indice, 0) + 1
                break
    return cuenta


def pintar_por(objeto, indice, condicion):
    """Asigna `indice` a las caras cuyo centro cumple `condicion(centro)`."""
    ob = bpy.data.objects[objeto] if isinstance(objeto, str) else objeto
    n = 0
    for p in ob.data.polygons:
        if condicion(p.center):
            p.material_index = indice
            n += 1
    return n
