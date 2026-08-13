# -*- coding: utf-8 -*-
"""
Verifications for a Blender prop pipeline.

Every function returns NUMBERS, not impressions. All of them have been used in
production, and each one caught at least one defect that visual inspection did
not see.

Usage: paste into execute_blender_code, or store as a text datablock in the .blend.

    from verifications import *
    print(manifold("Cuerpo"))
    print(axis_clearance("Pin", "Valvula", axis=(1,0,0), point=(0,-0.008,0.4826), radius=0.00225))
"""

import bpy, bmesh, math, os
from mathutils import Vector


# ─────────────────────────────────────────────────────────── mesh

def _evaluated(name):
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    o = bpy.data.objects[name]
    ev = o.evaluated_get(dg)
    return ev, ev.to_mesh()


def manifold(name):
    """Boundary and non-manifold edges on the EVALUATED mesh (with modifiers).

    Checking the base mesh lies: modifiers can open or close the mesh. A curve
    with a bevel and use_fill_caps can still have its ends wide open."""
    ev, m = _evaluated(name)
    bm = bmesh.new(); bm.from_mesh(m)
    r = {"faces": len(bm.faces),
         "tris": sum(len(f.verts) - 2 for f in bm.faces),
         "boundary": sum(1 for e in bm.edges if e.is_boundary),
         "nonmanifold": sum(1 for e in bm.edges if not e.is_manifold),
         "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
         "triangles": sum(1 for f in bm.faces if len(f.verts) == 3),
         "scale": [round(v, 6) for v in bpy.data.objects[name].scale]}
    bm.free(); ev.to_mesh_clear()
    return r


def dimensions(name, expected_mm=None, tolerance_mm=2.0):
    """Bounding dimensions of the EVALUATED mesh, in mm.

    The Catmull-Clark limit surface does NOT match the base mesh: a ring of N
    sides converges to R*(2+cos(2pi/N))/3. Measuring the base mesh gives you a
    dimension the render does not have."""
    ev, m = _evaluated(name)
    co = [ev.matrix_world @ v.co for v in m.vertices]
    d = [round((max(c[i] for c in co) - min(c[i] for c in co)) * 1000, 3)
         for i in range(3)]
    ev.to_mesh_clear()
    r = {"L_mm": d[0], "W_mm": d[1], "H_mm": d[2]}
    if expected_mm:
        dev = [round(a - b, 3) for a, b in zip(d, expected_mm)]
        r["deviation_mm"] = dev
        r["within_tolerance"] = all(abs(x) <= tolerance_mm for x in dev)
    return r


def degenerate_faces(name, aspect_threshold=8.0):
    """Faces with an extreme aspect ratio. They are the cause of the dirty
    shading around holes cut by a boolean into an already subdivided mesh.

    If ratios above 100:1 show up, the topology is broken even though the
    manifold count comes back perfect."""
    ev, m = _evaluated(name)
    bm = bmesh.new(); bm.from_mesh(m)
    ratios = []
    for f in bm.faces:
        ls = [e.calc_length() for e in f.edges]
        if min(ls) > 1e-9:
            ratios.append(max(ls) / min(ls))
    bm.free(); ev.to_mesh_clear()
    if not ratios:
        return {"faces": 0}
    return {"faces": len(ratios),
            "max": round(max(ratios), 1),
            "over_threshold": sum(1 for a in ratios if a > aspect_threshold),
            "over_20": sum(1 for a in ratios if a > 20),
            "over_100": sum(1 for a in ratios if a > 100)}


def shading(name):
    """Sharp edges and flat faces. A machined part with 0 sharp edges averages
    its normals across every hard corner: drilled holes read as craters and
    chamfers smear away."""
    me = bpy.data.objects[name].data
    at = me.attributes.get("sharp_edge")
    return {"sharp_edges": sum(1 for d in at.data if d.value) if at else 0,
            "edges": len(me.edges),
            "flat_faces": sum(1 for p in me.polygons if not p.use_smooth),
            "faces": len(me.polygons)}


# ─────────────────────────────────────────────────────────── clearances

def axis_clearance(moving, fixed, axis, point, radius, length=None):
    """Clearance of a cylindrical part inside a hole or fitting.

    Returns NEGATIVE if the part passes through material. Catches the case the
    viewport cannot show: a tube poking through the wall of its fitting because
    the curve flexes right after it exits.

    NOTE: the low poly can report positive clearance while the high poly is
    negative, because it tessellates coarser and misses the worst sample.
    ALWAYS measure the high poly."""
    axis = Vector(axis).normalized(); point = Vector(point)
    ev, m = _evaluated(fixed)
    worst, where = 1e9, None
    for v in m.vertices:
        w = ev.matrix_world @ v.co
        d = (w - point).dot(axis)
        if length is not None and not (0.0 <= d <= length):
            continue
        perp = ((w - point) - axis * d).length
        if perp < worst:
            worst, where = perp, [round(c * 1000, 2) for c in w]
    ev.to_mesh_clear()
    return {"min_radius_mm": round(worst * 1000, 3),
            "clearance_mm": round((worst - radius) * 1000, 3),
            "vertex": where,
            "intersects": worst < radius}


def profile_clearance(name, profile, margin=0.0):
    """Clearance of a part against a solid of revolution, given its profile as
    (radius, z) pairs. For hoses, cables and clips against a body."""
    def radius(z):
        if z <= profile[0][1] or z >= profile[-1][1]:
            return 0.0
        for (r1, z1), (r2, z2) in zip(profile, profile[1:]):
            if z1 <= z <= z2:
                t = (z - z1) / (z2 - z1) if z2 != z1 else 0.0
                return r1 + (r2 - r1) * t
        return 0.0
    ev, m = _evaluated(name)
    worst, where = 1e9, None
    for v in m.vertices:
        w = ev.matrix_world @ v.co
        d = (w.x ** 2 + w.y ** 2) ** 0.5 - radius(w.z) - margin
        if d < worst:
            worst, where = d, [round(c * 1000, 1) for c in w]
    ev.to_mesh_clear()
    return {"clearance_mm": round(worst * 1000, 2), "vertex": where,
            "intersects": worst < 0}


def animated_clearance(name, profile, f0, f1, step=2, margin=0.0):
    """Same as profile_clearance but sweeping the animation range.
    A part can clear at rest and intersect halfway through its travel."""
    sc = bpy.context.scene
    saved = sc.frame_current
    worst, worst_f = 1e9, None
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); bpy.context.view_layer.update()
        r = profile_clearance(name, profile, margin)
        if r["clearance_mm"] / 1000 < worst:
            worst, worst_f = r["clearance_mm"] / 1000, f
    sc.frame_set(saved)
    return {"min_clearance_mm": round(worst * 1000, 2), "frame": worst_f,
            "intersects": worst < 0}


def _bvh(name, margin=0.0, max_probes=16):
    """Build a world-space BVH plus a list of points proven to sit in this
    part's own material, for _inside()'s parity ray cast.

    A SINGLE probe is not enough, and the centroid is the worst choice for
    it: a channel section, a tube, a wheel rim or an angled bracket all have
    their centroid in the EMPTY space the part wraps around, not in its
    material — a probe there proves nothing about whether the part's steel
    overlaps a neighbour's. It also fails for a case that looks nothing like
    a corner case in a vehicle body: two axis-aligned panels that overlap by
    pure translation along one axis (a body panel sliding into its
    neighbour) share identical extents on the other two axes, so an
    arbitrary vertex sits exactly on the other part's boundary plane — a ray
    cast from a point ON a face is a coin flip, not a measurement. This is
    also why BVH triangle overlap alone is not enough: every crossing face
    pair in that configuration is parallel or exactly coplanar, which
    general triangle-triangle intersection is defined to treat as
    non-intersecting, so overlap() legitimately returns zero for a real
    interpenetration.

    The fix used here: sample up to max_probes face centers, spread evenly
    across the polygon list, each nudged inward along its own normal by a
    small fraction of the part's bounding diagonal — small enough not to
    punch through a thin wall to the far side, large enough to clear the
    surface itself. That lands inside the material AT the surface, which is
    exactly where a real interpenetration with a neighbour would also be.
    The centroid is kept as one extra, cheap probe for solid convex parts
    where it is reliable. pairwise_intersections accepts a pair as
    overlapping if ANY probe from either side lands inside the other part.
    """
    from mathutils.bvhtree import BVHTree
    ev, m = _evaluated(name)
    mw = ev.matrix_world
    nmat = mw.inverted_safe().transposed().to_3x3()
    verts = [mw @ v.co for v in m.vertices]
    polys = [list(p.vertices) for p in m.polygons]
    # epsilon is ALWAYS 0.0, never `margin`. Passing margin here does not buy
    # proximity detection (measured: zero effect on separated geometry, see
    # _any_near) — it only pads the BVH's own leaf bounds, which makes
    # _inside()'s ray cast re-hit the same padded surface it just left,
    # because the 1e-5 step-off between ray casts is far smaller than any
    # realistic margin. Confirmed: margin=0.02 alone made a two-separate-cube
    # scene exhaust the 64-hit cap on every ray cast, permanently and
    # falsely raising cap_reached. Proximity is _any_near's job alone.
    t = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)

    probes = []
    if verts:
        xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
        diag = ((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2
                + (max(zs) - min(zs)) ** 2) ** 0.5
        inset = min(max(diag * 1e-3, 1e-5), 1e-3)  # 0.01-1 mm, scaled to part size
        probes.append(sum(verts, Vector()) / len(verts))  # centroid: cheap, convex-only
        n_faces = len(m.polygons)
        if n_faces:
            stride = max(1, n_faces // max_probes)
            for i in range(0, n_faces, stride):
                poly = m.polygons[i]
                c_world = mw @ poly.center
                n_world = (nmat @ poly.normal).normalized()
                probes.append(c_world - n_world * inset)
    ev.to_mesh_clear()
    return t, probes


def _inside(tree, point, direction=(0.5774, 0.5774, 0.5774), max_hits=64):
    """Parity ray cast from a single point: odd hit count means enclosed.

    Returns (is_inside, hit_cap_reached). A radiator grille or a fin stack
    can cross more than max_hits surfaces; if the cap is hit the parity is
    unreliable and the caller MUST NOT read a resulting False as clean —
    that is exactly the silent-wrong-answer failure mode this return value
    exists to prevent.
    """
    if point is None:
        return False, False
    p, d, hits = Vector(point), Vector(direction).normalized(), 0
    for _ in range(max_hits):
        loc, nor, idx, dist = tree.ray_cast(p, d)
        if loc is None:
            return hits % 2 == 1, False
        hits += 1
        p = loc + d * 1e-5
    return hits % 2 == 1, True


def _any_inside(tree, points):
    """True if ANY probe point lands inside tree. Also reports whether the
    64-hit ray cast cap was reached on any of them, so the caller can flag
    the result as unreliable instead of trusting a clean False."""
    cap_reached = False
    for pt in points:
        inside, capped = _inside(tree, pt)
        cap_reached = cap_reached or capped
        if inside:
            return True, cap_reached
    return False, cap_reached


def _any_near(tree, points, margin):
    """True if any probe point sits within `margin` of tree's surface.

    Uses BVHTree.find_nearest(point, distance=margin), a genuine
    point-to-surface distance query — NOT BVHTree.FromPolygons' `epsilon`.
    That distinction is load-bearing: measured directly (two axis-aligned
    boxes with a real 0.04 m gap, AND a sharp tip approaching a flat plate
    to rule out the parallel-face degenerate case) epsilon has ZERO effect
    on separated geometry at any magnitude tried, up to 5.0 — 125x the gap.
    epsilon only smooths the numerical precision of the intersection test
    for geometry that is already touching or coincident; it is not a
    Minkowski-style "expand by epsilon" clearance check. find_nearest is.
    """
    if margin <= 0.0:
        return False
    for pt in points:
        loc, nor, idx, dist = tree.find_nearest(pt, margin)
        if loc is not None:
            return True
    return False


def _check_pairs(trees, margin=0.0):
    """Pairwise crossing/containment/proximity check over {name: (bvh, probes)}.

    Shared by pairwise_intersections and animated_intersections so the
    animated sweep can reuse cached BVHs for parts that do not move instead
    of rebuilding all of them every frame.
    """
    names = list(trees.keys())
    pairs, cap_reached = [], False
    for i, a in enumerate(names):
        ta, pa = trees[a]
        for b in names[i + 1:]:
            tb, pb = trees[b]
            ov = ta.overlap(tb)
            if ov:
                pairs.append({"a": a, "b": b, "overlaps": len(ov), "mode": "crossing"})
                continue
            inside_ab, cap1 = _any_inside(tb, pa)
            inside_ba, cap2 = _any_inside(ta, pb)
            cap_reached = cap_reached or cap1 or cap2
            if inside_ab or inside_ba:
                pairs.append({"a": a, "b": b, "overlaps": 0, "mode": "contained"})
            elif margin > 0.0 and (_any_near(tb, pa, margin) or _any_near(ta, pb, margin)):
                pairs.append({"a": a, "b": b, "overlaps": 0, "mode": "near"})
    return pairs, cap_reached


def pairwise_intersections(names_or_collection, margin=0.0):
    """Bulk interpenetration check between sibling parts of an assembly.

    Uncovered by a Corona delivery truck: profile_clearance() measures against a
    SOLID OF REVOLUTION — it takes a (radius, z) profile and computes distance
    to the Z axis. On a vehicle that returns numbers with no meaning, which is
    worse than not measuring. And with ~60 modules that is ~1,770 pairs at
    O(n^2) — checking by hand is not viable, so "it looks well assembled"
    becomes the only evidence, the exact impression this skill exists to
    replace. Same rule as render_cost: measure the time on a representative
    subset before running this on the full assembly, do not find out from a
    frozen session.

    Three outcomes are detected, checked in this order, first match wins:

    - "crossing": BVHTree.overlap found triangles that actually cross.
    - "contained": no triangle crossing, but a parity ray cast from one
      part's probe points (see _bvh) proves it sits inside the other's
      material. This is the ONLY way to catch a bolt fully swallowed by the
      panel it should sit on — it renders identically to a bolt that is
      missing — and it is also what catches the far more common case of two
      axis-aligned panels overlapping by pure translation along one axis,
      where every crossing face pair is parallel or coplanar and
      BVHTree.overlap legitimately returns zero for a real interpenetration.
    - "near": only checked when margin > 0 and neither of the above fired.
      A probe point of one part sits within `margin` of the other's surface,
      via BVHTree.find_nearest — a real point-to-surface distance query.

    CAVEAT on `mode`: it names which code path found the pair, not the true
    topology. A "crossing"-shaped overlap that degenerates to zero BVH
    triangle hits (the parallel/coplanar case above) is still reported as
    "contained", because that is the path that caught it. Downstream code
    should treat `clean` and `overlaps` as the facts and `mode` as a hint.

    margin's effect is ONLY the "near" path above (BVHTree.find_nearest).
    The BVH itself is ALWAYS built with epsilon=0.0, regardless of margin
    — never pass margin as BVHTree epsilon. Two reasons, both measured, not
    assumed: (1) epsilon has ZERO effect on separated geometry at any
    magnitude tried up to 5.0 against a real 0.04 m gap (both a
    parallel-face pair and a sharp tip approaching a flat plate, ruling out
    the parallel-face degenerate case specifically) — it only smooths
    numerical precision for geometry already touching or coincident, so it
    buys nothing. (2) it actively BREAKS _inside()'s ray cast: epsilon pads
    the BVH's leaf bounds, and the 1e-5 step the ray takes off a hit is
    always far smaller than any realistic margin, so the next cast re-hits
    the same padded surface — measured on two cubes separated by 40 mm,
    margin=0.02 alone exhausted the 64-hit cap on every ray cast and left
    cap_reached permanently, falsely, True. So margin does NOT turn a real
    "crossing" near-miss into a hit — it only ever produces "near". And it
    never reaches "contained": the parity ray cast has no notion of margin,
    so two genuinely separate parts are never reported "contained" no
    matter how large margin is.

    `cap_reached` in the returned dict is True if any ray cast hit the
    64-surface parity cap (see _inside) on any pair. When it is True, do not
    trust a `clean == True` result blindly — re-check the flagged geometry.
    """
    if isinstance(names_or_collection, str):
        names = [o.name for o in
                 bpy.data.collections[names_or_collection].all_objects
                 if o.type == 'MESH']
    else:
        names = list(names_or_collection)

    trees = {n: _bvh(n, margin) for n in names}
    pairs, cap_reached = _check_pairs(trees, margin)
    return {"pairs": pairs, "count": len(pairs), "clean": not pairs,
            "cap_reached": cap_reached}


def animated_intersections(moving, others, f0, f1, step=2, margin=0.0):
    """pairwise_intersections swept across an animation range.

    A door clears at rest and eats the B pillar halfway through its travel.
    Checking only the rest pose is checking the one frame that cannot fail.

    `others` are assumed static for the sweep: their BVH+probes are built
    ONCE, before the frame loop, and reused every frame. Only `moving` is
    rebuilt per frame. See pairwise_intersections for what `mode`, `margin`
    and `cap_reached` mean — unchanged here, just accumulated across frames.
    """
    sc = bpy.context.scene
    saved = sc.frame_current
    static_trees = {n: _bvh(n, margin) for n in others}
    bad, worst_f, cap_reached = [], None, False
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        trees = dict(static_trees)
        trees[moving] = _bvh(moving, margin)
        pairs, cap = _check_pairs(trees, margin)
        cap_reached = cap_reached or cap
        for p in pairs:
            if moving in (p["a"], p["b"]):
                bad.append(dict(p, frame=f))
                if worst_f is None:
                    worst_f = f
    sc.frame_set(saved)
    bpy.context.view_layer.update()
    return {"pairs": bad, "worst_frame": worst_f, "clean": not bad,
            "cap_reached": cap_reached}


# ─────────────────────────────────────────────────────────── UV

def uv_density(names, texture_res=4096):
    """Texel density per part. The deviation between parts sharing a set should
    be ~0: if one part has twice the density, the atlas is badly scaled and it
    will show in the render."""
    out, a3t, a2t = {}, 0.0, 0.0
    for n in names:
        bm = bmesh.new(); bm.from_mesh(bpy.data.objects[n].data)
        uv = bm.loops.layers.uv.active
        if uv is None:
            out[n] = "NO UV"; bm.free(); continue
        a3 = sum(f.calc_area() for f in bm.faces); a2 = 0.0
        for f in bm.faces:
            ls = [l[uv].uv for l in f.loops]
            for i in range(1, len(ls) - 1):
                a2 += abs((ls[i].x - ls[0].x) * (ls[i + 1].y - ls[0].y) -
                          (ls[i + 1].x - ls[0].x) * (ls[i].y - ls[0].y)) / 2
        bm.free(); a3t += a3; a2t += a2
        out[n] = round(math.sqrt(a2 / a3) * texture_res / 1000, 3) if a3 else 0
    v = [x for x in out.values() if isinstance(x, float)]
    return {"px_per_mm": out,
            "mean": round(math.sqrt(a2t / a3t) * texture_res / 1000, 3) if a3t else 0,
            "deviation_pct": round(100 * (max(v) - min(v)) / max(v), 3) if v else None}


def uv_overlap(names, grid=1024):
    """Rasterizes the UV islands and counts cells covered more than once.

    A torus (closed ring) needs TWO cuts to unwrap. With only one, the unwrap
    collapses: zero-area UV faces and up to 10 stacked layers, with no other
    check giving it away."""
    import numpy as np
    count = np.zeros((grid, grid), dtype=np.int16); deg = 0
    for name in names:
        bm = bmesh.new(); bm.from_mesh(bpy.data.objects[name].data)
        uv = bm.loops.layers.uv.active
        if uv is None:
            bm.free(); continue
        for f in bm.faces:
            ls = [l[uv].uv for l in f.loops]
            au = sum(abs((ls[i].x - ls[0].x) * (ls[i + 1].y - ls[0].y) -
                         (ls[i + 1].x - ls[0].x) * (ls[i].y - ls[0].y)) / 2
                     for i in range(1, len(ls) - 1))
            if au < 1e-9:
                deg += 1
            for i in range(1, len(ls) - 1):
                tri = np.array([[ls[0].x, ls[0].y], [ls[i].x, ls[i].y],
                                [ls[i + 1].x, ls[i + 1].y]]) * grid
                x0 = max(int(np.floor(tri[:, 0].min())), 0)
                x1 = min(int(np.ceil(tri[:, 0].max())) + 1, grid)
                y0 = max(int(np.floor(tri[:, 1].min())), 0)
                y1 = min(int(np.ceil(tri[:, 1].max())) + 1, grid)
                if x1 <= x0 or y1 <= y0:
                    continue
                xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
                a, b, c = tri
                d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(d) < 1e-12:
                    continue
                w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
                w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
                count[y0:y1, x0:x1] += ((w0 >= 0) & (w1 >= 0) &
                                        ((1 - w0 - w1) >= 0)).astype(np.int16)
        bm.free()
    covered = int((count >= 1).sum())
    return {"coverage_pct": round(100 * covered / grid ** 2, 2),
            "overlapping_cells": int((count >= 2).sum()),
            "max_layers": int(count.max()),
            "degenerate_uv_faces": deg}


# ─────────────────────────────────────────────────────────── render

def silhouette_hp_vs_lp(col_hp, col_lp, camera, res=(1400, 1800), samples=16,
                        hide=()):
    """Renders both collections with a transparent background and compares the
    alpha channel. It is the only honest measure of whether the low poly holds
    the silhouette.

    NOTE: the backdrop must be hidden, or alpha comes back opaque across the
    whole frame and the comparison reports 0% difference for the wrong reason."""
    import numpy as np
    from PIL import Image
    sc = bpy.context.scene; r = sc.render
    vl = bpy.context.view_layer
    tmp = bpy.app.tempdir
    prev = dict(x=r.resolution_x, y=r.resolution_y, s=sc.cycles.samples, p=r.filepath,
                cam=sc.camera, tr=r.film_transparent, w=sc.world,
                fmt=r.image_settings.file_format, cm=r.image_settings.color_mode)
    hidden = {n: bpy.data.objects[n].hide_render for n in hide}
    def excl(name, val):
        for c in vl.layer_collection.children:
            if c.name == name:
                c.hide_viewport = False; c.exclude = val
    try:
        for n in hide:
            bpy.data.objects[n].hide_render = True
        sc.world = None
        r.resolution_x, r.resolution_y = res
        sc.cycles.samples = samples
        r.film_transparent = True
        r.image_settings.file_format = 'PNG'
        r.image_settings.color_mode = 'RGBA'
        sc.camera = bpy.data.objects[camera]
        outputs = {}
        for label, active, other in (("hp", col_hp, col_lp), ("lp", col_lp, col_hp)):
            excl(other, True); excl(active, False)
            r.filepath = os.path.join(tmp, "sil_%s.png" % label)
            bpy.ops.render.render(write_still=True)
            outputs[label] = r.filepath
        excl(col_hp, False); excl(col_lp, False)
    finally:
        for n, v in hidden.items():
            bpy.data.objects[n].hide_render = v
        r.resolution_x, r.resolution_y = prev["x"], prev["y"]
        sc.cycles.samples = prev["s"]; r.filepath = prev["p"]
        sc.camera = prev["cam"]; r.film_transparent = prev["tr"]; sc.world = prev["w"]
        r.image_settings.file_format = prev["fmt"]; r.image_settings.color_mode = prev["cm"]
    a = np.array(Image.open(outputs["hp"]).convert("RGBA"))[:, :, 3].astype(np.int16)
    b = np.array(Image.open(outputs["lp"]).convert("RGBA"))[:, :, 3].astype(np.int16)
    ca, cb = int((a > 128).sum()), int((b > 128).sum())
    diff = int((np.abs(a - b) > 128).sum())
    return {"hp_coverage_px": ca, "lp_coverage_px": cb,
            "area_delta_pct": round(100 * (cb - ca) / max(ca, 1), 3),
            "differing_px_pct": round(100 * diff / max(ca, 1), 3)}


def backdrop_coverage(camera, f0, f1, step=5, res=(480, 270), samples=12):
    """Sets the world to MAGENTA and counts how much of it shows in each frame.

    Magenta at the EDGES of the frame means the backdrop does not cover and must
    be closed. Magenta only in the centre over the object is reflection or
    transmission, which is correct. The distinction matters: looking at the
    image is not enough, because the rim of a backlit cyclorama looks exactly
    like a hole and is not one."""
    import numpy as np
    from PIL import Image
    sc = bpy.context.scene; r = sc.render
    tmp = bpy.app.tempdir
    w = bpy.data.worlds.get("_MAGENTA") or bpy.data.worlds.new("_MAGENTA")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (1, 0, 1, 1)
    nt.links.new(bg.outputs["Background"], o_.inputs["Surface"])
    prev = dict(x=r.resolution_x, y=r.resolution_y, s=sc.cycles.samples,
                p=r.filepath, cam=sc.camera, w=sc.world, f=sc.frame_current)
    worst, edges, detail = (0.0, None), [], []
    try:
        sc.world = w; sc.camera = bpy.data.objects[camera]
        r.resolution_x, r.resolution_y = res
        sc.cycles.samples = samples
        for f in range(f0, f1 + 1, step):
            sc.frame_set(f)
            r.filepath = os.path.join(tmp, "cov_%04d.png" % f)
            bpy.ops.render.render(write_still=True)
            a = np.array(Image.open(r.filepath).convert("RGB")).astype(np.int16)
            m = (a[:, :, 0] > 150) & (a[:, :, 1] < 90) & (a[:, :, 2] > 150)
            pct = 100 * m.sum() / m.size
            if pct > worst[0]:
                worst = (pct, f)
            if m.sum():
                ys, xs = np.where(m)
                h, wd = m.shape
                edge = int(((ys < h * .12) | (ys > h * .88) |
                            (xs < wd * .12) | (xs > wd * .88)).sum())
                if edge:
                    edges.append((f, edge))
                detail.append((f, round(pct, 4)))
    finally:
        sc.world = prev["w"]; sc.camera = prev["cam"]
        r.resolution_x, r.resolution_y = prev["x"], prev["y"]
        sc.cycles.samples = prev["s"]; r.filepath = prev["p"]
        sc.frame_set(prev["f"])
    return {"worst_pct": round(worst[0], 4), "worst_frame": worst[1],
            "frames_with_world": len(detail),
            "frames_with_world_AT_EDGES": edges or "none",
            "verdict": "BACKDROP INSUFFICIENT" if edges else "backdrop covers"}


def framing_check(camera, collection, f0, f1, step=3, margin=0.02):
    """Projects every vertex and checks that nothing leaves the frame across the
    whole range. A part that unfolds may only leave frame for 10 frames."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = bpy.data.objects[camera]
    saved = sc.frame_current
    ext = {"u_min": 1e9, "v_min": 1e9, "u_max": -1e9, "v_max": -1e9}
    fr = {}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); dg.update()
        for o in bpy.data.collections[collection].objects:
            if o.type not in {'MESH', 'CURVE'}:
                continue
            ev = o.evaluated_get(dg); m = ev.to_mesh()
            for v in m.vertices:
                c = world_to_camera_view(sc, cam, ev.matrix_world @ v.co)
                for k, val in (("u_min", c.x), ("v_min", c.y)):
                    if val < ext[k]:
                        ext[k], fr[k] = val, f
                for k, val in (("u_max", c.x), ("v_max", c.y)):
                    if val > ext[k]:
                        ext[k], fr[k] = val, f
            ev.to_mesh_clear()
    sc.frame_set(saved)
    inside = (ext["u_min"] >= margin and ext["v_min"] >= margin
              and ext["u_max"] <= 1 - margin and ext["v_max"] <= 1 - margin)
    return {"extremes": {k: round(v, 4) for k, v in ext.items()},
            "frames": fr, "all_inside": inside}


def turntable_loop(camera, f_start, f_wrap):
    """A turntable of N frames goes from 0 degrees at frame 1 to 360 at frame
    N+1, NOT at N. If frame N matches frame 1, the loop repeats a pose."""
    sc = bpy.context.scene
    cam = bpy.data.objects[camera]
    saved = sc.frame_current
    def pose(f):
        sc.frame_set(f); bpy.context.view_layer.update()
        return cam.matrix_world.copy()
    m0, m1 = pose(f_start), pose(f_wrap)
    steps = []
    for f in range(f_start, f_wrap):
        steps.append((pose(f + 1).translation - pose(f).translation).length)
    sc.frame_set(saved)
    err = max(abs(a - b) for ra, rb in zip(m0, m1) for a, b in zip(ra, rb))
    return {"loop_error": round(err, 9),
            "min_step_mm": round(min(steps) * 1000, 3),
            "max_step_mm": round(max(steps) * 1000, 3),
            "uniform": (max(steps) - min(steps)) < 1e-5}


def render_cost(camera, frames=(1,), res=(1920, 1080), samples=256):
    """Measures seconds per frame BEFORE committing to a batch.
    Run it with compute_device_type set to CUDA and to OPTIX and compare: a GPU
    without RT cores adds raw throughput under CUDA but drags under OptiX."""
    import time
    sc = bpy.context.scene; r = sc.render
    prev = dict(x=r.resolution_x, y=r.resolution_y, s=sc.cycles.samples,
                p=r.filepath, cam=sc.camera, f=sc.frame_current)
    try:
        sc.camera = bpy.data.objects[camera]
        r.resolution_x, r.resolution_y = res
        sc.cycles.samples = samples
        r.filepath = os.path.join(bpy.app.tempdir, "cost_")
        t0 = time.time()
        for f in frames:
            sc.frame_set(f)
            bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
    finally:
        r.resolution_x, r.resolution_y = prev["x"], prev["y"]
        sc.cycles.samples = prev["s"]; r.filepath = prev["p"]
        sc.camera = prev["cam"]; sc.frame_set(prev["f"])
    return {"s_per_frame": round(dt / len(frames), 2),
            "gpus": [d.name for d in
                     bpy.context.preferences.addons['cycles'].preferences.devices
                     if d.use]}
