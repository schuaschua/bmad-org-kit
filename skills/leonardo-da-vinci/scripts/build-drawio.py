#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Validate a cited diagram model and render it as a stamped .drawio file (plus PNG/SVG).

Reads `<folder>/<name>.model.json` and writes `<folder>/<name>.drawio` beside it, then
`<name>.png` and `<name>.svg` when draw.io desktop is installed (or DRAWIO_CLI names it).
Nothing is drawn unless the whole model validates; every problem is reported at once so it
can be fixed in the model:

- `spine` must be an ARCHITECTURE-SPINE.md under _bmad-output/planning-artifacts/architecture/,
  and every other `sources` entry must be a file under _bmad-output/ (spec and UX docs)
- every node, group, edge, participant and message needs a `cite`: an AD id the spine
  defines (`AD-4`), or a reference starting with a source's file name (`SPEC.md §3.2`)
- ids are unique, edges join existing nodes, kinds suit the diagram type, data tags are PII/PHI

Model (`cite` is a string or a list of strings):

    {
      "type": "c4-context | c4-containers | deployment | data-flow | sequence",
      "title": "Chat service",
      "spine": "_bmad-output/planning-artifacts/architecture/<name>/ARCHITECTURE-SPINE.md",
      "sources": ["_bmad-output/specs/SPEC.md"],
      "direction": "TB | LR",                   optional; data-flow defaults to LR, others TB
      "page": {"size": "A4 | A3 | Letter", "orientation": "portrait | landscape"},   default A4 portrait
      "provider": "azure",                      deployment only; the stencil catalogue for `icon` (default azure)
      "groups": [{"id", "label", "kind", "parent"?, "icon"?, "cite"}],
      "nodes":  [{"id", "label", "kind", "group"?, "tech"?, "description"?, "data"?: ["PII", "PHI"],
                  "icon"?: "stencil id (stencils.py search): the provider's (app_services/App_Services) or library:id (kubernetes:pod)",
                  "style"?: "raw draw.io style, only for a shape no catalogue holds",
                  "layer"?: 0, "cite"}],
      "edges":  [{"from", "to", "label", "tech"?, "data"?, "dashed"?: true, "cite"}],
      "participants": [{"id", "label", "kind", "cite"}],          sequence only
      "messages": [{"from", "to", "label", "return"?: true, "data"?, "cite"}],   sequence only
      "gaps": ["what the sources don't say that this diagram needs"]
    }

Kinds per type:
    c4-context     nodes person, system, system_ext; groups boundary
    c4-containers  nodes person, system_ext, container, container_ext, database; groups boundary
    deployment     nodes service, person, external; groups cloud, on_premises, region, subscription, resource_group, vnet, subnet, boundary
                   (two or more regions must share one enclosing group; groups may carry an icon too)
    data-flow      nodes external, process, store, person; groups trust_boundary
    sequence       participants person, system, system_ext, container, container_ext, service, external

Layout is layered (longest path over the edges, barycentre ordering), groups get their own
columns so boxes never overlap, and the page is the model's paper size and orientation (default A4 portrait). The drawing is fitted
to one page, or two when one would shrink it too far; the result reports `page.pages` and
`page.scale`. Below 0.7 even on two pages the citations print too small: `page.readable` is
false and `other_orientation_scale` says whether turning the paper would help. Diagram-level metadata (type, drawn time, spine stamp, AD hashes, source hashes) sits
on the diagram's root cell, where draw.io keeps it when the file is edited and saved.

Usage:
    uv run build-drawio.py <project-root> <folder>/<name>.model.json [--force] [--export png,svg|none]

Exit codes: 0=success, 1=invalid model, or <name>.drawio exists without --force, 2=runtime error
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spine as spine_mod  # noqa: E402
import stencils as stencils_mod  # noqa: E402

TYPES = {
    "c4-context": {"nodes": {"person", "system", "system_ext"}, "groups": {"boundary"}},
    "c4-containers": {"nodes": {"person", "system_ext", "container", "container_ext", "database"}, "groups": {"boundary"}},
    "deployment": {"nodes": {"service", "person", "external"},
                   "groups": {"cloud", "on_premises", "region", "subscription", "resource_group", "vnet", "subnet", "boundary"}},
    "data-flow": {"nodes": {"external", "process", "store", "person"}, "groups": {"trust_boundary"}},
    "sequence": {"nodes": {"person", "system", "system_ext", "container", "container_ext", "service", "external"}, "groups": set()},
}
TYPE_NAMES = {"c4-context": "C4 system context", "c4-containers": "C4 containers", "deployment": "Cloud deployment",
              "data-flow": "Data flow", "sequence": "Sequence"}
DATA_TAGS = {"PII", "PHI"}
AD_ID = re.compile(r"^AD-\d+$")
SPINE_DIR = "_bmad-output/planning-artifacts/architecture/"

BOX = "rounded=1;whiteSpace=wrap;html=1;arcSize=8;fontSize=12;"
NODE_STYLES = {
    "person": "shape=actor;html=1;fillColor=#08427B;strokeColor=#073B6F;verticalLabelPosition=bottom;verticalAlign=top;fontSize=12;",
    "system": BOX + "fillColor=#1168BD;strokeColor=#0B4884;fontColor=#FFFFFF;",
    "system_ext": BOX + "fillColor=#999999;strokeColor=#6B6B6B;fontColor=#FFFFFF;",
    "container": BOX + "fillColor=#438DD5;strokeColor=#3C7FC0;fontColor=#FFFFFF;",
    "container_ext": BOX + "fillColor=#999999;strokeColor=#6B6B6B;fontColor=#FFFFFF;",
    "database": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fontSize=12;"
                "fillColor=#438DD5;strokeColor=#3C7FC0;fontColor=#FFFFFF;",
    "service": BOX + "fillColor=#FFFFFF;strokeColor=#0078D4;fontColor=#000000;",
    "external": "rounded=0;whiteSpace=wrap;html=1;fontSize=12;fillColor=#F5F5F5;strokeColor=#666666;",
    "process": "ellipse;whiteSpace=wrap;html=1;fontSize=12;fillColor=#DAE8FC;strokeColor=#6C8EBF;",
    "store": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fontSize=12;"
             "fillColor=#FFF2CC;strokeColor=#D6B656;",
}
GROUP_BASE = ("rounded=0;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;align=left;"
              "verticalAlign=top;spacingLeft=8;spacingTop=2;fillColor=none;fontStyle=1;fontSize=12;")
GROUP_STYLES = {
    "boundary": GROUP_BASE + "dashed=1;strokeColor=#444444;",
    "trust_boundary": GROUP_BASE + "dashed=1;dashPattern=8 4;strokeWidth=2;strokeColor=#B85450;fontColor=#B85450;",
    "cloud": GROUP_BASE + "strokeColor=#0078D4;strokeWidth=2;fontColor=#0078D4;fillColor=#FBFDFF;",
    "region": GROUP_BASE + "strokeColor=#0078D4;fontColor=#0078D4;",
    "on_premises": GROUP_BASE + "strokeColor=#6B6B6B;strokeWidth=2;fontColor=#444444;fillColor=#F7F7F7;",
    "subscription": GROUP_BASE + "dashed=1;strokeColor=#0078D4;",
    "resource_group": GROUP_BASE + "dashed=1;strokeColor=#7A7A7A;",
    "vnet": GROUP_BASE + "strokeColor=#5EA0EF;fillColor=#F2F8FF;",
    "subnet": GROUP_BASE + "dashed=1;strokeColor=#5EA0EF;",
}
EDGE_STYLE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;fontSize=10;"
              "labelBackgroundColor=#FFFFFF;strokeColor=#555555;")
SENSITIVE = "strokeColor=#B85450;strokeWidth=2;fontColor=#B85450;"

W, H = 170, 80            # node slot
PERSON = (44, 52)         # actor figure; its label sits below it
ICON = 56                 # library icon (e.g. Azure); its label sits below it
ICON_SLOT = 120           # width an icon or a person takes in its row
GROUP_ICON = 26           # icon in a group's header (e.g. the AKS cluster)
GAP_ACROSS = 40
PAD_START, PAD_END = 38, 16
TOP = 90                  # room for the title and stamp
PAPER = {"A4": (827, 1169), "A3": (1169, 1654), "Letter": (850, 1100)}  # draw.io page units, portrait
MIN_READABLE_SCALE = 0.7  # below this the 9pt citations print under ~6pt, even across two pages


class ModelError(Exception):
    pass


def as_list(cite) -> list[str]:
    if isinstance(cite, str):
        cite = [cite]
    return [c.strip() for c in cite or [] if isinstance(c, str) and c.strip()]


def validate(model: dict, root: Path) -> list[Path]:
    """Raise ModelError listing every problem; return the source files (spine first)."""
    problems: list[str] = []
    kind = model.get("type")
    if kind not in TYPES:
        raise ModelError(f"type must be one of {sorted(TYPES)}")
    if not str(model.get("title", "")).strip():
        problems.append("title is required")

    spine_rel = str(model.get("spine", ""))
    spine_path = root / spine_rel
    if not (spine_rel.startswith(SPINE_DIR) and spine_rel.endswith("/ARCHITECTURE-SPINE.md") and spine_path.is_file()):
        raise ModelError(f"spine must be an existing {SPINE_DIR}<name>/ARCHITECTURE-SPINE.md, got {spine_rel!r}")
    sources = [spine_path]
    for rel in model.get("sources", []):
        path = (root / rel).resolve()
        try:
            inside = path.relative_to(root.resolve()).as_posix()
        except ValueError:
            inside = ""
        if not inside.startswith("_bmad-output/"):
            problems.append(f"source {rel!r} is outside _bmad-output/: diagrams come from the spine, spec and UX docs only")
        elif not path.is_file():
            problems.append(f"source not found: {rel!r}")
        else:
            sources.append(path)
    ads = spine_mod.parse_ads(spine_path.read_text(encoding="utf-8"))[0]
    names = sorted({p.name for p in sources})

    def check(where: str, item: dict) -> None:
        cites = as_list(item.get("cite"))
        if not cites:
            problems.append(f"{where}: no cite; if no source states it, list it under gaps instead of drawing it")
        for c in cites:
            if AD_ID.match(c):
                if c not in ads:
                    problems.append(f"{where}: cites {c}, which the spine does not define (it defines {', '.join(ads) or 'no ADs'})")
            elif not any(c == n or c.startswith((n + " ", n + "#", n + ":")) for n in names):
                problems.append(f"{where}: cite {c!r} is neither an AD id nor starts with a source file name ({', '.join(names)})")
        for tag in item.get("data") or []:
            if tag not in DATA_TAGS:
                problems.append(f"{where}: data tag {tag!r} must be one of {sorted(DATA_TAGS)}")

    provider = model.get("provider", "azure")
    if kind == "deployment" and provider not in stencils_mod.providers():
        problems.append(f"provider {provider!r} has no stencil catalogue (have: {', '.join(stencils_mod.providers())})")
    libraries: dict[str, dict] = {}
    for item in model.get("nodes", []) + model.get("groups", []) + model.get("participants", []):
        if not item.get("icon"):
            continue
        if kind != "deployment":
            problems.append(f"{item.get('id')}: icons are for deployment diagrams")
            continue
        library, _, sid = item["icon"].rpartition(":")
        library = library or provider
        if library not in libraries:
            try:
                libraries[library] = {s["id"]: s for s in stencils_mod.load(library)["stencils"]}
            except KeyError:
                problems.append(f"{item.get('id')}: icon library {library!r} has no catalogue (have: {', '.join(stencils_mod.providers())})")
                libraries[library] = {}
                continue
        catalogue = libraries[library]
        if sid in catalogue:
            item["_stencil"] = catalogue[sid]
        elif catalogue:
            near = stencils_mod.search({"stencils": list(catalogue.values())}, sid.split("/")[-1].replace("_", " "), 3)
            problems.append(f"{item.get('id')}: icon {item['icon']!r} is not in the {library} catalogue; "
                            f"closest: {', '.join(m['id'] for m in near) or 'none, draw a labelled box'}")

    allowed = TYPES[kind]
    if kind == "sequence":
        parts = model.get("participants", [])
        ids = [p.get("id") for p in parts]
        if not parts:
            problems.append("participants are required")
        if len(ids) != len(set(ids)):
            problems.append("participant ids must be unique")
        for p in parts:
            if p.get("kind") not in allowed["nodes"]:
                problems.append(f"participant {p.get('id')}: kind must be one of {sorted(allowed['nodes'])}")
            check(f"participant {p.get('id')}", p)
        if not model.get("messages"):
            problems.append("messages are required")
        for i, m in enumerate(model.get("messages", []), 1):
            for end in ("from", "to"):
                if m.get(end) not in ids:
                    problems.append(f"message {i}: {end} {m.get(end)!r} is not a participant")
            check(f"message {i}", m)
    else:
        groups, nodes = model.get("groups", []), model.get("nodes", [])
        gids, nids = [g.get("id") for g in groups], [n.get("id") for n in nodes]
        if not nodes:
            problems.append("nodes are required")
        if len(gids + nids) != len(set(gids + nids)):
            problems.append("node and group ids must be unique")
        parents = {g.get("id"): g.get("parent") for g in groups}
        for g in groups:
            if g.get("kind") not in allowed["groups"]:
                problems.append(f"group {g.get('id')}: kind must be one of {sorted(allowed['groups']) or 'none for this type'}")
            if g.get("parent") and g["parent"] not in gids:
                problems.append(f"group {g.get('id')}: parent {g['parent']!r} is not a group")
            if not any(n.get("group") == g.get("id") for n in nodes) and g.get("id") not in parents.values():
                problems.append(f"group {g.get('id')}: empty")
            seen, cur = set(), g.get("id")
            while cur:
                if cur in seen:
                    problems.append(f"group {g.get('id')}: parent cycle")
                    break
                seen.add(cur)
                cur = parents.get(cur)
            check(f"group {g.get('id')}", g)
        regions = [g for g in groups if g.get("kind") == "region"]
        if len(regions) > 1 and (len({g.get("parent") for g in regions}) > 1 or not regions[0].get("parent")):
            problems.append("multi-region: put every region group inside one enclosing group (kind cloud), "
                            "with global services such as Front Door and DNS beside the regions in it")
        for n in nodes:
            if n.get("kind") not in allowed["nodes"]:
                problems.append(f"node {n.get('id')}: kind must be one of {sorted(allowed['nodes'])}")
            if n.get("group") and n["group"] not in gids:
                problems.append(f"node {n.get('id')}: group {n['group']!r} is not a group")
            check(f"node {n.get('id')}", n)
        for i, e in enumerate(model.get("edges", []), 1):
            for end in ("from", "to"):
                if e.get(end) not in nids:
                    problems.append(f"edge {i}: {end} {e.get(end)!r} is not a node")
            check(f"edge {i} ({e.get('from')} -> {e.get('to')})", e)
    page = model.get("page") or {}
    if page.get("size", "A4") not in PAPER or page.get("orientation", "portrait") not in ("portrait", "landscape"):
        problems.append(f"page must be {{\"size\": one of {sorted(PAPER)}, \"orientation\": \"portrait\" or \"landscape\"}}")
    if not isinstance(model.get("gaps", []), list):
        problems.append("gaps must be a list of strings")
    if problems:
        raise ModelError("; ".join(problems))
    return sources


# --- labels -------------------------------------------------------------------------------

def cite_line(item: dict) -> str:
    return f'<br><font style="font-size:9px" color="#555555">{html.escape("; ".join(as_list(item.get("cite"))))}</font>'


def node_label(item: dict, with_tech: bool = True) -> str:
    text = ""
    if item.get("data"):
        text += f'<font color="#B85450"><b>{"/".join(item["data"])}</b></font> '
    text += f"<b>{html.escape(item.get('label', item['id']))}</b>"
    if with_tech and item.get("tech"):
        text += f"<br><i>[{html.escape(item['tech'])}]</i>"
    if item.get("description"):
        text += f'<br><font style="font-size:10px">{html.escape(item["description"])}</font>'
    return text + cite_line(item)


def edge_label(item: dict, prefix: str = "") -> str:
    text = prefix + html.escape(item.get("label", ""))
    if item.get("tech"):
        text += f" [{html.escape(item['tech'])}]"
    if item.get("data"):
        text = f'<b>{"/".join(item["data"])}</b> ' + text
    return text + cite_line(item)


# --- layered layout -----------------------------------------------------------------------

def assign_layers(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    ids = [n["id"] for n in nodes]
    adj = {i: [] for i in ids}
    for e in edges:
        if e["from"] != e["to"]:
            adj[e["from"]].append(e["to"])
    state: dict[str, int] = {}
    preds = {i: [] for i in ids}

    def dfs(u: str) -> None:  # keep forward edges only, so a cycle can't break the layering
        state[u] = 1
        for v in adj[u]:
            if state.get(v) == 1:
                continue
            preds[v].append(u)
            if not state.get(v):
                dfs(v)
        state[u] = 2

    for i in ids:
        if not state.get(i):
            dfs(i)
    layer: dict[str, int] = {}

    def depth(u: str) -> int:
        if u not in layer:
            layer[u] = 0
            layer[u] = max((depth(p) + 1 for p in preds[u]), default=0)
        return layer[u]

    for i in ids:
        depth(i)
    for n in nodes:
        if isinstance(n.get("layer"), int) and n["layer"] >= 0:
            layer[n["id"]] = n["layer"]
    used = {lyr: i for i, lyr in enumerate(sorted(set(layer.values())))}  # close up empty layers
    return {nid: used[lyr] for nid, lyr in layer.items()}


def order_in_layers(nodes: list[dict], edges: list[dict], layer: dict[str, int]) -> dict[str, float]:
    pos = {n["id"]: float(i) for i, n in enumerate(nodes)}
    nbrs = {n["id"]: [] for n in nodes}
    for e in edges:
        nbrs[e["from"]].append(e["to"])
        nbrs[e["to"]].append(e["from"])
    for _ in range(2):
        for n in nodes:
            near = [pos[m] for m in nbrs[n["id"]] if layer[m] != layer[n["id"]]]
            if near:
                pos[n["id"]] = sum(near) / len(near)
        by_layer: dict[int, list[str]] = {}
        for n in nodes:
            by_layer.setdefault(layer[n["id"]], []).append(n["id"])
        for ids in by_layer.values():
            for rank, i in enumerate(sorted(ids, key=lambda k: pos[k])):
                pos[i] = float(rank)
    return pos


def layout(model: dict) -> tuple[dict, dict]:
    """({node id: (x, y, w, h)}, {group id: (x, y, w, h)}), absolute page units."""
    nodes, edges, groups = model.get("nodes", []), model.get("edges", []), model.get("groups", [])
    lr = model.get("direction", "LR" if model["type"] == "data-flow" else "TB") == "LR"
    s_across, s_along = (H, W) if lr else (W, H)
    layer = assign_layers(nodes, edges)
    key = order_in_layers(nodes, edges, layer)
    children: dict = {None: [g["id"] for g in groups if not g.get("parent")]}
    direct: dict = {None: []}
    for g in groups:
        children.setdefault(g["id"], [])
        direct[g["id"]] = []
    for g in groups:
        if g.get("parent"):
            children[g["parent"]].append(g["id"])
    for n in nodes:
        direct[n.get("group")].append(n["id"])

    span: dict = {}  # group id -> (first layer, last layer) of the nodes inside it

    def spans(gid) -> tuple[int, int]:
        ls = [layer[n] for n in direct[gid]] + [x for c in children[gid] for x in spans(c)]
        span[gid] = (min(ls), max(ls))
        return span[gid]

    for gid in children[None]:
        spans(gid)
    # Each gap between two layers leaves room for the group edges that end above it and start below it.
    top_layer = max(layer.values(), default=0)
    parent_of = {g["id"]: g.get("parent") for g in groups}

    def nested(gid, edge: int, lyr: int) -> int:  # boxes in gid's ancestry that also start (0) or end (1) at lyr
        count = 0
        while gid and span[gid][edge] == lyr:
            count, gid = count + 1, parent_of[gid]
        return count

    offsets = [TOP]
    for lyr in range(top_layer):
        ends = max((nested(g, 1, lyr) for g in span), default=0)
        starts = max((nested(g, 0, lyr + 1) for g in span), default=0)
        offsets.append(offsets[-1] + s_along + 50 + ends * PAD_END + starts * PAD_START)
    iconish = {n["id"] for n in nodes if n.get("icon") or n.get("style") or n.get("kind") == "person"}

    def across(nid: str) -> float:  # icons and people need less room than a labelled box
        return s_across if lr or nid not in iconish else ICON_SLOT

    def row_width(ids: list[str]) -> float:
        return sum(across(i) for i in ids) + GAP_ACROSS * max(len(ids) - 1, 0)

    rows_of: dict = {}   # group id -> {layer: [node ids]}
    side_of: dict = {}   # group id -> layers whose nodes sit in a column beside the child groups
    width: dict = {}
    core: dict = {}

    def measure(gid) -> float:
        kid_widths = [measure(c) for c in children[gid]]
        kid_layers = [span[c] for c in children[gid]]
        rows: dict[int, list[str]] = {}
        for nid in direct[gid]:
            rows.setdefault(layer[nid], []).append(nid)
        for ids in rows.values():
            ids.sort(key=lambda k: key[k])
        # A row that shares layers with a child group sits beside it; any other row spans the whole box.
        side = {l for l in rows if any(lo <= l <= hi for lo, hi in kid_layers)}
        side_w = max((row_width(rows[l]) for l in side), default=0)
        kids_w = sum(kid_widths) + GAP_ACROSS * max(len(kid_widths) - 1, 0)
        core[gid] = side_w + (GAP_ACROSS if side_w and kid_widths else 0) + kids_w
        free_w = max((row_width(rows[l]) for l in rows if l not in side), default=0)
        rows_of[gid], side_of[gid] = rows, side
        width[gid] = max(core[gid], free_w) + (PAD_START + PAD_END if gid else 0)
        return width[gid]

    measure(None)

    def along(lyr: int) -> float:
        return offsets[lyr]

    slot: dict[str, tuple[float, float]] = {}
    box: dict[str, list[float]] = {}

    def place(gid, x0: float) -> tuple[float, float]:
        inner_x = x0 + (PAD_START if gid else 0)
        inner_w = width[gid] - (PAD_START + PAD_END if gid else 0)
        rows, side = rows_of[gid], side_of[gid]
        side_w = max((row_width(rows[l]) for l in side), default=0)
        cx = inner_x + (inner_w - core[gid]) / 2
        lo, hi = float("inf"), float("-inf")
        for lyr, ids in rows.items():
            left, room = (cx, side_w) if lyr in side else (inner_x, inner_w)
            x = left + (room - row_width(ids)) / 2
            for nid in ids:
                slot[nid] = (x, along(lyr))
                x += across(nid) + GAP_ACROSS
            lo, hi = min(lo, along(lyr)), max(hi, along(lyr) + s_along)
        if side_w:
            cx += side_w + GAP_ACROSS
        for c in children[gid]:
            clo, chi = place(c, cx)
            lo, hi = min(lo, clo), max(hi, chi)
            cx += width[c] + GAP_ACROSS
        if gid:
            lo, hi = lo - PAD_START, hi + PAD_END
            box[gid] = [x0, lo, width[gid], hi - lo]
        return lo, hi

    place(None, 20)
    if lr:
        return ({n: (b, a, s_along, across(n)) for n, (a, b) in slot.items()},
                {g: (b, a, wb, wa) for g, (a, b, wa, wb) in box.items()})
    return ({n: (a, b, across(n), s_along) for n, (a, b) in slot.items()}, {g: tuple(v) for g, v in box.items()})


# --- XML ----------------------------------------------------------------------------------

def add_cell(root_el, cid: str, value: str, style: str, parent: str, geo=None, *, edge=False,
             source=None, target=None, cite=None, points=None):
    attrs = {"id": cid, "label": value}
    if cite is not None:
        joined = "; ".join(as_list(cite))
        attrs.update({"cite": joined, "tooltip": f"Source: {joined}"})
    obj = ET.SubElement(root_el, "object", attrs)
    mx = ET.SubElement(obj, "mxCell", {"style": style, "parent": parent, "edge" if edge else "vertex": "1"})
    if source:
        mx.set("source", source)
    if target:
        mx.set("target", target)
    g = ET.SubElement(mx, "mxGeometry", {"as": "geometry"})
    if geo:
        g.attrib.update(dict(zip(("x", "y", "width", "height"), (f"{v:g}" for v in geo))))
    else:
        g.set("relative", "1")
    if points:
        (sx, sy), (tx, ty), mids = points
        ET.SubElement(g, "mxPoint", {"x": f"{sx:g}", "y": f"{sy:g}", "as": "sourcePoint"})
        ET.SubElement(g, "mxPoint", {"x": f"{tx:g}", "y": f"{ty:g}", "as": "targetPoint"})
        if mids:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for x, y in mids:
                ET.SubElement(arr, "mxPoint", {"x": f"{x:g}", "y": f"{y:g}"})


def draw_graph(model: dict, root_el) -> tuple[float, float]:
    node_geo, group_geo = layout(model)
    groups = {g["id"]: g for g in model.get("groups", [])}

    def origin(gid):
        return group_geo[gid][:2] if gid else (0, 0)

    drawn: list[str] = []

    def draw_group(gid: str) -> None:  # parents first, so draw.io nests children inside them
        if gid in drawn:
            return
        g = groups[gid]
        if g.get("parent"):
            draw_group(g["parent"])
        x, y, w, h = group_geo[gid]
        ox, oy = origin(g.get("parent"))
        label = (f"{html.escape(g['label'])} <font style=\"font-size:9px\" color=\"#555555\">"
                 f"({html.escape('; '.join(as_list(g['cite'])))})</font>")
        stencil = g.get("_stencil")
        style = GROUP_STYLES[g["kind"]] + ("spacingLeft=34;spacingTop=6;" if stencil else "")
        add_cell(root_el, f"g-{gid}", label, style, f"g-{g['parent']}" if g.get("parent") else "1",
                 (x - ox, y - oy, w, h), cite=g["cite"])
        if stencil:  # the hosting service's icon in the box's header
            k = GROUP_ICON / max(stencil["w"], stencil["h"])
            add_cell(root_el, f"g-{gid}-icon", "", stencil["style"].rstrip(";") + ";movable=0;resizable=0;",
                     f"g-{gid}", (6, 5, round(stencil["w"] * k), round(stencil["h"] * k)))
        drawn.append(gid)

    for gid in groups:
        draw_group(gid)
    for n in model["nodes"]:
        x, y, w, h = node_geo[n["id"]]
        stencil = n.get("_stencil")
        if stencil or n.get("style"):
            style = (stencil["style"] if stencil else n["style"]).rstrip(";") + ";verticalLabelPosition=bottom;verticalAlign=top;html=1;"
            sw, sh = (stencil["w"], stencil["h"]) if stencil else (ICON, ICON)
            k = ICON / max(sw, sh)
            x, w, h = x + (w - sw * k) / 2, round(sw * k), round(sh * k)
        else:
            style = NODE_STYLES[n["kind"]] + (SENSITIVE if n.get("data") else "")
            if n["kind"] == "person":
                x, w, h = x + (w - PERSON[0]) / 2, *PERSON
        ox, oy = origin(n.get("group"))
        add_cell(root_el, f"n-{n['id']}", node_label(n, with_tech=model["type"] != "c4-context"), style,
                 f"g-{n['group']}" if n.get("group") else "1", (x - ox, y - oy, w, h), cite=n["cite"])
    for i, e in enumerate(model.get("edges", []), 1):
        style = EDGE_STYLE + ("dashed=1;" if e.get("dashed") else "") + (SENSITIVE if e.get("data") else "")
        add_cell(root_el, f"e-{i}", edge_label(e), style, "1", edge=True,
                 source=f"n-{e['from']}", target=f"n-{e['to']}", cite=e["cite"])
    boxes = list(node_geo.values()) + list(group_geo.values())
    return max(x + w for x, _, w, _ in boxes), max(y + h for _, y, _, h in boxes) + 50


def draw_sequence(model: dict, root_el) -> tuple[float, float]:
    parts, msgs = model["participants"], model["messages"]
    head, step, gap = 60, 44, 70
    height = head + step * (len(msgs) + 1)
    cx = {}
    for i, p in enumerate(parts):
        x = 20 + i * (W + gap)
        cx[p["id"]] = x + W / 2
        colours = "".join(re.findall(r"(?:fillColor|strokeColor|fontColor)=[^;]+;", NODE_STYLES[p["kind"]]))
        style = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;collapsible=0;"
                 f"recursiveResize=0;outlineConnect=0;size={head};fontSize=12;{colours}")
        add_cell(root_el, f"p-{p['id']}", node_label(p), style, "1", (x, TOP, W, height), cite=p["cite"])
    for j, m in enumerate(msgs, 1):
        y = TOP + head + j * step
        style = ("html=1;verticalAlign=bottom;fontSize=10;labelBackgroundColor=#FFFFFF;"
                 + ("dashed=1;endArrow=open;endFill=0;" if m.get("return") else "endArrow=block;endFill=1;")
                 + (SENSITIVE if m.get("data") else ""))
        a, b = cx[m["from"]], cx[m["to"]]
        if a == b:
            pts = ((a, y - 10), (a, y + 10), [(a + 50, y - 10), (a + 50, y + 10)])
            style += "edgeStyle=none;align=left;"
        else:
            pts = ((a, y), (b, y), [])
        add_cell(root_el, f"m-{j}", edge_label(m, prefix=f"{j}. "), style, "1", edge=True, cite=m["cite"], points=pts)
    return 20 + len(parts) * (W + gap) - gap, TOP + height + 40


def page_fit(width: float, height: float, size: str, orientation: str) -> dict:
    """Fit the drawing to the chosen paper: one page, else two (side by side or stacked, whichever is larger)."""
    short, long_ = PAPER[size]
    pw, ph = (short, long_) if orientation == "portrait" else (long_, short)
    margin = 80

    def scale(w_avail: float, h_avail: float) -> float:
        return min(1.0, (w_avail - margin) / width, (h_avail - margin) / height)

    one = scale(pw, ph)
    two = max(scale(2 * pw, ph), scale(pw, 2 * ph))
    pages, best = (1, one) if one >= MIN_READABLE_SCALE or one >= two else (2, two)
    fit = {"size": size, "orientation": orientation, "pages": pages, "scale": round(best, 2),
           "readable": best >= MIN_READABLE_SCALE, "page_width": pw, "page_height": ph}
    if not fit["readable"]:
        other = "landscape" if orientation == "portrait" else "portrait"
        ow, oh = (ph, pw)
        alt = max(scale(ow, oh), scale(2 * ow, oh), scale(ow, 2 * oh))
        fit["other_orientation_scale"] = {other: round(alt, 2)}
    return fit


def stamp_line(st: dict, drawn: str) -> str:
    if st["spine_commit"]:
        src = f"@ {st['spine_commit'][:7]} ({st['spine_committed'][:10]})" + (" + uncommitted changes" if st["spine_dirty"] else "")
    else:
        src = f"modified {st['spine_modified'][:10]} (not in git)"
    return f"Drawn {drawn[:10]} from {st['spine']} {src}"


def build(model: dict, root: Path) -> tuple[bytes, dict]:
    sources = validate(model, root)
    st = spine_mod.stamp(root, sources[0])
    drawn = datetime.now(timezone.utc).isoformat(timespec="seconds")
    items = [i for k in ("nodes", "groups", "edges", "participants", "messages") for i in model.get(k, [])]
    cited = sorted({c for i in items for c in as_list(i.get("cite")) if AD_ID.match(c)}, key=lambda a: int(a[3:]))

    mxfile = ET.Element("mxfile", {"host": "org-kit leonardo-da-vinci", "type": "device"})
    diagram = ET.SubElement(mxfile, "diagram", {"id": model["type"], "name": TYPE_NAMES[model["type"]]})
    graph = ET.SubElement(diagram, "mxGraphModel", {"grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1",
                                                     "connect": "1", "arrows": "1", "fold": "1", "page": "1",
                                                     "pageScale": "1", "math": "0", "shadow": "0"})
    root_el = ET.SubElement(graph, "root")
    meta = ET.SubElement(root_el, "object", {
        "id": "0", "label": "", "arch_diagram": "1", "arch_type": model["type"], "arch_title": model["title"],
        "drawn": drawn, "spine": st["spine"], "spine_commit": st["spine_commit"],
        "spine_committed": st["spine_committed"], "spine_dirty": str(st["spine_dirty"]).lower(),
        "spine_modified": st["spine_modified"], "ad_hashes": json.dumps(st["ad_hashes"], separators=(",", ":")),
        "cited_ads": ",".join(cited),
        "source_hashes": json.dumps({p.resolve().relative_to(root.resolve()).as_posix(): spine_mod.file_hash(p)
                                     for p in sources[1:]}, separators=(",", ":")),
    })
    ET.SubElement(meta, "mxCell")
    ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})

    right, bottom = (draw_sequence if model["type"] == "sequence" else draw_graph)(model, root_el)
    right = max(right, 520)
    add_cell(root_el, "title", f"<b>{html.escape(TYPE_NAMES[model['type']])}: {html.escape(model['title'])}</b>",
             "text;html=1;align=left;verticalAlign=top;fontSize=16;", "1", (20, 10, right - 20, 28))
    add_cell(root_el, "stamp", html.escape(stamp_line(st, drawn)),
             "text;html=1;align=left;verticalAlign=top;fontSize=10;fontColor=#555555;", "1", (20, 38, right - 20, 20))
    gaps = [str(g) for g in model.get("gaps", []) if str(g).strip()]
    notes = []
    if model["type"] == "data-flow":
        notes.append('<b>Key:</b> <font color="#B85450"><b>PII/PHI</b></font> marks personal or health data; '
                     "red dashed boxes are trust boundaries.")
    notes.append("<b>Gaps (not drawn):</b>" + ("<br>" + "<br>".join(f"• {html.escape(g)}" for g in gaps) if gaps else " none"))
    notes.append("Each element's source is in grey under its name and in its tooltip.")
    notes_h = 40 + 16 * (len(gaps) + 2 * len(notes))
    add_cell(root_el, "notes", "<br><br>".join(notes),
             "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=11;strokeColor=#CCCCCC;fillColor=#FAFAFA;spacing=8;",
             "1", (20, bottom, right - 20, notes_h))
    page = model.get("page") or {}
    fit = page_fit(right + 20, bottom + notes_h + 20, page.get("size", "A4"), page.get("orientation", "portrait"))
    graph.attrib.update({"pageWidth": str(fit.pop("page_width")), "pageHeight": str(fit.pop("page_height"))})
    meta.set("page", f"{fit['size']} {fit['orientation']} x{fit['pages']} at {fit['scale']}")
    ET.indent(mxfile)
    report = {"type": model["type"], "stamp": stamp_line(st, drawn), "cited_ads": cited, "gaps": gaps, "page": fit,
              "elements": len(items)}
    return ET.tostring(mxfile, encoding="utf-8"), report


def export(target: Path, formats: list[str]) -> dict:
    if not formats:
        return {"skipped": "not requested"}
    cli = spine_mod.drawio_cli()
    if not cli:
        return {"skipped": "draw.io desktop not found (install it, or set DRAWIO_CLI to its executable)"}
    written, failed = [], []
    for fmt in formats:
        out = target.with_suffix(f".{fmt}")
        args = [cli, "--export", "--format", fmt, "--border", "10", *(["--scale", "2"] if fmt == "png" else []),
                "--output", str(out), str(target)]
        try:
            res = subprocess.run(args, capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            failed.append({"format": fmt, "error": str(exc)})
            continue
        if res.returncode == 0 and out.is_file():
            written.append(str(out))
        else:
            failed.append({"format": fmt, "error": (res.stderr or res.stdout).strip()[-400:]})
    return {"written": written, "failed": failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_root")
    parser.add_argument("model", help="<folder>/<name>.model.json; <name>.drawio is written beside it")
    parser.add_argument("--force", action="store_true", help="Replace an existing <name>.drawio (hand edits in it are lost)")
    parser.add_argument("--export", default="png,svg", help="Comma-separated export formats, or 'none' (default: png,svg)")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    model_path = Path(args.model)
    if not model_path.is_absolute() and not model_path.exists():
        model_path = root / model_path
    if not model_path.name.endswith(".model.json"):
        print(json.dumps({"status": "error", "message": "the model file must be named <name>.model.json"}))
        return 1
    target = model_path.with_name(model_path.name[: -len(".model.json")] + ".drawio")
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
        xml_bytes, report = build(model, root)
        if target.exists() and not args.force:
            print(json.dumps({"status": "error", "message": f"{target.name} exists; pass --force to replace it (hand edits in it are lost)"}))
            return 1
        target.write_bytes(xml_bytes)
    except ModelError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 2
    formats = [] if args.export.strip().lower() == "none" else [f.strip().lower() for f in args.export.split(",") if f.strip()]
    print(json.dumps({"status": "success", "file": str(target), **report, "exports": export(target, formats)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
