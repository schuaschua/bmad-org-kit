#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Check every diagram in the diagrams folder against the spine it was drawn from.

Reads the stamp build-drawio.py puts on each .drawio file's root cell (draw.io keeps it
when the file is edited and saved, compressed or not) and compares it with the spine and
sources as they are now:

    current       the spine is unchanged since the diagram was drawn
    outdated      the spine changed after drawing, but no AD and no other source did
    stale         an AD the diagram was drawn against changed, was added or was removed,
                  or another source file changed; `ads` names each AD and whether the
                  diagram cites it
    spine-missing the recorded spine no longer exists
    unstamped     not drawn by leonardo-da-vinci (no stamp), so it can't be checked

Usage:
    uv run diagram-drift.py <project-root> [--folder <diagrams folder>] [-o <file>]

The folder defaults to the org config's diagrams_folder (docs/architecture/diagrams).
Exit codes: 0=nothing stale, 1=a diagram is stale or its spine is missing, 2=runtime error
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spine as spine_mod  # noqa: E402


def read_stamp(path: Path) -> dict | None:
    """The attributes of the first page's root cell, or None when it carries no stamp."""
    diagram = ET.parse(path).getroot().find("diagram")
    if diagram is None:
        return None
    graph = diagram.find("mxGraphModel")
    if graph is None and (diagram.text or "").strip():  # draw.io's compressed page format
        raw = zlib.decompress(base64.b64decode(diagram.text.strip()), -15)
        graph = ET.fromstring(urllib.parse.unquote(raw.decode("utf-8")))
    if graph is None:
        return None
    for el in graph.iter():
        if el.get("id") == "0" and el.get("arch_diagram") == "1":
            return dict(el.attrib)
    return None


def check(root: Path, path: Path) -> dict:
    st = read_stamp(path)
    model = path.with_name(path.stem + ".model.json")
    entry = {"file": path.name, "model": model.name if model.is_file() else None}
    if not st:
        return {**entry, "status": "unstamped"}
    entry.update({"type": st.get("arch_type"), "title": st.get("arch_title"), "drawn": st.get("drawn"),
                  "spine": st.get("spine"),
                  "drawn_from": st.get("spine_commit", "")[:7] or st.get("spine_modified", "")})
    spine = root / st.get("spine", "")
    if not st.get("spine") or not spine.is_file():
        return {**entry, "status": "spine-missing"}

    now = spine_mod.stamp(root, spine)
    entry["spine_now"] = now["spine_commit"][:7] or now["spine_modified"]
    if now["spine_dirty"]:
        entry["spine_now"] += " + uncommitted changes"
    old = json.loads(st.get("ad_hashes") or "{}")
    cited = set(filter(None, st.get("cited_ads", "").split(",")))
    ads = []
    for ad_id in sorted(set(old) | set(now["ad_hashes"]), key=lambda a: int(a[3:])):
        before, after = old.get(ad_id), now["ad_hashes"].get(ad_id)
        if before != after:
            change = "added" if before is None else "removed" if after is None else "changed"
            ads.append({"id": ad_id, "change": change, "cited": ad_id in cited,
                        "title": now["ads"].get(ad_id, {}).get("title", "")})
    sources = []
    for rel, digest in json.loads(st.get("source_hashes") or "{}").items():
        src = root / rel
        if not src.is_file():
            sources.append({"file": rel, "change": "removed"})
        elif spine_mod.file_hash(src) != digest:
            sources.append({"file": rel, "change": "changed"})

    moved = (now["spine_commit"] != st.get("spine_commit", "") or now["spine_dirty"]
             or (not now["spine_commit"] and now["spine_modified"] != st.get("spine_modified")))
    status = "stale" if ads or sources else "outdated" if moved else "current"
    return {**entry, "status": status, "ads": ads, "sources": sources}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_root")
    parser.add_argument("--folder", help="Diagrams folder (default: the org config's diagrams_folder)")
    parser.add_argument("-o", "--output", help="Write the JSON here instead of stdout")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    folder = Path(args.folder) if args.folder else spine_mod.diagrams_folder(root)
    folder = folder if folder.is_absolute() else root / folder
    try:
        results = [check(root, p) for p in sorted(folder.glob("*.drawio"))] if folder.is_dir() else []
    except (OSError, ET.ParseError, ValueError, zlib.error) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 2
    counts = {s: sum(r["status"] == s for r in results) for s in ("current", "outdated", "stale", "spine-missing", "unstamped")}
    text = json.dumps({"status": "success", "folder": folder.as_posix(), "counts": counts, "diagrams": results}, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 1 if counts["stale"] or counts["spine-missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
