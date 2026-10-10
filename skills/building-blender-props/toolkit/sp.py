"""Mando de Substance 3D Painter desde la terminal, a traves del MCP sp-mcp.

    python sp.py estado
    python sp.py proyecto <Prop> <Set> [--extrusion 0.007]   crea el .spp, hornea desde el HP e importa las mascaras
    python sp.py normal   <Prop> <Set>                       usa la normal horneada en Blender (relieve de material) como mesh map
    python sp.py importar <Prop> <ruta en el prop> [...]            imagenes sueltas como textura (un escaneo de Texturas/Fuente)
    python sp.py rehacer  <Prop> [vistas.json]               borra la pila, aplica <Prop>/texturizar_sp.py y captura
    python sp.py ver      <Prop> <vistas.json>               solo capturas
    python sp.py exportar <Prop> <Set>                       exporta e instala TX_<Set>_{BaseColor,Normal,ORM}.png
    python sp.py llamar   <herramienta> ['<json>']           una herramienta sp_* suelta

Painter tiene que estar abierto, sin minimizar y con la sesion de Windows sin bloquear.
El repo del MCP se toma de SP_MCP_REPO o de ../../SubstancePainter-MCP; la carpeta de props, de
SP_PROPS_ROOT o del padre de este fichero.

`<Prop>/texturizar_sp.py` define `construir()` y devuelve una `sp_receta.Receta`.
Las capturas se copian a <Prop>/_sp_mcp/vistas/NN_<nombre>.jpg (fuera de git).
vistas.json = [{"nombre": "hoja", "yaw": 20, "pitch": -50, "target": [x, y, z], "distance": 0.2}, ...]
con target en coordenadas de Painter: (Bx, Bz, -By) en metros respecto a Blender.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get("SP_PROPS_ROOT") or os.environ.get("BLENDER_PROPS_ROOT") or os.path.dirname(AQUI)      # carpeta que contiene los props
MCP = os.environ.get("SP_MCP_REPO") or os.path.normpath(os.path.join(RAIZ, "..", "SubstancePainter-MCP"))


def llamar(pasos, eco=True):
    """Ejecuta una lista [{tool, args}] en UNA sesion del servidor. Devuelve [(json|None, [imagenes], error)]."""
    fd, lote = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf8") as fh:
        json.dump(pasos, fh)
    try:
        p = subprocess.run(["uv", "run", "--project", "server", "python", "server/tests_live/mcp_call.py", "--batch", lote],
                           cwd=MCP, capture_output=True, text=True, encoding="utf8", errors="replace")
    finally:
        os.remove(lote)
    res, cur = [], None
    for ln in p.stdout.splitlines():
        if ln.startswith("=== ["):
            cur = [None, [], ln.rstrip().endswith("ERROR")]
            res.append(cur)
        elif cur is None:
            continue
        elif ln.startswith("{") and cur[0] is None:
            try:
                cur[0] = json.loads(ln)
            except ValueError:
                cur[0] = {"_texto": ln[:2000]}
        elif ln.startswith("[imagen] "):
            cur[1].append(ln[9:].strip())
        elif ln.startswith("Error executing tool"):
            cur[0], cur[2] = {"_error": ln}, True
        elif cur[2] and ln.startswith("Datos:"):
            cur[0]["_datos"] = ln[:3000]
    if eco:
        for paso, (d, imgs, err) in zip(pasos, res):
            txt = json.dumps(d, ensure_ascii=False) if d else ""
            print(("ERROR " if err else "ok    ") + paso["tool"], txt[:900 if err else 260])
    if len(res) < len(pasos):
        print("... se paro en el paso %d de %d" % (len(res), len(pasos)))
    return res


def rutas(prop):
    r = os.path.join(RAIZ, prop)
    return {"raiz": r, "spp": os.path.join(r, prop + ".spp"), "tex": os.path.join(r, "Texturas"),
            "mascaras": os.path.join(r, "Texturas", "Bakes", "Mascaras"),
            "export": os.path.join(r, "Texturas", "Bakes", "SP_export"),
            "lp": os.path.join(r, "Exportados", prop + "_LP.fbx"), "hp": os.path.join(r, "Exportados", prop + "_HP.fbx"),
            "vistas": os.path.join(r, "_sp_mcp", "vistas")}


def u(p):
    return p.replace("\\", "/")


def proyecto(prop, ts, extrusion=0.007):
    """Proyecto nuevo desde la low poly (OpenGL, 4096), horneado desde el high poly e importacion de
    todas las mascaras. `extrusion` es relativa a la diagonal de la escena (0.007 de 0.36 m = 2.5 mm)."""
    R = rutas(prop)
    for k in ("lp", "hp"):
        if not os.path.exists(R[k]):
            sys.exit("falta " + R[k])
    pasos = [{"tool": "sp_project_create", "args": {"mesh_path": u(R["lp"]), "normal_format": "OpenGL", "resolution": 4096,
                                                    "close_current": True, "discard_changes": True}},
             {"tool": "sp_project_save", "args": {"mode": "save_as", "path": u(R["spp"])}},
             {"tool": "sp_bake", "args": {"size": 4096, "high_meshes": [u(R["hp"])],
                                          "common": {"SubSampling": 1, "MaxHeight": extrusion, "MaxDepth": extrusion},
                                          "baker_params": {"Position": {"NormalizationScale": "Full Scene"}},
                                          "timeout_s": 1500}},
             {"tool": "sp_set_display", "args": {"environment": "Studio Tomoco"}, "continue_on_error": True}]
    for f in sorted(os.listdir(R["mascaras"])):
        if f.endswith(".png") and not f.startswith("_"):
            pasos.append({"tool": "sp_import_resource", "args": {"path": u(os.path.join(R["mascaras"], f)), "usage": "texture"}})
    pasos += [{"tool": "sp_list_texture_sets", "args": {"detail": "full"}},
              {"tool": "sp_project_save", "args": {"mode": "save"}}]
    res = llamar(pasos)
    sets = next((d for d, _, _ in res if d and "texture_sets" in d and "active" in d), None)
    if sets:
        t = sets["texture_sets"][0]
        print("set:", t["name"], "| mesh maps:", t.get("baked_mesh_maps"))
        if t["name"] != ts:
            print("AVISO: el texture set se llama", t["name"], "y no", ts)


def normal(prop, ts):
    """Pone la normal horneada en Blender (`substance.normal_hp`, Texturas/Bakes/NORMAL_blender.png) como mesh map
    `Normal` del set. Es el camino cuando el relieve del high poly esta en sus materiales y no en su geometria:
    Painter lo habria perdido. Importa tambien CP_Relieve_* si `sp_mascaras.py` ya las genero."""
    R = rutas(prop)
    src = os.path.join(R["tex"], "Bakes", "NORMAL_blender.png")
    if not os.path.exists(src):
        sys.exit("falta " + src)
    pasos = [{"tool": "sp_import_resource", "args": {"path": u(src), "usage": "texture"}}]
    for f in ("CP_Relieve_Canto.png", "CP_Relieve_Hueco.png"):
        if os.path.exists(os.path.join(R["mascaras"], f)):
            pasos.append({"tool": "sp_import_resource", "args": {"path": u(os.path.join(R["mascaras"], f)), "usage": "texture"}})
    res = llamar(pasos, eco=False)
    url = (res[0][0] or {}).get("url")
    if not url:
        sys.exit("no se pudo importar la normal: %s" % (res[0][0],))
    codigo = chr(10).join([
        "import substance_painter.textureset as ts, substance_painter.resource as rs",
        "t = ts.TextureSet.from_name(%r)" % ts,
        "t.set_mesh_map_resource(ts.MeshMapUsage.Normal, rs.ResourceID.from_url(%r))" % url,
        "r = t.get_mesh_map_resource(ts.MeshMapUsage.Normal)",
        "__result__ = {'normal': r.name if r else None}"])
    out = llamar([{"tool": "sp_exec_python", "args": {"code": codigo, "undo_group": False}},
                  {"tool": "sp_wait_idle", "args": {"timeout_s": 120, "quiet_ms": 3000}},
                  {"tool": "sp_project_save", "args": {"mode": "save"}}])
    return out


def _receta(prop):
    spec = importlib.util.spec_from_file_location("texturizar_sp", os.path.join(RAIZ, prop, "texturizar_sp.py"))
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, AQUI)
    spec.loader.exec_module(m)
    return m.construir()


def _capturas(vistas):
    pasos = []
    for v in vistas:
        if v.get("hoja"):
            pasos.append({"tool": "sp_contact_sheet", "args": {"views": v["hoja"], "cell_px": 1024, "max_px": 1568}})
        else:
            a = {k: v[k] for k in ("yaw", "pitch", "target", "distance") if k in v}
            pasos += [{"tool": "sp_set_camera", "args": a}, {"tool": "sp_screenshot", "args": {"view": "current", "max_px": 1568}}]
    return pasos


def _recoger(prop, vistas, res):
    R = rutas(prop)
    os.makedirs(R["vistas"], exist_ok=True)
    imgs = [i for _, im, _ in res for i in im]
    out = []
    for k, (v, src) in enumerate(zip(vistas, imgs)):
        dst = os.path.join(R["vistas"], "%02d_%s%s" % (k, v.get("nombre", "vista"), os.path.splitext(src)[1]))
        shutil.copyfile(src, dst)
        out.append(dst)
        print("vista:", dst)
    return out


def rehacer(prop, vistas=()):
    """Borra las capas que haya y aplica la receta del prop. Determinista: el mismo script da la misma pila.
    (No se usa sp_undo: en 12.1 revienta con 'QAction already deleted'.)"""
    r = _receta(prop)
    st = llamar([{"tool": "sp_get_layer_stack", "args": {"texture_set": r.ts, "max_depth": 0}}], eco=False)[0][0]
    rec = r.json(borrar=[l["uid"] for l in st["layers"]])
    seco = llamar([{"tool": "sp_apply_recipe", "args": {"recipe": rec, "dry_run": True}}], eco=False)[0]
    if seco[2] or not (seco[0] or {}).get("valid"):
        print("receta NO valida:", json.dumps(seco[0], ensure_ascii=False)[:3000])
        return None
    res = llamar([{"tool": "sp_apply_recipe", "args": {"recipe": rec}}, {"tool": "sp_wait_idle", "args": {"timeout_s": 300, "quiet_ms": 8000}}]
                 + _capturas(vistas), eco=False)       # 3 s de calma no bastan con rellenos de imagen: la madera salia blanca
    d = res[0][0] or {}
    print("receta:", "ERROR " + json.dumps(d, ensure_ascii=False)[:3000] if res[0][2] else "%d ops" % d.get("ops", 0))
    return _recoger(prop, vistas, res[2:])


def ver(prop, vistas):
    return _recoger(prop, vistas, llamar(_capturas(vistas), eco=False))


def medir(ts):
    """Avisos PBR por canal (albedo fuera de rango, metal no binario, roughness plano)."""
    res = llamar([{"tool": "sp_map_stats", "args": {"channel": c, "texture_set": ts}} for c in ("baseColor", "roughness", "metallic")],
                 eco=False)
    return [d for d, _, _ in res]


def exportar(prop, ts):
    """ORM empaquetado (preset de Unreal: R=AO, G=Roughness, B=Metallic) + BaseColor a 8 bits, y la normal
    OpenGL a 16 bits del preset de Blender. Las instala como Texturas/TX_<Set>_*.png y guarda el .spp."""
    R = rutas(prop)
    res = llamar([{"tool": "sp_wait_idle", "args": {"timeout_s": 180, "quiet_ms": 3000}},
                  {"tool": "sp_export_textures", "args": {"out_dir": u(R["export"]), "preset": "Unreal Engine (Packed)", "bit_depth": "8"}},
                  {"tool": "sp_export_textures", "args": {"out_dir": u(R["export"]), "preset": "Blender (Principled BSDF)", "bit_depth": "16"}},
                  {"tool": "sp_project_save", "args": {"mode": "save"}}], eco=False)
    if any(e for _, _, e in res) or len(res) < 4:
        print("exportacion fallida:", [d for d, _, e in res if e])
        return None
    base = os.path.basename(R["lp"])[:-4]
    corto = ts[3:] if ts.startswith("LP_") else ts
    pares = {"BaseColor": "%s_%s_BaseColor_sRGB.png" % (base, ts), "ORM": "%s_%s_OcclusionRoughnessMetallic_Raw.png" % (base, ts),
             "Normal": "%s_Normal_Raw.png" % ts}
    out = {}
    for k, f in pares.items():
        src, dst = os.path.join(R["export"], f), os.path.join(R["tex"], "TX_%s_%s.png" % (corto, k))
        for intento in range(12):                 # Blender tiene el mapa abierto mientras renderiza: Errno 22 al sobrescribir
            try:
                shutil.copyfile(src, dst)
                break
            except OSError:
                if intento == 11:
                    raise
                time.sleep(2)
        out[k] = (dst, os.path.getsize(dst))
        print("instalado:", dst, os.path.getsize(dst) // 1024, "KB")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    cmd = a[0] if a else "estado"
    if cmd == "estado":
        llamar([{"tool": "sp_status", "args": {}}])
    elif cmd == "proyecto":
        proyecto(a[1], a[2], float(a[a.index("--extrusion") + 1]) if "--extrusion" in a else 0.007)
    elif cmd == "normal":
        normal(a[1], a[2])
    elif cmd == "importar":
        llamar([{"tool": "sp_import_resource", "args": {"path": u(os.path.join(RAIZ, a[1], f)), "usage": "texture"}} for f in a[2:]])
    elif cmd == "rehacer":
        rehacer(a[1], json.load(open(a[2], encoding="utf8")) if len(a) > 2 else ())
    elif cmd == "ver":
        ver(a[1], json.load(open(a[2], encoding="utf8")))
    elif cmd == "medir":
        for d in medir(a[1]):
            print(json.dumps(d, ensure_ascii=False)[:600])
    elif cmd == "exportar":
        exportar(a[1], a[2])
    elif cmd == "llamar":
        llamar([{"tool": a[1], "args": json.loads(a[2]) if len(a) > 2 else {}}])
    else:
        sys.exit(__doc__)
