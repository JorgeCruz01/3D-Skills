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


_PROBE_DIRECTIONS = (
    Vector((0.8018, 0.2673, 0.5345)),
    Vector((-0.3574, 0.8944, 0.2673)),
    Vector((0.1652, -0.5164, 0.8397)),
)  # deliberately skewed: none is an axis, none is (1,1,1)/permutation/
   # reflection of it (the old single-ray direction), none is a permutation
   # or mirror of either other one. A truck chassis is full of axis-aligned
   # faces, so a probe direction that even looks like an axis or the main
   # diagonal is exactly the geometry most likely to graze a surface
   # tangentially instead of crossing it cleanly.


def seating_gap(cover, base, min_mm=0.10, max_mm=0.50, low_pct=10):
    """Two-sided clearance for a part that must SIT ON another surface.

    Every other clearance gate in this file asks one question: is the gap
    positive. That is the right question for parts that must not touch. It
    is the wrong question for a part whose job is to sit ON something — a
    press-on nail, a decal shell, a hub cap, a trim panel, a badge. Those
    fail in TWO directions, and "positive gap" only catches one of them.

    Measured, and it is the reason this function exists: a press-on nail
    modelled over a body's own nail passed `pairwise_intersections` clean,
    passed every positive-clearance check, and had a minimum gap of 0.945 mm
    with a median of 1.558 mm. It was FLOATING a millimetre and a half above
    the surface it was supposed to be glued to. Visible instantly in a
    render once someone thought to look, invisible to every number being
    measured, because floating is a positive gap. Lowering the part until
    the gap read 0.197 mm min / 0.281 mm at the 10th percentile fixed it.

    So the criterion has a floor AND a ceiling:
    - `min_mm`  floor: below this the parts are effectively intersecting,
                and in a game engine that is z-fighting.
    - `max_mm`  ceiling on the LOW percentile, not on the minimum. A fitted
                part only contacts its base over part of its area — a nail
                touches at the bed and lifts away past the free edge — so
                requiring the MEDIAN to be small would be wrong. What must
                be small is the close end of the distribution: the part has
                to actually land somewhere.

    `low_pct` is which percentile carries that ceiling (10 by default).
    Distances are measured from every vertex of `base` to the nearest point
    on `cover`'s evaluated surface, so modifiers count.

    `base` MUST be the surface actually being covered, not the whole body it
    belongs to. Feed it a whole two-hand mesh to check one fingernail and
    almost every sample is metres away: the low percentile then measures
    unrelated anatomy and the function reports "floating" for a part that is
    seated perfectly. Measured exactly that way while testing this function —
    21,966 samples, median 1,079 mm, verdict "floating", nail fine. So
    `contact_pct` is returned alongside: the share of base samples that are
    within the ceiling at all. When that number is near zero the input is
    over-scoped far more often than the part is really floating, and the
    verdict says so instead of quietly blaming the geometry.

    Returns min/low/median/max in mm plus `seated`. `seated` is False both
    when the part bites into its base and when it hovers over it, and
    `verdict` says which.
    """
    from mathutils.bvhtree import BVHTree
    ev_c, mc = _evaluated(cover)
    mwc = ev_c.matrix_world
    tree = BVHTree.FromPolygons([mwc @ v.co for v in mc.vertices],
                                [list(p.vertices) for p in mc.polygons],
                                all_triangles=False, epsilon=0.0)
    ev_c.to_mesh_clear()
    ev_b, mb = _evaluated(base)
    mwb = ev_b.matrix_world
    d = []
    for v in mb.vertices:
        hit = tree.find_nearest(mwb @ v.co)
        if hit[0] is not None:
            d.append(hit[3] * 1000.0)
    ev_b.to_mesh_clear()
    if not d:
        return {"seated": None, "no_geometry_evaluated": True,
                "verdict": "nothing measured"}
    d.sort()
    n = len(d)
    lo = d[min(int(n * low_pct / 100.0), n - 1)]
    contact = sum(1 for x in d if x <= max_mm)
    contact_pct = round(100.0 * contact / n, 2)
    res = {"samples": n,
           "min_mm": round(d[0], 4),
           "low_mm": round(lo, 4),
           "median_mm": round(d[n // 2], 4),
           "max_mm": round(d[-1], 4),
           "low_pct": low_pct,
           "contact_pct": contact_pct}
    if d[0] < min_mm:
        res.update(seated=False, verdict="biting in: min below floor")
    elif lo > max_mm and contact_pct < 2.0:
        res.update(seated=None,
                   verdict="inconclusive: only %.2f%% of base samples are within "
                           "the ceiling. `base` is probably over-scoped — pass the "
                           "surface being covered, not the whole body." % contact_pct)
    elif lo > max_mm:
        res.update(seated=False, verdict="floating: low percentile above ceiling")
    else:
        res.update(seated=True, verdict="seated")
    return res


def _bvh(name, margin=0.0, max_probes=16):
    """Build a world-space BVH plus a list of points PROVEN to sit in this
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

    The candidate points: up to max_probes face centers, spread evenly
    across the polygon list, each nudged inward along its own normal by a
    small fraction of the part's bounding diagonal, plus the centroid.

    SELF-VALIDATION, and why it is not optional: "nudged inward along its
    own normal" assumes the normal is correct and outward-facing. That
    assumption breaks for real production meshes — a join() of several
    sub-parts can leave some faces with reversed winding, and nothing in
    the mesh itself flags it. A candidate built from a flipped normal moves
    OUTWARD instead of inward and lands in whatever empty space the part
    wraps around. Measured on a real chassis: a U-clamp wrapping a bar with
    real clearance (not touching it — BVHTree.overlap == 0, correctly) was
    reported "contained" because one of the clamp's own candidate points
    had drifted into the air gap and happened to land inside the bar. A
    point floating in empty space that isn't part of either solid proves
    nothing about either one, yet it lit up the alarm. So every candidate is
    checked against its OWN part's tree before being trusted: only the ones
    that pass _inside(this_tree, candidate) become probes. One extra ray
    cast per candidate, self-correcting, and it costs nothing when the
    normal was right — which is most of the time.
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

    candidates = []
    if verts:
        xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
        aabb = ((min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)))
        diag = ((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2
                + (max(zs) - min(zs)) ** 2) ** 0.5
        inset = min(max(diag * 1e-3, 1e-5), 1e-3)  # 0.01-1 mm, scaled to part size
        # Centroid kept as one extra candidate: cheap, and self-validation
        # already filters it out on its own for concave parts (it lands in
        # their hollow, same as any other bad candidate), so it can no
        # longer produce a wrong answer — only a redundant one, on convex
        # parts where a face-center probe would have caught it anyway.
        candidates.append(sum(verts, Vector()) / len(verts))
        n_faces = len(m.polygons)
        if n_faces:
            stride = max(1, n_faces // max_probes)
            for i in range(0, n_faces, stride):
                poly = m.polygons[i]
                c_world = mw @ poly.center
                n_world = (nmat @ poly.normal).normalized()
                candidates.append(c_world - n_world * inset)
    else:
        aabb = ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0))

    # Boundary edges, because PARITY IS UNDEFINED ON AN OPEN SURFACE.
    # _inside() counts ray crossings and reads the parity; that only means
    # "enclosed" if the surface actually encloses something. Fire a ray at a
    # shell with a hole in it and some rays leave through the hole, changing
    # the crossing count by one and flipping the answer. Measured on an
    # avatar hand mesh cut at the wrist (68 boundary edges): a nail sitting
    # on a fingertip, comfortably outside the finger, produced disagreement
    # on 418 of its 418 vertices — every single one. The same test against a
    # temporary hole-filled copy of that hand gave 0 disagreements.
    #
    # Reported, not silently repaired: filling holes changes what is being
    # measured, and only the caller knows whether the cap belongs to the
    # solid. The fix at the call site is a TEMP copy plus
    # bmesh.ops.holes_fill(), never the original mesh.
    edge_use = {}
    for poly in m.polygons:
        vs = list(poly.vertices)
        for i in range(len(vs)):
            a_, b_ = vs[i], vs[(i + 1) % len(vs)]
            k = (b_, a_) if a_ > b_ else (a_, b_)
            edge_use[k] = edge_use.get(k, 0) + 1
    open_edges = sum(1 for c in edge_use.values() if c == 1)

    ev.to_mesh_clear()
    probes = [pt for pt in candidates if _inside(t, pt)[0]]
    return t, probes, aabb, open_edges


def _inside(tree, point, max_hits=64):
    """Consensus parity ray cast: odd hit count means enclosed, but only ONE
    ray is not trustworthy enough to decide that on its own.

    Cast from `point` along each of _PROBE_DIRECTIONS and take the parity of
    each independently. Measured, not theoretical: a single ray along the
    old fixed diagonal (1,1,1)/sqrt(3) that grazes a curved surface
    tangentially registers ONE hit where the true crossing count is zero or
    two — parity flips, and a point outside is declared inside. Chassis
    geometry is full of cylinders (axles, tubes, bolts), so this was not a
    rare edge case, it was systematic for that direction on that geometry.
    Reproduced directly: a point positioned so the (1,1,1) ray grazes a
    cylinder came back "inside" under the old single-ray check.

    Requires UNANIMOUS agreement across all three directions to report
    "inside" — not a majority. A 2-1 split means the point is close enough
    to a surface that direction alone changes the answer, which is exactly
    the situation a single ray could not detect and get wrong; the correct
    response is to refuse to call it, not to outvote the doubt.

    Returns (is_inside, hit_cap_reached, disagreement):
    - is_inside: True only if all three rays agree the point is enclosed.
    - hit_cap_reached: True if any single ray hit max_hits surfaces (a
      radiator grille or fin stack can cross more than that); the caller
      MUST NOT read a resulting False as clean when this is True.
    - disagreement: True if the three rays did not all agree (2-1 either
      way). Signals "near a surface, answer not reliable" even when the
      2-1 split happens to still resolve to is_inside == False.
    """
    if point is None:
        return False, False, False
    p0 = Vector(point)
    votes, cap_reached = [], False
    for direction in _PROBE_DIRECTIONS:
        p, d, hits = p0, direction.normalized(), 0
        capped = False
        for _ in range(max_hits):
            loc, nor, idx, dist = tree.ray_cast(p, d)
            if loc is None:
                break
            hits += 1
            p = loc + d * 1e-5
        else:
            capped = True
        cap_reached = cap_reached or capped
        votes.append(hits % 2 == 1)
    unanimous = len(set(votes)) == 1
    return (unanimous and votes[0]), cap_reached, (not unanimous)


def _any_inside(tree, points):
    """True if ANY probe point lands inside tree (unanimous 3-ray consensus,
    see _inside). Also reports whether the ray cap was reached, and whether
    any probe's three rays disagreed with each other — either one means the
    caller should not fully trust a resulting False as clean."""
    cap_reached = disagreement = False
    for pt in points:
        inside, capped, disagree = _inside(tree, pt)
        cap_reached = cap_reached or capped
        disagreement = disagreement or disagree
        if inside:
            return True, cap_reached, disagreement
    return False, cap_reached, disagreement


def _aabb_maybe_close(box_a, box_b, margin=0.0):
    """Exact AABB separating-axis rejection, expanded by `margin`.

    If the gap between the two boxes exceeds `margin` on ANY axis, the
    solids cannot cross, cannot contain each other, and cannot come within
    `margin` — an AABB always contains its solid by definition, so this can
    NEVER produce a false negative, only skip pairs it is mathematically
    certain about. On a ~60-part assembly (~1,770 pairs) the overwhelming
    majority of pairs are parts metres apart; this turns each of those into
    two interval comparisons per axis instead of any ray casting at all —
    and it is not just a speed-up, it is a correctness fix: it is what
    stops _inside()'s ray casts from ever running on a pair that is
    provably separated, which is the only way to guarantee the tangential-
    graze failure mode can't manufacture a "contained" out of thin air.
    """
    for (amin, amax), (bmin, bmax) in zip(box_a, box_b):
        gap = max(amin - bmax, bmin - amax, 0.0)
        if gap > margin:
            return False
    return True


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
    """Pairwise crossing/containment/proximity check over
    {name: (bvh, probes, aabb)}.

    Shared by pairwise_intersections and animated_intersections so the
    animated sweep can reuse cached BVHs for parts that do not move instead
    of rebuilding all of them every frame.

    Every pair is AABB-rejected first (see _aabb_maybe_close) — exact, not
    a heuristic, and it is what makes the containment path safe to run at
    all on a full assembly: it guarantees ray casts only ever run on pairs
    that are already known to be close, so a tangential-graze parity flip
    (see _inside) can no longer manufacture a "contained" between parts
    that are metres apart.

    Returns (pairs, cap_reached, unverified, disagreement, open_meshes).
    - `unverified`: sorted list of names whose self-validated probe list
      came back EMPTY (see _bvh) — every candidate for that part failed its
      own self-check. That part's containment role could not be evaluated
      in either direction for ANY pair: not "clean", "not checked".
    - `disagreement`: True if any containment check's three consensus rays
      failed to agree unanimously on any probe, for any pair — the point
      was close enough to a surface that the answer is not reliable, even
      though it resolved to "not contained".
    - `open_meshes`: {name: boundary_edge_count} for every part that is not
      a closed surface. Containment against any of these is UNDEFINED, not
      merely unreliable (see _bvh). A clean result that includes open
      meshes has not measured containment for those parts at all.
    """
    names = list(trees.keys())
    pairs, cap_reached, disagreement = [], False, False
    unverified = sorted(n for n, (_, probes, _, _) in trees.items() if not probes)
    open_meshes = {n: oe for n, (_, _, _, oe) in trees.items() if oe}
    for i, a in enumerate(names):
        ta, pa, box_a, _ = trees[a]
        for b in names[i + 1:]:
            tb, pb, box_b, _ = trees[b]
            if not _aabb_maybe_close(box_a, box_b, margin):
                continue  # exact rejection: cannot cross, contain, or be within margin
            ov = ta.overlap(tb)
            if ov:
                pairs.append({"a": a, "b": b, "overlaps": len(ov), "mode": "crossing"})
                continue
            inside_ab, cap1, dis1 = _any_inside(tb, pa)
            inside_ba, cap2, dis2 = _any_inside(ta, pb)
            cap_reached = cap_reached or cap1 or cap2
            disagreement = disagreement or dis1 or dis2
            if inside_ab or inside_ba:
                pairs.append({"a": a, "b": b, "overlaps": 0, "mode": "contained"})
            elif margin > 0.0 and (_any_near(tb, pa, margin) or _any_near(ta, pb, margin)):
                pairs.append({"a": a, "b": b, "overlaps": 0, "mode": "near"})
    return pairs, cap_reached, unverified, disagreement, open_meshes


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

    `unverified_parts` lists any part whose probes (see _bvh) were ALL
    discarded by self-validation — every candidate point failed to land
    inside that part's own material, most likely because a join() or
    similar left some of its normals flipped. The containment check could
    not run for that part in either direction. `clean == True` in the
    presence of a non-empty `unverified_parts` is NOT a clearance, it is a
    gap in coverage: fix the geometry (recalculate normals) and re-run.

    Every pair is rejected first by an exact AABB test (see
    _aabb_maybe_close) before any ray is cast — this is what makes it safe
    to run "contained" checks at all across a full assembly: it guarantees
    ray casts never run on a pair that is provably separated, so a stray
    tangential graze cannot manufacture a false "contained" between parts
    that are metres apart (measured in production: three such pairs, AABB
    gaps of tens of centimetres to metres on some axis, reported
    "contained" before this filter existed). It ALSO means the ~1,770-pair
    O(n^2) cost above is mostly two interval comparisons per pair, not a
    ray cast — most pairs in a real assembly are nowhere near each other.

    The containment ray cast itself is a 3-direction UNANIMOUS consensus
    (see _inside), not one ray: a single ray along a fixed diagonal that
    grazes a curved surface tangentially (systematic on cylinders — axles,
    tubes, bolts — not random) registers one hit where it should register
    zero or two, flipping parity and declaring an exterior point interior.
    `disagreement` in the returned dict is True if any probe's three rays
    failed to agree unanimously on any pair checked — the geometry came
    close enough to a surface that the answer should not be fully trusted,
    even where it resolved to "not contained".
    """
    if isinstance(names_or_collection, str):
        names = [o.name for o in
                 bpy.data.collections[names_or_collection].all_objects
                 if o.type == 'MESH']
    else:
        names = list(names_or_collection)

    trees = {n: _bvh(n, margin) for n in names}
    pairs, cap_reached, unverified, disagreement, open_meshes = \
        _check_pairs(trees, margin)
    return {"pairs": pairs, "count": len(pairs), "clean": not pairs,
            "cap_reached": cap_reached, "unverified_parts": unverified,
            "disagreement": disagreement, "open_meshes": open_meshes}


def animated_intersections(moving, others, f0, f1, step=2, margin=0.0):
    """pairwise_intersections swept across an animation range.

    A door clears at rest and eats the B pillar halfway through its travel.
    Checking only the rest pose is checking the one frame that cannot fail.

    `others` are assumed static for the sweep: their BVH+probes+AABB are
    built ONCE, before the frame loop, and reused every frame. Only
    `moving` is rebuilt per frame. See pairwise_intersections for what
    `mode`, `margin`, `cap_reached`, `unverified_parts` and `disagreement`
    mean — unchanged here, just accumulated across every frame checked.
    """
    sc = bpy.context.scene
    saved = sc.frame_current
    static_trees = {n: _bvh(n, margin) for n in others}
    bad, worst_f, cap_reached, disagreement = [], None, False, False
    unverified = set(n for n, (_, probes, _, _) in static_trees.items() if not probes)
    open_meshes = {}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        trees = dict(static_trees)
        trees[moving] = _bvh(moving, margin)
        pairs, cap, unv, dis, opn = _check_pairs(trees, margin)
        cap_reached = cap_reached or cap
        disagreement = disagreement or dis
        unverified.update(unv)
        open_meshes.update(opn)
        for p in pairs:
            if moving in (p["a"], p["b"]):
                bad.append(dict(p, frame=f))
                if worst_f is None:
                    worst_f = f
    sc.frame_set(saved)
    bpy.context.view_layer.update()
    return {"pairs": bad, "worst_frame": worst_f, "clean": not bad,
            "cap_reached": cap_reached, "unverified_parts": sorted(unverified),
            "disagreement": disagreement, "open_meshes": open_meshes}


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

def _png_pixels(path):
    """Read a rendered PNG back into a numpy array WITHOUT PIL.

    PIL does not ship with Blender's bundled Python, so `from PIL import Image`
    makes any function using it unrunnable in a normal Blender session —
    measured as ModuleNotFoundError on a stock Blender 5.2 install whose
    executable came from the Microsoft Store and could not be pip-installed
    into. Blender reads its own renders back through bpy.data.images, so that
    is what this uses.

    This helper exists because the same PIL import was fixed once in
    backdrop_coverage and left behind in silhouette_hp_vs_lp: two copies of the
    same six lines meant one got repaired and its twin stayed broken, unnoticed
    for a whole prop. One reader, both callers.

    Two details that silently corrupt the numbers if skipped:
      * the image is forced to 'Non-Color' before reading, or Blender applies
        the sRGB-to-linear transfer on the way in and the values stop matching
        what PIL returned from the same file;
      * bpy.data.images stores rows BOTTOM-to-top, so the array is flipped to
        the top-to-bottom order the render was framed in. It matters the moment
        you ask *where* in the frame something is, not just how much of it.

    Returns an (h, w, channels) int16 array in 0..255."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = 'Non-Color'
        iw, ih, ch = img.size[0], img.size[1], img.channels
        px = np.empty(iw * ih * ch, dtype=np.float32)
        img.pixels.foreach_get(px)
        return np.flipud((px.reshape(ih, iw, ch) * 255.0).astype(np.int16))
    finally:
        bpy.data.images.remove(img)


def silhouette_hp_vs_lp(col_hp, col_lp, camera, res=(1400, 1800), samples=16,
                        hide=()):
    """Renders both collections with a transparent background and compares the
    alpha channel. It is the only honest measure of whether the low poly holds
    the silhouette.

    NOTE: the backdrop must be hidden, or alpha comes back opaque across the
    whole frame and the comparison reports 0% difference for the wrong reason."""
    import numpy as np
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
    a = _png_pixels(outputs["hp"])[:, :, 3]
    b = _png_pixels(outputs["lp"])[:, :, 3]
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
    like a hole and is not one.

    Reads pixels WITHOUT PIL: `from PIL import Image` made this function
    inejecutable in a normal Blender session — PIL does not ship with
    Blender's Python, and a `blender.exe` installed from the Microsoft Store
    cannot `pip install` into it either (confirmed: ModuleNotFoundError on a
    real user machine). Pixels are read the way Blender already has them in
    memory: `bpy.data.images.load()` on the just-written render, then
    `Image.pixels.foreach_get()` into a numpy array. Output contract (keys,
    thresholds, verdict logic) is unchanged from the PIL version."""
    import numpy as np
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
                p=r.filepath, cam=sc.camera, w=sc.world, f=sc.frame_current,
                fmt=r.image_settings.file_format, cm=r.image_settings.color_mode)
    worst, edges, detail = (0.0, None), [], []
    try:
        sc.world = w; sc.camera = bpy.data.objects[camera]
        r.resolution_x, r.resolution_y = res
        sc.cycles.samples = samples
        r.image_settings.file_format = 'PNG'
        r.image_settings.color_mode = 'RGB'
        for f in range(f0, f1 + 1, step):
            sc.frame_set(f)
            path = os.path.join(tmp, "cov_%04d.png" % f)
            r.filepath = path
            bpy.ops.render.render(write_still=True)
            a = _png_pixels(path)[:, :, :3]
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
        r.image_settings.file_format = prev["fmt"]; r.image_settings.color_mode = prev["cm"]
    return {"worst_pct": round(worst[0], 4), "worst_frame": worst[1],
            "frames_with_world": len(detail),
            "frames_with_world_AT_EDGES": edges or "none",
            "verdict": "BACKDROP INSUFFICIENT" if edges else "backdrop covers"}


def framing_check(camera, collection, f0, f1, step=3, margin=0.02):
    """Projects every vertex and checks that nothing leaves the frame across the
    whole range. A part that unfolds may only leave frame for 10 frames.

    Walks `all_objects`, not `objects`: a collection's `.objects` returns ONLY
    its direct children, silently skipping anything that lives in a
    subcollection. Uncovered on a Corona delivery truck: "Camion" is a parent
    collection whose 108 meshes live entirely inside 6 subcollections and has
    0 objects directly in it. `framing_check(cam, "Camion", ...)` with a
    camera placed INSIDE the truck's cab iterated zero vertices, left every
    sentinel extreme untouched (u_min/v_min stuck at +1e9, u_max/v_max stuck
    at -1e9), and still reported `all_inside: True` — an empty range
    trivially satisfies the inequality. The same camera against the leaf
    collection "Caja_Ext" correctly reported `all_inside: False`. This is
    exactly the failure mode this skill exists to prevent: a check that
    cannot fail.

    Absence of data must never read as success. If no vertex was evaluated
    across the whole range, `all_inside` is forced to `None` (never `True`)
    and `no_geometry_evaluated` is set to `True` — a caller must treat
    `all_inside is not True` as "not proven inside", and `None` specifically
    as "nothing was checked", not as a pass."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = bpy.data.objects[camera]
    saved = sc.frame_current
    ext = {"u_min": 1e9, "v_min": 1e9, "u_max": -1e9, "v_max": -1e9}
    fr = {}
    verts_evaluated = 0
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); dg.update()
        for o in bpy.data.collections[collection].all_objects:
            if o.type not in {'MESH', 'CURVE'}:
                continue
            ev = o.evaluated_get(dg); m = ev.to_mesh()
            for v in m.vertices:
                verts_evaluated += 1
                c = world_to_camera_view(sc, cam, ev.matrix_world @ v.co)
                for k, val in (("u_min", c.x), ("v_min", c.y)):
                    if val < ext[k]:
                        ext[k], fr[k] = val, f
                for k, val in (("u_max", c.x), ("v_max", c.y)):
                    if val > ext[k]:
                        ext[k], fr[k] = val, f
            ev.to_mesh_clear()
    sc.frame_set(saved)
    if verts_evaluated == 0:
        return {"extremes": {k: round(v, 4) for k, v in ext.items()},
                "frames": fr, "all_inside": None,
                "no_geometry_evaluated": True}
    inside = (ext["u_min"] >= margin and ext["v_min"] >= margin
              and ext["u_max"] <= 1 - margin and ext["v_max"] <= 1 - margin)
    return {"extremes": {k: round(v, 4) for k, v in ext.items()},
            "frames": fr, "all_inside": inside,
            "no_geometry_evaluated": False}


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


# ─────────────────────────────────────────────────────── file vs session

def datablocks_on_disk(path, expect_objects=(), expect_meshes=()):
    """Read a .blend ON DISK and report what it actually contains.

    MEASURING THE SESSION IS NOT MEASURING THE FILE. Every other function
    here inspects `bpy.data`, which is the open session. That is the right
    target while modelling and the wrong one the moment a file gets copied,
    handed over, linked, or used as the input to the next stage — because
    an unsaved session and its file on disk are different objects, and
    nothing warns you.

    Measured, and it cost a rebuild: a client's .blend was opened, its mesh
    inspected through `bpy.data` (21,966 verts, 14 loose parts, all
    correct), and the FILE copied to a new working location. The file was
    140,543 bytes and contained no objects at all — the mesh existed only
    in the unsaved session. It reached disk later, when the session was
    closed and saved, by which time the copy had already been made from the
    objectless version. The working file was born empty and it took
    reopening it and querying `bpy.data.objects` to notice.

    Uses `bpy.data.libraries.load` in read-only mode: nothing is imported,
    nothing is linked, the current scene is untouched. Blender cannot load
    from the file it currently has open, so pass a path other than
    `bpy.data.filepath` — to check the current file, save it first and then
    verify the copy you are about to hand off.

    Returns what the file holds plus `missing`, and `ok` is True only when
    every expected name is present.
    """
    import os
    if not os.path.exists(path):
        return {"ok": False, "error": "file does not exist", "path": path}
    if os.path.normcase(os.path.abspath(path)) == \
            os.path.normcase(os.path.abspath(bpy.data.filepath or "")):
        return {"ok": False, "path": path,
                "error": "this is the currently open file; Blender cannot load "
                         "from it. Save, then verify the copy you will hand off."}
    found = {}
    try:
        with bpy.data.libraries.load(path) as (src, _dst):
            for k in ("objects", "meshes", "materials", "images",
                      "collections", "scenes", "actions"):
                found[k] = sorted(getattr(src, k, []) or [])
    except Exception as exc:  # unreadable / not a .blend / wrong version
        return {"ok": False, "error": repr(exc), "path": path}
    missing = {
        "objects": [n for n in expect_objects if n not in found.get("objects", [])],
        "meshes": [n for n in expect_meshes if n not in found.get("meshes", [])],
    }
    return {"ok": not (missing["objects"] or missing["meshes"]),
            "path": path,
            "size_bytes": os.path.getsize(path),
            "counts": {k: len(v) for k, v in found.items()},
            "objects": found.get("objects", []),
            "meshes": found.get("meshes", []),
            "missing": missing}


def texture_files(directory, expect):
    """Checks that every delivered map exists ON DISK, is not 0x0 and has the
    expected resolution. `expect` = {filename: (width, height)}.

    A bake target lives in the session until it is saved. Real case: a shared
    working .blend held twelve bake images (BaseColor, Normal, ORM for four
    props) that reported size 0x0 in `bpy.data.images` -- the datablocks were
    there, the pixels never reached a file. Nothing that inspects the scene
    notices; only reading the file back does.

    Refuses to pass when it evaluated nothing."""
    import os
    missing, zero, wrong = [], [], {}
    for name, size in expect.items():
        path = os.path.join(directory, name)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            missing.append(name)
            continue
        img = bpy.data.images.load(path, check_existing=False)
        got = (img.size[0], img.size[1])
        bpy.data.images.remove(img)
        if 0 in got:
            zero.append(name)
        elif got != tuple(size):
            wrong[name] = got
    return {"ok": bool(expect) and not (missing or zero or wrong), "evaluated": len(expect),
            "missing": missing, "zero_sized": zero, "wrong_size": wrong}


def fbx_roundtrip(path, expect_tris, expect_uv_layers=1, expect_materials=None,
                  expect_dims_mm=None, tol_mm=0.5):
    """Re-imports an exported FBX into a throwaway scene and compares it with
    what was meant to be exported: triangle count, UV layer count, material
    names and overall dimensions. Everything else in this file measures the
    session; the client receives the FBX.

    `expect_tris` and `expect_dims_mm` are for the whole exported set. The
    imported objects and the temporary scene are removed before returning."""
    import os
    if not os.path.exists(path):
        return {"ok": False, "error": "file does not exist", "path": path}
    previous = bpy.context.window.scene
    tmp = bpy.data.scenes.new("_fbx_check")
    bpy.context.window.scene = tmp
    before = set(bpy.data.objects)
    diffs = {}
    try:
        bpy.ops.import_scene.fbx(filepath=path)
        meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
        bpy.context.view_layer.update()
        tris, lo, hi, uvs, mats = 0, [1e9] * 3, [-1e9] * 3, set(), set()
        for o in meshes:
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
            uvs.add(len(o.data.uv_layers))
            mats |= {s.material.name.split(".")[0] for s in o.material_slots if s.material}
            for v in o.data.vertices:
                p = o.matrix_world @ v.co
                for i in range(3):
                    lo[i] = min(lo[i], p[i])
                    hi[i] = max(hi[i], p[i])
        dims = [round((hi[i] - lo[i]) * 1000, 2) for i in range(3)] if meshes else None
        if tris != expect_tris:
            diffs["tris"] = (tris, expect_tris)
        if uvs != {expect_uv_layers}:
            diffs["uv_layers"] = (sorted(uvs), expect_uv_layers)
        if expect_materials is not None and mats != set(expect_materials):
            diffs["materials"] = (sorted(mats), sorted(expect_materials))
        if expect_dims_mm is not None and (
                dims is None or any(abs(a - b) > tol_mm for a, b in zip(dims, expect_dims_mm))):
            diffs["dims_mm"] = (dims, list(expect_dims_mm))
        result = {"ok": bool(meshes) and not diffs, "evaluated": len(meshes), "tris": tris,
                  "uv_layers": sorted(uvs), "materials": sorted(mats), "dims_mm": dims,
                  "diffs": diffs}
    finally:
        for o in [o for o in bpy.data.objects if o not in before]:
            d = o.data
            bpy.data.objects.remove(o)
            if d and d.users == 0 and isinstance(d, bpy.types.Mesh):
                bpy.data.meshes.remove(d)
        bpy.context.window.scene = previous
        bpy.data.scenes.remove(tmp)
    return result


def bake_fidelity(col_hp, col_lp, camera, out_dir, res=(1024, 1024), samples=48, hide=()):
    """Renders the HP and the baked LP from the same camera under the same
    lights and returns their mean and 99th-percentile difference in 0-255
    levels, over the pixels either of them covers. Threshold: mean < 2.

    This is the gate the table always listed ("compare LP+normal render
    against HP") without a function behind it. Measured on a hard hat: 1.25
    mean, 21 at p99 -- the p99 sits on the silhouette, where an 11k-triangle
    LP and a 574k-face HP legitimately differ by a pixel.

    Collections are passed by name; `hide` lists objects to keep out of both
    renders (backdrop, display stand). Render visibility is restored."""
    import os
    import numpy as np
    sc = bpy.context.scene
    state = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples,
             sc.render.filepath, sc.render.film_transparent,
             {o.name: o.hide_render for o in bpy.data.objects},
             sc.render.image_settings.file_format, sc.render.image_settings.color_mode)
    hp = {o.name for o in bpy.data.collections[col_hp].all_objects}
    lp = {o.name for o in bpy.data.collections[col_lp].all_objects}
    px = {}
    try:
        sc.camera = bpy.data.objects[camera]
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.cycles.samples = samples
        sc.render.film_transparent = True
        # the coverage mask IS the alpha channel: a scene left on RGB output writes
        # no alpha, every pixel reads as covered and the background dilutes the
        # mean. Measured: 0.383 over 1,048,576 px instead of 1.251 over 284,618.
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA"
        for tag, show, conceal in (("hp", hp, lp), ("lp", lp, hp)):
            for n in show:
                bpy.data.objects[n].hide_render = False
            for n in set(conceal) | set(hide):
                bpy.data.objects[n].hide_render = True
            path = os.path.join(out_dir, "_fidelity_%s.png" % tag)
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(path, check_existing=False)
            a = np.empty(res[0] * res[1] * 4, dtype=np.float32)
            img.pixels.foreach_get(a)
            bpy.data.images.remove(img)
            px[tag] = a.reshape(res[1], res[0], 4)
    finally:
        sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = state[:4]
        sc.render.filepath, sc.render.film_transparent = state[4], state[5]
        sc.render.image_settings.file_format, sc.render.image_settings.color_mode = state[7], state[8]
        for n, h in state[6].items():
            if n in bpy.data.objects:
                bpy.data.objects[n].hide_render = h
    covered = (px["hp"][..., 3] > 0.5) | (px["lp"][..., 3] > 0.5)
    if not covered.any():
        return {"ok": False, "evaluated": 0}
    full = np.abs(px["hp"][..., :3] - px["lp"][..., :3]).mean(-1) * 255
    d = full[covered]
    mean = float(d.mean())
    # Where does the difference live? `mean_smooth_255` is the mean over pixels
    # that are inside BOTH silhouettes (eroded 3 px) and where the HP render
    # itself is smooth: that is what the normal map is responsible for. The
    # rest is contours, where a rounded HP edge and a hard LP edge land one
    # pixel apart. Measured on a gate valve: 2.64 total, 0.93 smooth, 1.76 of
    # the 2.64 on internal edges. `ok` is NOT changed by this breakdown: it
    # tells you what to fix, it does not move the threshold.
    both = (px["hp"][..., 3] > 0.5) & (px["lp"][..., 3] > 0.5)
    for _ in range(3):
        both = both & np.roll(both, 1, 0) & np.roll(both, -1, 0) & np.roll(both, 1, 1) & np.roll(both, -1, 1)
    lum = px["hp"][..., :3].mean(-1)
    grad = np.abs(np.roll(lum, 1, 0) - lum) + np.abs(np.roll(lum, 1, 1) - lum)
    smooth = both & (grad < 0.02)
    return {"ok": mean < 2.0, "evaluated": int(covered.sum()), "mean_diff_255": round(mean, 3),
            "p99_diff_255": round(float(np.percentile(d, 99)), 2),
            "max_diff_255": round(float(d.max()), 1),
            "mean_smooth_255": round(float(full[smooth].mean()), 3) if smooth.any() else None,
            "smooth_px": int(smooth.sum())}


def surface_distance(a, b, near_mm=1.0):
    """Minimum distance (mm) from the vertices of `a` to the surface of `b`,
    plus how many of those vertices sit BEHIND the nearest face of `b`.

    The independent measurement that settles a `disagreement: True` from
    pairwise_intersections. Real case: one of two mirror-identical wire forks
    raised `disagreement` against a shell and its twin did not; this returned
    0.2 mm (the designed seating gap) on both sides with zero vertices behind
    -- a ray grazing a flat face 0.2 mm away, not a contained part.

    The sign is only counted within `near_mm` of the surface. Far from it the
    nearest face can simply be facing the other way: counted over all
    vertices, the same two forks reported 691 "inside" each."""
    from mathutils.bvhtree import BVHTree
    ob = bpy.data.objects[b]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    tree = BVHTree.FromBMesh(bm)
    oa = bpy.data.objects[a]
    best, behind = None, 0
    for v in oa.data.vertices:
        p = oa.matrix_world @ v.co
        loc, nor, _, dist = tree.find_nearest(p)
        if (p - loc).dot(nor) < 0 and dist * 1000 < near_mm:
            behind += 1
        if best is None or dist < best:
            best = dist
    bm.free()
    if best is None:
        return {"ok": False, "evaluated": 0}
    return {"ok": behind == 0, "evaluated": len(oa.data.vertices),
            "min_mm": round(best * 1000, 3), "vertices_behind": behind}


def light_leaks(names, point, allowed=(), n=4000):
    """Leak test for a cavity. Casts `n` rays from `point` (inside the cavity)
    in every direction against the joined set `names`; a ray that hits nothing
    escaped through an opening. `allowed` = [(direction, half_angle_deg), ...]
    lists the openings that are SUPPOSED to exist (the two ports of a valve).

    Real case: the internal chamber cut into a valve bonnet broke through the
    wall of the dome where the dome narrows. The part was still watertight
    (the hole had walls), had no degenerate faces and crossed nothing; a
    render showed a black slot in the casting. On that bonnet this returns 41
    escaping rays; on the corrected one, 0.

    Choose `point` in the EMPTY space of the cavity. The first version of the
    probe sat on the stem axis, inside the stem: every ray hit the stem and
    the gate reported 0 escapes on the defective part. Validate the probe on
    a known-bad case, or at least confirm `allowed=()` reports escapes through
    the openings you know are there."""
    import math
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for name in names:
        ob = bpy.data.objects[name]
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        tmp.transform(ob.matrix_world)
        me = bpy.data.meshes.new("_leak")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    p = Vector(point)
    cones = [(Vector(d).normalized(), math.cos(math.radians(a))) for d, a in allowed]
    escapes, total = 0, Vector()
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        d = Vector((r * math.cos(golden * i), r * math.sin(golden * i), z))
        if tree.ray_cast(p, d)[0] is None and not any(d.dot(c) >= cosine for c, cosine in cones):
            escapes += 1
            total += d
    return {"ok": bool(names) and escapes == 0, "evaluated": n, "escapes": escapes,
            "mean_direction": [round(v, 2) for v in (total / escapes)] if escapes else None}


def collection_fingerprint(collection):
    """{object name: (vertices, faces)} for every mesh in `collection`,
    recursively. Take it of the HIGH POLY before building the low poly and
    compare afterwards with `fingerprint_unchanged`."""
    return {o.name: (len(o.data.vertices), len(o.data.polygons))
            for o in bpy.data.collections[collection].all_objects if o.type == "MESH"}


def fingerprint_unchanged(collection, before):
    """Nothing done to the low poly may touch the high poly.

    Real case: a mesh helper reused an existing object when one with the
    requested name already existed. Building the low poly asked for parts
    named like the high poly's nuts, washers, gaskets and seats; the helper
    replaced THEIR meshes with low-poly ones and the join step swept them
    into the LP object. The high poly went from 31 parts to 13 with no error
    anywhere. It surfaced only as a 1.4 % silhouette failure, traced with a
    difference image to nuts missing from the HP pass."""
    now = collection_fingerprint(collection)
    missing = sorted(set(before) - set(now))
    added = sorted(set(now) - set(before))
    changed = sorted(n for n in before if n in now and before[n] != now[n])
    return {"ok": bool(before) and not (missing or added or changed), "evaluated": len(before),
            "missing": missing, "added": added, "changed": changed}


def decals_visible(decals, carrier, axis="Y", side=None):
    """Every vertex of every decal must lie IN FRONT of its carrier, seen from
    outside along `axis`. For each vertex a ray is cast from outside toward
    the carrier; if the carrier is hit before the ray reaches the decal, that
    vertex is buried. The side each vertex is viewed from is the sign of its
    own coordinate on `axis` (front decals at -Y, back decals at +Y), unless
    `side` (-1 or +1) forces it for all of them.

    `side` exists because the sign rule is wrong for any face that is not on
    the outer side of the origin: a lamp housing with its FRONT face at
    y = +20 mm was reported as 448 of 448 vertices buried while the render
    showed the text perfectly.

    Real case: legends laid out on a recessed instrument panel. The flat was
    narrower than its cutter — a lip of the housing started 4.5 mm inside the
    nominal edge — and "HOLD" rendered as "OLD", "V=" as "/=". The text did
    not float (a seating check passes) and did not cross (an intersection
    check passes on an open mesh that it skips anyway): it was underneath.

    Returns {decal: (buried, total)} for the ones with buried vertices."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    i = "XYZ".index(axis)
    ob = bpy.data.objects[carrier]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    forced = None if side is None else (1.0 if side > 0 else -1.0)
    buried, evaluated = {}, 0
    for name in decals:
        d = bpy.data.objects[name]
        n = 0
        for v in d.data.vertices:
            p = d.matrix_world @ v.co
            s = forced if forced is not None else (-1.0 if p[i] < 0 else 1.0)
            origin = Vector(p)
            origin[i] = s * 10.0
            direction = Vector((0, 0, 0))
            direction[i] = -s
            hit = tree.ray_cast(origin, direction)
            if hit[0] is not None and (hit[0][i] - p[i]) * s > 1e-5:
                n += 1
        evaluated += len(d.data.vertices)
        if n:
            buried[name] = (n, len(d.data.vertices))
    return {"ok": evaluated > 0 and not buried, "evaluated": evaluated, "buried": buried}
