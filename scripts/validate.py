#!/usr/bin/env python3
"""Deterministic structural linter for .drawio files.

Catches the class of mistakes a vision self-check is slow and unreliable at:
dangling edge endpoints, duplicate or reserved ids, broken parent references,
and (as warnings) off-grid geometry, overlapping sibling nodes, and edge
routing defects. Runs without launching draw.io, so it is a fast pre-check
before the visual review step.

  python3 validate.py diagram.drawio

Edge routing checks (warnings): an edge segment crossing a non-incident leaf
vertex ("routes through vertex"), and two edges crossing each other ("edges X
and Y cross") — the two defects the SKILL.md step-5 self-check looks for
("Edge-shape overlap", "Stacked edges"), but caught here deterministically.

Routing is only knowable from the XML when an edge carries explicit waypoints
(``<Array as="points">``) — exactly the hand-routed case the SKILL.md tells
authors to use to route around shapes. Edges with no waypoints are auto-routed
by draw.io at render time (the path is not stored), so they are NOT geometry-
checked here, keeping these warnings free of false positives. Endpoints honour
``exitX/exitY``/``entryX/entryY`` when present, else the node centre, and
absolute positions are resolved through parent containers.

Exit status is non-zero when any error (or, with --strict, any warning) is
found, so it can gate a workflow. Compressed (non-XML) diagram pages are
skipped with a warning — this skill always writes uncompressed XML.

Usage: python3 validate.py <file.drawio> [--strict]
"""
import argparse
import sys
import xml.etree.ElementTree as ET

RESERVED = {"0", "1"}
CLI_RESERVED = {"join"}  # draw.io v30.x CLI silently fails export with these ids


def rect(cell):
    """Return (x, y, w, h) floats for a cell's geometry, or None if absent/bad.

    x/y default to 0 when omitted: draw.io treats a missing position as the
    origin, and container-managed children (table rows, swimlane/UML-class
    lines under tableLayout) legitimately omit x/y while keeping width/height.
    Only width/height are required to be present and numeric.
    """
    g = cell.find("mxGeometry")
    if g is None:
        return None
    try:
        return (float(g.get("x", "0")), float(g.get("y", "0")),
                float(g.get("width", "nan")), float(g.get("height", "nan")))
    except ValueError:
        return None


def is_edge_label(cell):
    """True for a draw.io edge label / relative-positioned child vertex.

    These legitimately omit width/height: their position is given relative to a
    parent edge (style ``edgeLabel``) or via ``relative="1"`` geometry. Treating
    them as normal vertices wrongly flags them as missing/invalid geometry.
    """
    if "edgeLabel" in (cell.get("style") or ""):
        return True
    g = cell.find("mxGeometry")
    return g is not None and g.get("relative") == "1"


def overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


# --- Edge routing geometry -------------------------------------------------
#
# These helpers reason about edge paths. They only apply to edges with explicit
# waypoints (the route is otherwise computed by draw.io at render time and not
# stored in the XML), so the checks never guess an auto-routed path.

def style_num(style, key):
    """Return float value of ``key=`` in a draw.io style string, or None."""
    for part in (style or "").split(";"):
        if part.startswith(key + "="):
            try:
                return float(part.split("=", 1)[1])
            except ValueError:
                return None
    return None


def abs_rect(cell, by_id):
    """Absolute (x, y, w, h) of a vertex, summing parent-container offsets.

    Children of a container use coordinates relative to the container origin, so
    an edge spanning containers needs absolute positions to be compared.
    """
    r = rect(cell)
    if r is None or any(v != v for v in r):
        return None
    x, y, w, h = r
    parent, seen = cell.get("parent"), set()
    while parent and parent in by_id and parent not in seen:
        seen.add(parent)
        p = by_id[parent]
        if p.get("vertex") == "1":
            pr = rect(p)
            if pr and not any(v != v for v in pr):
                x += pr[0]
                y += pr[1]
        parent = p.get("parent")
    return (x, y, w, h)


def endpoint(edge, end, by_id):
    """Absolute (x, y) where ``edge`` meets its source/target vertex.

    Honours exitX/exitY (source) and entryX/entryY (target) if the style pins
    them; otherwise the vertex centre. Returns None if the vertex is unresolved.
    """
    vid = edge.get(end)
    if not vid or vid not in by_id:
        return None
    box = abs_rect(by_id[vid], by_id)
    if box is None:
        return None
    x, y, w, h = box
    style = edge.get("style") or ""
    fx = style_num(style, "exitX" if end == "source" else "entryX")
    fy = style_num(style, "exitY" if end == "source" else "entryY")
    return (x + (fx if fx is not None else 0.5) * w,
            y + (fy if fy is not None else 0.5) * h)


def edge_waypoints(edge):
    """Explicit <Array as="points"> waypoints of an edge as [(x, y), ...]."""
    g = edge.find("mxGeometry")
    if g is None:
        return []
    arr = g.find("Array")
    if arr is None:
        return []
    pts = []
    for pt in arr.findall("mxPoint"):
        px, py = pt.get("x"), pt.get("y")
        if px is not None and py is not None:
            try:
                pts.append((float(px), float(py)))
            except ValueError:
                pass
    return pts


def edge_route(edge, by_id):
    """Absolute polyline [(x, y), ...] for a waypointed edge, or None.

    Returns None when the edge has no explicit waypoints (auto-routed; path
    unknown) or an endpoint cannot be resolved.
    """
    waypoints = edge_waypoints(edge)
    if not waypoints:
        return None
    s, t = endpoint(edge, "source", by_id), endpoint(edge, "target", by_id)
    if s is None or t is None:
        return None
    return [s] + waypoints + [t]


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)


def segments_cross(p1, p2, p3, p4):
    """True if segments p1p2 and p3p4 properly cross (interior intersection).

    Proper crossing only: collinear overlap and shared-endpoint touches return
    False, so edges meeting at a common node or grazing a corner are not flagged.
    """
    o1, o2 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    o3, o4 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    return o1 != o2 and o3 != o4 and 0 not in (o1, o2, o3, o4)


def _point_in_rect(p, box, eps=1e-6):
    x, y, w, h = box
    return x + eps < p[0] < x + w - eps and y + eps < p[1] < y + h - eps


def route_hits_rect(points, box):
    """True if a polyline enters a rectangle's interior or crosses a border."""
    x, y, w, h = box
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    borders = list(zip(corners, corners[1:] + corners[:1]))
    for a, b in zip(points, points[1:]):
        if _point_in_rect(a, box) or _point_in_rect(b, box):
            return True
        if any(segments_cross(a, b, c, d) for c, d in borders):
            return True
    return False


def routes_cross(pa, pb):
    """True if any segment of polyline pa properly crosses any of pb."""
    for a1, a2 in zip(pa, pa[1:]):
        for b1, b2 in zip(pb, pb[1:]):
            if segments_cross(a1, a2, b1, b2):
                return True
    return False


def visual_warnings(cells, ids):
    """Comprehensive visual quality checks beyond structural correctness.

    Catches: dogleg bends, rhombus+orthogonal jogs, short arrowhead stubs,
    long-distance routing, and extreme aspect ratios.
    """
    DOGLEG_THRESHOLD = 3     # px — below this draw.io snaps to straight
    STUB_MIN = 20            # px — minimum last-segment length for arrowhead
    LONG_ROUTE_RATIO = 0.7   # edge path > 70% of canvas diagonal
    ASPECT_MAX = 3.5         # canvas height/width ratio
    warns = []

    # --- Collect canvas bounds ---
    all_rects = []
    for c in cells:
        if c.get("vertex") == "1":
            r = abs_rect(c, {ci.get("id"): ci for ci in cells})
            if r:
                all_rects.append(r)
    if all_rects:
        min_x = min(r[0] for r in all_rects)
        min_y = min(r[1] for r in all_rects)
        max_x = max(r[0] + r[2] for r in all_rects)
        max_y = max(r[1] + r[3] for r in all_rects)
        canvas_w = max_x - min_x
        canvas_h = max_y - min_y
        canvas_diag = (canvas_w**2 + canvas_h**2) ** 0.5
        if canvas_w > 0 and canvas_h / canvas_w > ASPECT_MAX:
            warns.append(
                f"aspect ratio {canvas_h/canvas_w:.1f}:1 exceeds {ASPECT_MAX}:1 "
                f"(diagram too tall/narrow, consider wider layout)")
    else:
        canvas_diag = 0

    for c in cells:
        if c.get("edge") != "1":
            continue
        style = c.get("style") or ""
        eid = c.get("id")
        s = endpoint(c, "source", {ci.get("id"): ci for ci in cells})
        t = endpoint(c, "target", {ci.get("id"): ci for ci in cells})
        if s is None or t is None:
            continue
        sx, sy = s
        tx, ty = t
        ey = style_num(style, "exitY")
        ex = style_num(style, "exitX")
        ny = style_num(style, "entryY")
        nx = style_num(style, "entryX")
        waypoints = edge_waypoints(c)

        # --- 1. Dogleg: auto-routed edges (no waypoints) ---
        if not waypoints:
            # Any vertical connection: exit bottom → entry top
            if ey == 1.0 and ny == 0.0 and abs(sx - tx) > DOGLEG_THRESHOLD:
                warns.append(
                    f"edge {eid!r} dogleg: exit_x={sx:.0f} vs entry_x={tx:.0f} "
                    f"(diff={abs(sx-tx):.0f}px)")
            # Horizontal: exit right → entry left, only flag very small y-diffs (larger = intentional spread)
            if ex == 1.0 and nx == 0.0 and DOGLEG_THRESHOLD < abs(sy - ty) < 15:
                warns.append(
                    f"edge {eid!r} dogleg: exit_y={sy:.0f} vs entry_y={ty:.0f} "
                    f"(diff={abs(sy-ty):.0f}px)")
            # Auto-routed without explicit exit/entry pins — check if source/target
            # centers are roughly aligned (both vertically adjacent)
            if ey is None and ny is None and ex is None and nx is None:
                if abs(sy - ty) > 20 and abs(sx - tx) > DOGLEG_THRESHOLD:
                    warns.append(
                        f"edge {eid!r} likely dogleg: source_x={sx:.0f} vs target_x={tx:.0f} "
                        f"(diff={abs(sx-tx):.0f}px, add exitX/entryX to align)")

        # --- 2. Dogleg: waypointed edges (consecutive near-parallel segments) ---
        if waypoints:
            pts = [s] + waypoints + [t]
            for i in range(len(pts) - 2):
                a, b, c_pt = pts[i], pts[i+1], pts[i+2]
                seg_len = ((b[0]-a[0])**2 + (b[1]-a[1])**2) ** 0.5
                # Short segment between two longer segments = dogleg
                if seg_len > 0 and seg_len < 15:
                    warns.append(
                        f"edge {eid!r} short waypoint segment ({seg_len:.0f}px) "
                        f"at point {i+1} — likely dogleg")

        # --- 3. Rhombus + orthogonalEdgeStyle horizontal exit ---
        if "orthogonal" in style:
            src_id = c.get("source")
            if src_id and src_id in {ci.get("id") for ci in cells}:
                src_cell = next((ci for ci in cells if ci.get("id") == src_id), None)
                if src_cell is not None:
                    src_style = src_cell.get("style") or ""
                    if "rhombus" in src_style and (ex == 1.0 or ex == 0.0):
                        warns.append(
                            f"edge {eid!r} exits rhombus horizontally with "
                            f"orthogonalEdgeStyle — causes visible jog at diamond "
                            f"edge (remove edgeStyle=orthogonalEdgeStyle)")

        # --- 4. Short arrowhead stub ---
        if waypoints:
            last_wp = waypoints[-1]
            stub = ((last_wp[0]-tx)**2 + (last_wp[1]-ty)**2) ** 0.5
            if stub < STUB_MIN:
                warns.append(
                    f"edge {eid!r} short arrowhead stub ({stub:.0f}px < {STUB_MIN}px) "
                    f"— arrowhead sits on bend")

        # --- 5. Long-distance routing ---
        if waypoints and canvas_diag > 0:
            pts = [s] + waypoints + [t]
            total = sum(((pts[i+1][0]-pts[i][0])**2 +
                         (pts[i+1][1]-pts[i][1])**2)**0.5
                        for i in range(len(pts)-1))
            ratio = total / canvas_diag
            if ratio > LONG_ROUTE_RATIO:
                warns.append(
                    f"edge {eid!r} long route ({total:.0f}px, "
                    f"{ratio:.0%} of canvas diagonal)")

    # --- 6. Fragile table row patterns ---
    for c in cells:
        if c.get("vertex") != "1":
            continue
        style = c.get("style") or ""
        cid = c.get("id") or ""
        value = c.get("value") or ""
        if "tableRow" in style and "horizontal=0" in style and "html=1" in style:
            if "<b>" in value or "<span" in value or "<br" in value:
                warns.append(
                    f"vertex {cid!r} uses tableRow+horizontal=0+html=1 with HTML tags "
                    f"in value — known to cause garbled text rendering on export. "
                    f"Use plain text values instead")

    # --- 7. Text overflow in vertices ---
    import re
    def _plain_text_len(value):
        """Estimate visible character count from a value (strip HTML tags)."""
        if not value:
            return 0
        text = re.sub(r'<[^>]+>', '', value)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&#xa;', '\n').replace('&#10;', '\n')
        longest_line = max((len(line) for line in text.split('\n')), default=0)
        return longest_line

    for c in cells:
        if c.get("vertex") != "1":
            continue
        r = rect(c)
        if r is None:
            continue
        _, _, w, h = r
        value = c.get("value") or ""
        style = c.get("style") or ""
        text_len = _plain_text_len(value)
        if text_len == 0:
            continue
        if "verticalLabelPosition" in style or "labelPosition" in style:
            continue
        font_size = style_num(style, "fontSize") or 12
        has_spacingLeft = style_num(style, "spacingLeft") or 0
        estimated_text_width = text_len * font_size * 0.65 + has_spacingLeft
        if w > 0 and estimated_text_width > w:
            warns.append(
                f"vertex {c.get('id')!r} text likely overflows: "
                f"~{estimated_text_width:.0f}px text in {w:.0f}px wide box "
                f"(widen to {int(estimated_text_width) + 20}px)")
        if "overflow=hidden" in style and text_len > 0:
            warns.append(
                f"vertex {c.get('id')!r} has overflow=hidden — "
                f"text will be clipped instead of wrapping. Remove overflow=hidden")

    # --- 8. Parallel edge proximity ---
    PARALLEL_MIN = 20  # px — minimum distance between parallel edge segments
    by_id_map = {ci.get("id"): ci for ci in cells}
    edge_segments = []
    for c in cells:
        if c.get("edge") != "1":
            continue
        eid = c.get("id")
        s = endpoint(c, "source", by_id_map)
        t = endpoint(c, "target", by_id_map)
        if s is None or t is None:
            continue
        wps = edge_waypoints(c)
        pts = [s] + wps + [t]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            seg_len = (dx*dx + dy*dy) ** 0.5
            if seg_len > 30:
                edge_segments.append((eid, a, b, seg_len))
    for i in range(len(edge_segments)):
        for j in range(i + 1, len(edge_segments)):
            eid_a, a1, a2, la = edge_segments[i]
            eid_b, b1, b2, lb = edge_segments[j]
            if eid_a == eid_b:
                continue
            da = (a2[0] - a1[0], a2[1] - a1[1])
            db = (b2[0] - b1[0], b2[1] - b1[1])
            cross = da[0] * db[1] - da[1] * db[0]
            if abs(cross) > la * lb * 0.1:
                continue
            mid_a = ((a1[0]+a2[0])/2, (a1[1]+a2[1])/2)
            mid_b = ((b1[0]+b2[0])/2, (b1[1]+b2[1])/2)
            dist = ((mid_a[0]-mid_b[0])**2 + (mid_a[1]-mid_b[1])**2) ** 0.5
            if dist < PARALLEL_MIN and min(la, lb) > 50:
                warns.append(
                    f"edges {eid_a!r} and {eid_b!r} run parallel within "
                    f"{dist:.0f}px — hard to distinguish (space ≥{PARALLEL_MIN}px apart)")
                break
        else:
            continue
        break

    return warns


def geometry_warnings(cells, ids, parents):
    """Edge-through-vertex and edge-crossing warnings for waypointed edges."""
    warns = []
    routed = []          # (edge_id, polyline, {source, target})
    for c in cells:
        if c.get("edge") == "1":
            style = c.get("style") or ""
            if "curved=1" in style:
                continue
            pts = edge_route(c, ids)
            if pts:
                routed.append((c.get("id"), pts,
                               {c.get("source"), c.get("target")}))
    # Edge routes through an unrelated leaf vertex (containers wrap children, so
    # an edge legitimately traverses them — restrict to leaves, as overlap does).
    leaves = [(c.get("id"), abs_rect(c, ids)) for c in cells
              if c.get("vertex") == "1" and c.get("id") not in parents
              and not is_edge_label(c)]
    leaves = [(vid, box) for vid, box in leaves if box]
    for eid, pts, ends in routed:
        for vid, box in leaves:
            if vid not in ends and route_hits_rect(pts, box):
                warns.append(f"edge {eid!r} routes through vertex {vid!r}")
    # Edge-edge crossings (both routes known).
    for i in range(len(routed)):
        for j in range(i + 1, len(routed)):
            (ia, pa, _), (ib, pb, _) = routed[i], routed[j]
            if routes_cross(pa, pb):
                warns.append(f"edges {ia!r} and {ib!r} cross")
    return warns


def check_page(diagram):
    """Return (errors, warnings) for one <diagram> page."""
    name = diagram.get("name", "?")
    model = diagram.find("mxGraphModel")
    if model is None:
        if (diagram.text or "").strip():
            return [], [f"page {name!r}: compressed, skipped (cannot lint)"]
        return [f"page {name!r}: no <mxGraphModel>"], []
    root = model.find("root")
    cells = root.findall("mxCell") if root is not None else []
    errors, warns = [], []
    ids = {}
    for c in cells:
        cid = c.get("id")
        if cid in ids:
            errors.append(f"duplicate id {cid!r}")
        ids[cid] = c
    parents = {c.get("parent") for c in cells}            # ids that have children
    for c in cells:
        cid, parent = c.get("id"), c.get("parent")
        is_v, is_e = c.get("vertex") == "1", c.get("edge") == "1"
        if parent is not None and parent not in ids:
            errors.append(f"cell {cid!r} parent {parent!r} does not exist")
        for end in ("source", "target"):
            ref = c.get(end)
            if ref and ref not in ids:
                errors.append(f"edge {cid!r} {end} {ref!r} does not exist")
        if (is_v or is_e) and cid in RESERVED:
            errors.append(f"cell {cid!r} reuses reserved id 0/1")
        if (is_v or is_e) and cid in CLI_RESERVED:
            errors.append(f"cell {cid!r} uses CLI-reserved id {cid!r} — draw.io export will silently fail. Rename it")
        if is_v and not is_edge_label(c):
            r = rect(c)
            if r is None or any(v != v for v in r):       # None or NaN
                errors.append(f"vertex {cid!r} has missing/invalid geometry")
            else:
                x, y, w, h = r
                if w <= 0 or h <= 0:
                    warns.append(f"vertex {cid!r} non-positive size {w:g}x{h:g}")
                if x < 0 or y < 0:
                    warns.append(f"vertex {cid!r} negative position ({x:g},{y:g})")
    # Sibling overlap: only leaf vertices (containers legitimately wrap children).
    # Skip UML shapes that by-design overlap (umlFrame covers umlLifeline, etc.)
    UML_OVERLAP_OK = {"umlFrame", "umlLifeline", "umlBoundary", "umlEntity", "umlControl"}
    def _is_uml_or_end_pair(ca, cb):
        sa, sb = (ca.get("style") or ""), (cb.get("style") or "")
        if any(k in sa or k in sb for k in UML_OVERLAP_OK):
            return True
        ia, ib = ca.get("id") or "", cb.get("id") or ""
        if "ellipse" in sa and "ellipse" in sb:
            import re
            def _end_stem(x):
                return re.sub(r'[_-]?(outer|inner|o|b)$', '', x)
            if _end_stem(ia) == _end_stem(ib) and _end_stem(ia) != "":
                return True
            if ia.startswith(ib) or ib.startswith(ia):
                return True
        return False
    boxes = [(c.get("id"), c.get("parent"), rect(c), c) for c in cells
             if c.get("vertex") == "1" and c.get("id") not in parents and rect(c)
             and not any(v != v for v in rect(c))]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (ia, pa, ra, ca), (ib, pb, rb, cb) = boxes[i], boxes[j]
            if pa == pb and overlap(ra, rb):
                if _is_uml_or_end_pair(ca, cb):
                    continue
                warns.append(f"vertices {ia!r} and {ib!r} overlap")
    warns += geometry_warnings(cells, ids, parents)
    warns += visual_warnings(cells, ids)
    # --- Content completeness checks ---
    all_values = [c.get("value") or "" for c in cells]
    all_styles = [(c.get("style") or "") for c in cells if c.get("vertex") == "1"]
    # Legend check: at least one element with "图例" or "legend" in value or id
    has_legend = any("图例" in v.lower() or "legend" in v.lower()
                     for v in all_values)
    has_legend = has_legend or any("图例" in (c.get("id") or "") or "legend" in (c.get("id") or "")
                                   for c in cells)
    if not has_legend:
        warns.append("no legend found — add a 图例/legend box explaining colors and symbols")
    # Color variety: count distinct fillColors among vertices
    fill_colors = set()
    for s in all_styles:
        for part in s.split(";"):
            if part.startswith("fillColor=") and "none" not in part:
                fill_colors.add(part.split("=", 1)[1].lower())
    if len(fill_colors) < 3 and len([c for c in cells if c.get("vertex") == "1"]) > 5:
        warns.append(
            f"only {len(fill_colors)} fill color(s) used across {len(all_styles)} vertices "
            f"— use color-coding by functional domain (see pitfalls §10.6)")
    return errors, warns


def main():
    ap = argparse.ArgumentParser(description="Lint a .drawio file for structural errors.")
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failure too")
    args = ap.parse_args()
    try:
        tree = ET.parse(args.file)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {args.file}: {exc}")
    pages = tree.getroot().findall("diagram") or [tree.getroot()]
    errors, warns = [], []
    for page in pages:
        e, w = check_page(page)
        errors += e
        warns += w
    for w in warns:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    if errors or (args.strict and warns):
        sys.exit(1)


if __name__ == "__main__":
    main()
