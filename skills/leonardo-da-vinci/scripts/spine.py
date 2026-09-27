#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Describe a project's architecture spines, diagrams folder and existing diagrams as JSON.

Without --spine: the spines found at the BMad location, the diagrams folder (org config
`diagrams_folder`), the diagrams already in it, and whether draw.io desktop is installed
for PNG/SVG exports.

With --spine: that spine's stamp, which is what a diagram records about the spine it was
drawn from: path, last git commit touching it (and whether it has uncommitted changes),
modification time, and a short hash of every AD's text. diagram-drift.py compares a
diagram's stamp with the current one to name the ADs that changed.

An AD starts at a line whose first token is its id (`AD-<n>`): a heading (`### AD-4 Hosting`),
a list item (`- **AD-4** ...`) or a bold paragraph. It runs to the next AD, or, when the AD
is a heading, to the next heading at the same or a higher level. The first definition of an
id wins; later ones are reported under `duplicates`.

Usage:
    uv run spine.py <project-root> [--spine <path>] [-o <file>]

Exit codes: 0=success, 1=no spine found or bad path
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

SPINE_GLOB = "_bmad-output/planning-artifacts/architecture/*/ARCHITECTURE-SPINE.md"
DEFAULT_FOLDER = "docs/architecture/diagrams"
CONFIG_FILES = ["_bmad/config.toml", "_bmad/custom/config.toml", "_bmad/custom/config.user.toml"]
AD_START = re.compile(r"^ {0,3}(#{1,6}\s+)?(?:[-*+]\s+)?(?:\*\*|__)?\[?(AD-\d+)\b\]?(?:\*\*|__)?[\s:.\-–—]*(.*)$")
HEADING = re.compile(r"^ {0,3}(#{1,6})\s")


def find_spines(root: Path) -> list[Path]:
    return sorted(root.glob(SPINE_GLOB))


def diagrams_folder(root: Path) -> Path:
    """The org config's diagrams_folder (custom overrides win), resolved against the root."""
    value = DEFAULT_FOLDER
    for rel in CONFIG_FILES:
        path = root / rel
        if path.is_file():
            try:
                found = tomllib.loads(path.read_text(encoding="utf-8")).get("modules", {}).get("org", {}).get("diagrams_folder")
            except tomllib.TOMLDecodeError:
                continue
            if isinstance(found, str) and found.strip():
                value = found.strip()
    value = value.replace("{project-root}", "").lstrip("/\\") if value.startswith("{project-root}") else value
    path = Path(value)
    return path if path.is_absolute() else root / path


def drawio_cli() -> str | None:
    env = os.environ.get("DRAWIO_CLI")
    if env:
        return env if Path(env).is_file() or shutil.which(env) else None
    for name in ("drawio", "draw.io"):
        if shutil.which(name):
            return shutil.which(name)
    for app in ("/Applications/draw.io.app/Contents/MacOS/draw.io", r"C:\Program Files\draw.io\draw.io.exe"):
        if Path(app).is_file():
            return app
    return None


def parse_ads(text: str) -> tuple[dict[str, dict], list[str]]:
    """Return ({AD id: {title, line, hash}}, duplicate ids)."""
    lines = text.splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = AD_START.match(line)
        if m:
            level = len(m.group(1).strip()) if m.group(1) else 0
            starts.append((i, m.group(2), level, m.group(3).strip(" *_")))
    ads: dict[str, dict] = {}
    duplicates: list[str] = []
    for n, (i, ad_id, level, title) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        for j in range(i + 1, end):
            h = HEADING.match(lines[j])
            if h and (level == 0 or len(h.group(1)) <= level):
                end = j
                break
        if ad_id in ads:
            duplicates.append(ad_id)
            continue
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(l.rstrip() for l in lines[i:end]).strip())
        ads[ad_id] = {"title": title, "line": i + 1, "hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]}
    return ads, duplicates


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def stamp(root: Path, spine: Path) -> dict:
    rel = spine.resolve().relative_to(root.resolve()).as_posix()
    log = _git(root, "log", "-1", "--format=%H%x09%cI", "--", rel)
    commit, committed = (log.split("\t") + [""])[:2] if log else ("", "")
    dirty = bool(_git(root, "status", "--porcelain", "--", rel)) if commit else False
    modified = datetime.fromtimestamp(spine.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    ads, duplicates = parse_ads(spine.read_text(encoding="utf-8"))
    return {"spine": rel, "spine_commit": commit, "spine_committed": committed, "spine_dirty": dirty,
            "spine_modified": modified, "ad_hashes": {k: v["hash"] for k, v in ads.items()},
            "ads": ads, "duplicates": duplicates}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_root")
    parser.add_argument("--spine", help="Spine to describe (relative to the project root, or absolute)")
    parser.add_argument("-o", "--output", help="Write the JSON here instead of stdout")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()

    if args.spine:
        spine = Path(args.spine)
        spine = spine if spine.is_absolute() else root / spine
        try:
            result = {"status": "success", **stamp(root, spine)} if spine.is_file() else \
                {"status": "error", "message": f"spine not found: {args.spine}"}
        except ValueError:
            result = {"status": "error", "message": f"spine must be inside the project: {spine}"}
    else:
        spines = find_spines(root)
        folder = diagrams_folder(root)
        result = {
            "status": "success" if spines else "error",
            "spines": [p.relative_to(root).as_posix() for p in spines],
            "diagrams_folder": folder.as_posix(),
            "diagrams": sorted(p.name for p in folder.glob("*.drawio")) if folder.is_dir() else [],
            "drawio_cli": drawio_cli(),
        }
        if not spines:
            result["message"] = f"no architecture spine at {SPINE_GLOB}"

    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
