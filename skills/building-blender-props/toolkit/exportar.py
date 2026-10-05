"""Exportacion de la low poly a FBX y GLB."""
import os

import bpy


def fbx_glb(objetos, destino, nombre):
    """Exporta solo `objetos` (nombres), con escala de metros y sin texturas
    embebidas: el FBX referencia los mapas por ruta relativa."""
    os.makedirs(destino, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for n in objetos:
        o = bpy.data.objects[n]
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[objetos[0]]
    fbx = os.path.join(destino, nombre + ".fbx")
    glb = os.path.join(destino, nombre + ".glb")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="EDGE", use_tspace=True,
                             use_mesh_modifiers=True, path_mode="RELATIVE", embed_textures=False,
                             bake_anim=False, axis_forward="-Z", axis_up="Y")
    bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_format="GLB",
                              export_apply=True, export_yup=True)
    return {"fbx": fbx, "glb": glb,
            "ok": all(os.path.exists(p) and os.path.getsize(p) > 1024 for p in (fbx, glb)),
            "bytes": {os.path.basename(p): os.path.getsize(p) for p in (fbx, glb) if os.path.exists(p)}}
