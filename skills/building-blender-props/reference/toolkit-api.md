# Toolkit API

Every public function in `../toolkit/`, derived from the code. Units: metres
unless a name says `_mm`. `coleccion` is always a collection **name**. `q` is
the quality factor: `1.0` high poly, `0.2`–`1.0` low poly.

Conventions that hold everywhere:

- Shape functions **always create a new object** and link it to `coleccion`.
  They never look one up by name.
- Temporary solids and cutters are named with a leading underscore
  (`"_deposito"`, `"_hueco_base"`). Cutter base names (before `.001`) are the
  keys used by `colada.pintar` and by `conservar` in `lowpoly.union_mecanizada`.
- Functions that measure return a dict; `ok` is `False` when nothing was
  evaluated.

## formas — parametric solids (`import formas as F`)

Constants: `F.MM = 0.001`, `F.EJES = {"X","Y","Z"}`.

### Profiles (return numpy arrays, create nothing)

| Signature | Returns | Use |
|---|---|---|
| `seg(n, q, minimo=3)` | `int` | segment count scaled by `q`, floored at `minimo` |
| `perfil_rect(w, h, r=0.0, s=0)` | `(M,2)` | centred rectangle, corners rounded with `s` segments |
| `perfil_circ(r, n, ry=None, fase=0.0)` | `(n,2)` | circle or ellipse |
| `superelipse(ax, ay, n, exp=2.5, t0=0.0, t1=2π, cerrado=True)` | `(n,2)` | squircle section for housings |
| `spline(puntos, n=8, cerrada=True, vivos=())` | `(M·n, k)` | Catmull-Rom through traced points; indices in `vivos` keep a sharp corner. Use for any outline drawn with a dozen points |
| `hexagono(entre_caras)` | `(6,2)` | hex by across-flats width |
| `disco(n)` | `(rho, theta)` grids `(n+1)²` | concentric square-to-disc map: all quads, no pole. For domes |

### Meshes (return the new object)

| Signature | Use |
|---|---|
| `barrido(nombre, camino, perfil, arriba, coleccion, cerrado=False, suave=True)` | sweep `perfil` (M,2) along `camino` (N,3); `arriba` orients the profile. Tubes, wires, handles; `cerrado=True` for rings |
| `prisma(nombre, contorno, origen, eje, alto, coleccion, bisel=0.0, s=0, suave=False, por_normal=False)` | extrude a flat outline along `eje`; `bisel`,`s` round both caps. `por_normal=True` offsets the bevel along the outline normal — required on elongated or concave outlines |
| `cilindro(nombre, radio, origen, eje, alto, n, coleccion, bisel=0.0, s=0)` | cylinder from an origin |
| `cil(nombre, radio, eje, a, b, n, coleccion, centro=(0.0, 0.0), bisel=0.0, s=0)` | cylinder between coordinates `a` and `b` on `eje`; `centro` = the other two coordinates in order (X: y,z · Y: x,z · Z: x,y) |
| `revolucion(nombre, perfil_rz, n, origen, eje, coleccion, suave=True)` | lathe a CLOSED `(r, z)` outline walked once; points with r = 0 lie on the axis |
| `tubo(nombre, r_ext, r_int, origen, eje, alto, n, coleccion, bisel=0.0)` | ring or bushing, optional chamfer |
| `caja(nombre, x, y, z, coleccion, r=0.0, s=0)` | box by intervals `(x0,x1),(y0,y1),(z0,z1)`; rounds only the four vertical edges. Use for cutters and hidden solids |
| `caja_blanda(nombre, x, y, z, coleccion, r, s=6, canto=None, sc=4)` | box with all twelve edges rounded; clamps `r` to 0.49 × the short side. Use for anything visible |
| `loft(nombre, secciones, coleccion, suave=True)` | skin sections of equal point count, capped |
| `domo(nombre, centro, lado, ry, rz, rx, n, coleccion, exp=0.75, plano=2.6)` | half super-ellipsoid closed by a flat cap, growing along `lado`·X |
| `texto(nombre, cadena, alto, relieve, coleccion, origen=(0,0,0), normal="-Y", fuente=None)` | text as a closed mesh, centred on `origen`, facing `normal` (`-Y +Y +X -X +Z`). `relieve=0.0` gives a flat decal; `relieve>0` a solid for cast lettering |
| `unir(nombre, objetos)` | join into the first object and rename it. No boolean |
| `circular(objeto, n, eje="Z", centro=(0,0,0), incluir_original=True)` | list of the object plus n−1 rotated copies (bolt circles, vents) |

### Casting and machining

| Signature | Returns | Use |
|---|---|---|
| `fundir(nombre, objetos, voxel, suavizado=6, factor=0.5)` | object | join, voxel-remesh, smooth: one closed skin with fillets of about `voxel·√suavizado`. Rounds everything — cut flats afterwards |
| `mecanizar(objeto, cortadores, soldar=0.0, operacion="DIFFERENCE", solver="EXACT")` | object | one boolean pass with all cutters as a collection operand; deletes the cutters. `soldar` merges only inside each cutter's box + 2 mm. `operacion="UNION"` to add volumes |
| `sombrear(objeto, angulo_grados=40)` | object | smooth shading with sharp edges by angle. Call on every part, HP (40) and LP (50) |
| `volumen_cm3(nombre)` | `float` | enclosed volume; only meaningful on a watertight mesh. For mass and capacity checks |

## colada — cast or moulded parts (`import colada`)

| Signature | Returns | Use |
|---|---|---|
| `colar(nombre, solidos, cortes=(), textos=(), voxel=0.6e-3, fino=0.45e-3, suavizado=8, suavizado_fino=2, solver="MANIFOLD", exactos=())` | object, shaded at 40° | the whole cast part: coarse cast → union `exactos` → cut `cortes` → fine remesh with `textos` fused in. Stores each cutter's footprint for `pintar` |
| `pintar(objeto, reglas, dist=None, fino=0.45e-3)` | `{indice: faces}` | material index by proximity to cutters: `reglas = [(indice, ("_panel", "_lcd")), ...]` in priority order; untouched faces get 0. Same session as `colar` |
| `pintar_por(objeto, indice, condicion)` | face count | material index where `condicion(face_center)` is true |

## lowpoly — (`import lowpoly as L`)

Constants: `L.GRUPO_REPLICAS = "Replicas"`, `L.PLANOS` (slice planes recorded by `trocear`).

| Signature | Returns | Use |
|---|---|---|
| `union_mecanizada(nombre, solidos, cortes, conservar, solver="MANIFOLD", soldar=0.3*MM)` | object | LP of a cast part: union the same solids built at low `q`, apply only the cutters whose base name is in `conservar`, then `limpiar` |
| `limpiar(ob, soldar=0.05*MM)` | object | collapse short edges, triangulate, beautify only between coplanar faces. Run on every LP part |
| `trocear(ob, paso, ejes="XYZ", soldar=0.05*MM)` | object | slice with planes every `paso` then `limpiar`. For long thin parts |
| `costura_en_planos(eje, cotas, tol=0.05*MM, donde=None)` | edge predicate | seams on given planes (e.g. `L.PLANOS[name]["X"]`): cut long islands into segments |
| `costura_por_orientacion(ref, umbral=0.0, donde=None)` | edge predicate | seams between face classes by `normal·ref`. 0 splits a tube in two halves; 0.5 separates top / sides / bottom of rounded sheet metal |
| `cualquiera(*predicados)` | edge predicate | OR of predicates, for `uv.desplegar(extra=...)` |
| `marcar(objetos, grupo)` | — | put all vertices in vertex group `grupo`; call BEFORE joining |
| `replicar(nombre, destinos)` | `{ok, copias, tris}` | duplicate each group's faces to new places with the same UVs. `destinos = {grupo: [Matrix or (dx,dy,dz), ...]}`; mirrors get their winding flipped. After unwrap, before silhouette |
| `proxy_bake(nombre, coleccion="LP Collection")` | name `<nombre>_bake` | copy of the LP without replicas, as bake target |
| `quitar_proxy(nombre)` | — | delete that copy |

## uv — (`import uv`)

`uv.VISTA` = default hero direction `(0.8, −1.0, 0.42)`; added cuts hide away from it.

| Signature | Returns | Use |
|---|---|---|
| `desplegar(nombres, margen=0.003, angulo_grados=50, vista=VISTA, extra=None, metodo="MINIMUM_STRETCH", refinado=("ejes", 25, 12, 5, 0))` | `{name: costuras-info, "refinado": [{umbral, costuras}]}` | seams + unwrap + equalised scale + pack. All `nombres` share ONE 0–1 atlas: call once per texture set. Needs a 3D viewport |
| `costuras(nombre, angulo_grados=50, vista=VISTA, max_pasadas=6, extra=None, plana=0.9)` | `{islas, no_disco, costuras, anadidas}` | marks seams only; `no_disco` should be 0 |
| `caras_solapadas(nombre, rejilla=2048)` | set of face indices | which faces overlap — to name the island before adding a seam |
| `caras_uv_nulas(nombre)` | `{ok, nulas, caras}` | faces with zero UV area |

## bake — (`import bake`)

| Signature | Returns | Use |
|---|---|---|
| `hornear(hp, lp, sets, destino, res=4096, extrusion=0.004, max_ray=0.0, margen=16, samples=16, samples_ao=64, unir=True)` | `{ok, sets: {set: {Normal, AO, BaseColor, RM, ORM}}, tiempos_s, res, …}`; also written to `<destino>/Bakes/bake_log.json` | `hp` = HP object names, `lp` = LP object name, `sets = {LP material name: set name}`. Four passes: Normal (16-bit), AO at half res, BaseColor and Roughness+Metallic by emission. Writes `TX_<set>_{BaseColor,Normal,ORM}.png` |
| `material_final(nombre, rutas, transmision=0.0, ior=1.45, alpha=1.0)` | material | delivery material from `rutas = {"BaseColor","ORM","Normal"}`. Clears the node tree: pass `transmision`/`ior` again for glass |

## materiales — high-poly materials (`import materiales as M`)

| Signature | Returns | Use |
|---|---|---|
| `pbr(nombre, mapas, tinte=(1,1,1), tam_m=0.25, rough=(0.0,1.0), metal=None, normal=1.0, suciedad=0.35, color_suciedad=(0.05,0.04,0.03), desgaste=0.0, color_desgaste=(0.8,0.8,0.8), transmision=0.0, ior=1.45, mezcla_tinte=1.0, manchas=0.0, color_manchas=(0.06,0.05,0.04), escala_manchas=9.0, desconchado=0.0, escala_desconchado=45.0)` | material | box-projected PBR (`mapas` from `texturas.descargar_pbr`, or `{}`) × tint, plus cavity dirt (AO node), edge wear (Pointiness), stains and chips. `tam_m` = metres per tile; `rough` = (add, factor). Drop the `color` key to keep only relief and roughness under a flat tint |
| `asignar(objeto, material, limpiar=True)` | slot index | append a material to an object by name |
| `relieve(nombre, tipo, paso, fondo, caja=None, x_min=None, angulo=30.0)` | material | add shader bump to an existing material: `"picado"` (checkering) or `"hoyuelos"` (dimples). `paso`, `fondo` in metres |

## texturas — CC0 downloads (`import texturas`)

| Signature | Returns | Use |
|---|---|---|
| `descargar_pbr(fuente, id_, destino, res="2K")` | `{ok, mapas: {color, normal, roughness, metallic?, ao?, displacement?}, tam, faltan, cero, desde_cache}` | `fuente` = `"ambientcg"` or `"polyhaven"`. Caches, copies into `destino`, fails if a required map is missing or 0×0 |

## prop — scaffolding (`import prop`)

| Signature | Returns | Use |
|---|---|---|
| `configurar(raiz, base=None)` | `{raiz, base, base_existe}` | set production root and template once per session |
| `plantilla()` | path | the studio template in use |
| `rutas(nombre)` | `{raiz, blend, referencias, texturas, texturas_fuente, texturas_bakes, renders, renders_stills, renders_topologia, renders_portafolio, exportados}` | all paths of a prop |
| `crear(nombre)` | `{ok, nuevo, **rutas}` | create the folder tree and `.blend` from the template and open it; refuses if the open session is dirty; never overwrites |
| `guardar(nombre)` | `{ok, bytes, objetos}` | save only if the open file IS that prop's `.blend` |

## estudio — lights and cameras (`import estudio`)

Constants: `REF_ALTO`, `LUCES`, `CAMARAS`, `DIRECCIONES` (object→camera per camera), `GANANCIA`, `VISTAS` (`tres_cuartos perfil frente trasera cenital inferior`).

| Signature | Returns | Use |
|---|---|---|
| `guardar_base()` | — | record the rig's original pose in custom properties; idempotent |
| `escalar_luces(coleccion)` | `{ok, escala, dim_m}` | scale light positions, size and power to the collection's bounding box |
| `encuadrar(camara, coleccion, margen=0.12, res=None)` | `{ok, all_inside, distancia_m, res}` | place the camera along its `base_dir` at the minimum distance that fits the bbox; sets the resolution itself. Negative `margen` crops in for detail shots |
| `vistas_previas(coleccion, carpeta, vistas=("tres_cuartos","perfil","frente"), res=(900,900), samples=24, prefijo="prev")` | `[{vista, ruta, ok}]` | fast isolated renders to JUDGE SHAPE against the reference photo |
| `preparar(coleccion, camara="CAM_Beauty", res=(2560,2560), margen=0.12)` | dict | `guardar_base` + `escalar_luces` + `encuadrar` |

## exportar / reexportar

| Signature | Returns | Use |
|---|---|---|
| `exportar.fbx_glb(objetos, destino, nombre)` | `{fbx, glb, ok, bytes}` | FBX (edge smoothing, tangents, relative texture paths) and GLB of the named objects only |
| `reexportar.empezar(props)` | `{abierto}` | queue props for re-export and open the first `.blend` |
| `reexportar.paso()` | `{exportado, caras_planas, tris, ok, diffs, quedan}` or `{fin, hecho}` | export the open prop, verify, open the next. One MCP call per step |

## laminas — delivery sheets (`import laminas`)

| Signature | Returns | Use |
|---|---|---|
| `par_split(objetos_lp, camara, carpeta, res=(3840,2160), samples=160, grosor=0.0005, solo_alambre=(), tambien=(), ocultar_en_render=())` | `{ruta, ok, res, misma_camara}` | both split passes from ONE untouched camera, composed. Writes `split_render.png`, `wireframe.png`, `split.png` |
| `wireframe(objetos, camara, salida, res=(2560,2560), samples=64, grosor=0.0009, ocultar=(), solo_alambre=(), tambien=())` | `{ruta, ok, res}` | LP in clay with its mesh drawn. `solo_alambre`: transparent parts drawn as wire only; `tambien`: display stand in clay, no wire |
| `split(ruta_render, ruta_wire, salida, grosor_linea=3)` | `{ruta, ok, res}` | diagonal composite of two same-camera images |
| `hoja_uv(objetos, salida, res=2048, fondo=…, linea=…)` | `{ruta, ok, res}` | UV sheet, one square per object side by side |
| `tira_mapas(rutas, salida, lado=1024)` | `{ruta, ok, res}` | horizontal strip of maps |
| `a_webp(png, webp, calidad=88)` | `{ruta, ok, error}` | ffmpeg conversion |

## puertas — gate batches in Spanish (`import puertas`)

Thin wrappers over `verifications`; thresholds live in verifying-blender-props.

| Signature | Returns |
|---|---|
| `geometria(nombres, max_aspecto=100)` | `{ok, evaluated, caras, fallos}` — manifold + degenerate faces + applied scale per part |
| `ensamblaje(nombres)` | `{ok, evaluated, pairs, disagreement, unverified_parts, open_meshes}` |
| `distancia_minima(a, b)` | `{min_mm, vertices_por_dentro}` |
| `texturas_en_disco(directorio, esperado)` | `texture_files` result |
| `piso_densidad(nombres, texture_res, piso_px_mm)` | `{ok, evaluated, min_px_mm, piso, below_floor}` |
| `ida_y_vuelta_fbx(ruta, tris, capas_uv=1, materiales=None, dims_mm=None, tol_mm=0.5)` | `fbx_roundtrip` result |
| `huella(coleccion)` / `huella_intacta(coleccion, antes)` | `{name: (verts, faces)}` / `{ok, faltan, nuevas, cambiadas}` — HP untouched by the LP build |
| `fugas(nombres, punto, permitidas=(), n=4000)` | `{ok, evaluated, escapes, direccion_media}` — leak test of a cavity |
| `fidelidad_bake(col_hp, col_lp, camara, salida_dir, res=(1024,1024), samples=48, ocultar=())` | `bake_fidelity` result |

## entrega — closing phases (`import entrega`)

| Signature | Returns | Use |
|---|---|---|
| `exportar_y_verificar(nombre, objetos_lp, materiales)` | `{export, tris, dims_mm, ida_y_vuelta}` | FBX + GLB into `Exportados/` as `<nombre>_LP.*` and round-trip gate |
| `still(nombre, fichero, direccion, res=(3840,2160), samples=160, margen=0.02, ocultar=(), relleno=None)` | `{ruta, ok, encuadre, t}` | one beauty still of the HIGH POLY into `Renders/Stills/`. `relleno = (position, watts, size_m)` adds a temporary fill light. One still per MCP call |
| `laminas_tecnicas(nombre, objetos_lp, mapas, solo_alambre=(), tambien=(), grosor=0.0005)` | `{split, uv, maps}` | split + wireframe + `uv.png` + `maps.png` |
| `paquete_portafolio(nombre, hero="01_hero.png")` | `{render, split, wireframe, uv, maps: {ok, kb}}` | the five `.webp` in `Renders/Portafolio/` |
| `cerrar(nombre, esperados)` | `{guardar, en_disco, rutas_externas_faltantes}` | save, check the `.blend` ON DISK via a copy, list missing external paths |

## tanda — the common tail (`import tanda`)

| Signature | Returns | Use |
|---|---|---|
| `medir_uv(nombres)` | `{name: {overlap: [1024, 2048], cov, px_mm, null}, ok}` | UV gates per object, before replicas and before joining sets |
| `malla(nombre)` | `{boundary, nonmanifold, ngons, max, over_100, ok}` | LP mesh gate |
| `hornear_y_exportar(nombre, lp_nombre, solidos_hp, sets, hero, extrusion, vistas=None, scratch=None)` | `{bake_s, tex, silueta: {vista: (px %, area %)}, fidelidad: (ok, mean, smooth), export}`; also `<prop>/_ultimo.json` | bake at 4096² (margin 6, 8 samples, AO 24) from HP + `Rotulos`, build `LP_<set>` materials, silhouette from three views, fidelity from `hero`, export, round-trip, save |
| `cerrar(nombre, lp_nombre, sets, hero, esperados, grosor=0.0008)` | `{split, paquete, cerrar, faltan}` | technical sheets with the hero camera, portfolio package, on-disk check |

`sets` here is a list of set NAMES: the LP materials must be called `LP_<set>`.

## pdf_a_referencia — run with system Python

```
python pdf_a_referencia.py ficha.pdf <prop>/Referencias [prefijo] [max_paginas]
```

Prints the text of each page and saves `<prefijo>_p<N>.png` at 120 dpi. Needs PyMuPDF.

## tela — cloth skins and sewn-on parts (`import tela as T`)

Workflow and measured settings: the building-blender-soft-goods skill.
`T.TEJIDOS` holds stiffness presets (`"cordura"`, `"lona"`, `"nailon_fino"`,
`"cuero"`): (tension, compression, shear, bending, vertex mass).

| Signature | Returns | Use |
|---|---|---|
| `bolsa(nombre, x, y, z, paso, coleccion, triangular=True, semilla=0)` | object | closed box meshed at `paso`, randomly triangulated; a test bag or a simple pouch |
| `grupo(ob, nombre, peso)` | vertex count | vertex group from `peso(co) -> 0..1` |
| `simular(ob, tejido="cordura", presion=8.0, frames=40, fijo=None, encoge=None, encogido=(0.0, 0.0), gravedad=0.0, calidad=8, autocolision=False, distancia=1.5e-3, colisionadores=(), aplicar=True, amortiguacion=5.0)` | `{s, s_por_frame, verts}` | inflate a closed mesh and apply the result. `fijo` = pinned group; `encoge` weights interpolate `encogido=(min, max)`, negative = slack |
| `alisar(ob, pasadas=3, factor=0.5, grupo_fijo=None)` | object | Laplacian smoothing after the simulation |
| `medir(ob, area_inicial=None)` | dict | self-crossing faces, open edges, area, enclosed volume in litres, dihedral mean and p95, edge lengths |
| `diezmar(nombre, origen, tris, coleccion)` | object | decimated copy: the low poly of a simulated skin |
| `arbol_de(objetos)` | `(BVHTree, bmesh)` | one tree over the skin plus what is already sewn on it; free the bmesh afterwards |
| `trazar(superficie, guia, paso=3 mm, separacion=0.6 mm, tension=12, arbol=None, rayo=None, hacia=None, retroceso=None)` | `(points, normals)` | project a rough polyline onto the surface and tension it. `rayo` = fixed direction; `hacia` = fixed target point; neither = nearest point |
| `apoyar(P, N, ancho, separacion, arbol, pasadas=4)` | `(points, max lift)` | lift a traced line until a ribbon of `ancho` clears the surface at its edges |
| `cinta(nombre, puntos, normales, ancho, grueso, coleccion, canto=0.3 mm)` | object | ribbon through points, bottom face on them; square-edged under 2 mm thick |
| `cincha(nombre, superficie, guia, ancho, grueso, coleccion, separacion=0.6 mm, tension=12, arbol=None, onda=None, devolver=False, rayo=None, hacia=None, paso=3 mm, pistas=5)` | object or `(object, P, N)` | `trazar` + ribbon. With `rayo`, the ribbon conforms across its width between `pistas` parallel tracks; `onda=(pitch, height)` lifts it between stitches |
| `cajitas(nombre, P, N, paso, tam, coleccion, alza=0.0)` | object | a row of boxes `tam=(w, l, h)` every `paso`, one mesh: zipper teeth, bar tacks |
| `marco(p, t, n)` | 4×4 matrix | places a part built with Y = length, Z = thickness at `p`, along tangent `t`, facing `n` |
| `asentar(ob, arbol, n, holgura=0.2 mm, alto=0.02)` | lift in metres | raise a rigid part along `n` until no vertex is under the surface (ray test) |
| `largo(P)` | array | arc length at each point |

## Added since the first batch

| Signature | Use |
|---|---|
| `lowpoly.cortar_en(ob, eje, cotas, ajuste=0.6 mm)` | cut a mesh on planes and leave clean edge loops there, for `costura_en_planos`; snaps nearby vertices to the plane instead of leaving slivers |
| `bake.hornear(..., solo_ao=False)` | `solo_ao=True` rebakes only occlusion and recomposes the ORM from `Bakes/TX_<set>_RM.png` (or from the delivered ORM when that file does not exist) |
| `bake.material_final(nombre, rutas, transmision=0.0, ior=1.45, alpha=1.0, ao=0.0)` | `ao` multiplies base colour by the occlusion channel, for renders only |
| `tanda.hornear_y_exportar(..., ao=0.0, solo_medir=False)` | `solo_medir=True` skips the bake and re-measures silhouette, fidelity and export on the maps already on disk |
| `materiales.relieve(nombre, tipo, paso, fondo, ...)` | new `tipo`: `"tejido"` (plain weave), `"canale"` (webbing ribs), `"arruga"` (soft noise) |


## quads — all-quad low poly (`import quads as Q`)

Why and when: `quad-topology.md`.

| Call | Returns | Notes |
|---|---|---|
| `Q.censo(ob)` | `{caras, tris, quads, ngonos, pct_quads, polos, pct_polos, aristas_no_estancas}` | the gate: `tris == 0 and ngonos == 0` |
| `Q.cuadrar(ob, soldar=0.02mm)` | census + `rejillas`, `sin_resolver` | cap n-gons and pole fans → Coons grids; boundary must be even |
| `Q.ajustar(ob, sobre, solo=None, mezcla=1.0)` | `{max_mm, media_mm, movidos}` | snaps vertices to the nearest point of the meshes `sobre`; `solo(co)` filters |
| `Q.desvio(ob, sobre, tope=2.0)` | `{p50_mm, p95_mm, max_mm, sobre_tope, muestras}` | face and edge midpoints against the high poly |
| `Q.retopo(ob, caras, vivos=None, semilla=0)` | census + `quadriflow` | QuadriFlow in place; decimate to ~60k first |
| `Q.ventana(ob, dentro, fondo)` | faces sunk | `dentro(centre, normal) -> bool`, `fondo(co) -> co`; pocket stays quads and watertight |
| `Q.lamina(nombres, ruta, desde, ancho=2000, grosor=0.35mm, centro=None, radio=None)` | path | 1 s Workbench render of the real edges |

Related additions elsewhere:

| Call | Notes |
|---|---|
| `F.seg(n, q, minimo)` | now rounds to an even count above 4 |
| `F.prisma(..., tramos=1)` | intermediate rings along the axis |
| `F.prisma_anillo(nombre, exterior, interior, origen, eje, alto, col, tramos=1)` | prism of an outline with a through hole; two paired loops |
| `F.remuestrear(puntos, n, cerrada=False)` | `n` equidistant spans along a polyline |
| `L.costura_por_lado(eje, cotas, donde=None)` | UV seam predicate: border between faces on either side of a plane |
| `M.pbr(..., polvo=, color_polvo=, altura_polvo=(z0, z1), sol=, color_sol=)` | dust rising from the floor between two object-space heights; fade on upward faces |
| `M.relieve(..., tinte=, color_tinte=)` | also darkens the base colour in the relief's valleys |
