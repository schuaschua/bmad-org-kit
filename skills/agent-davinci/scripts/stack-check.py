#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Check that the project's pipelines and infrastructure code use the DevOps stack agreed in architecture.md.

Reads the **DevOps** section of `architecture.md` (in the org config's `architecture_folder`, default
docs/architecture) and picks out the tools its table's Answer column names, in three categories:

- ci:  GitHub Actions, Jenkins, CircleCI, Azure DevOps Pipelines, Bitbucket Pipelines, GitLab CI
- cd:  Argo CD, Flux, Tekton
- iac: Terraform, Bicep, ARM templates, CloudFormation, AWS CDK, Pulumi

Then it looks for each tool's files in the project (a Jenkinsfile, .github/workflows/*.yml, *.tf,
*.bicep, manifests of kind argoproj.io, fluxcd.io or tekton.dev ...). A category is checked only when
the answers name at least one of its tools:

- `off_stack`: files of a tool the answers don't name, in a checked category (Bicep when Terraform was
  agreed). These fail the check.
- `missing`: an agreed tool with no files yet. Normal early on; with --strict it fails the check too.
- `unchecked`: categories whose answer names no tool this script knows.

A deliberate exception is a change to the principles (Da Vinci's AP), not to this script.

Files are the tracked and untracked-but-not-ignored ones when the project is a git repository, else a
walk that skips dependency and tool folders (node_modules, .terraform, vendor, _bmad ...).

Usage:
    uv run stack-check.py <project-root> [--strict]

Exit codes: 0=compliant (or no architecture.md / no DevOps section yet), 1=off-stack files
(or, with --strict, an agreed tool with no files), 2=bad path
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spine as spine_mod  # noqa: E402

YAML = ("*.yml", "*.yaml")
# tool -> category, names that select it in an answer, file globs (matched against the path relative to the
# root, and against the file name alone for globs without a slash), and for content markers: (globs, regex)
TOOLS: dict[str, dict] = {
    "github-actions": {"category": "ci", "names": [r"github actions"], "files": [".github/workflows/*.yml", ".github/workflows/*.yaml"]},
    "jenkins": {"category": "ci", "names": [r"jenkins"], "files": ["Jenkinsfile", "*.jenkinsfile", "Jenkinsfile.*"]},
    "circleci": {"category": "ci", "names": [r"circle ?ci"], "files": [".circleci/config.yml", ".circleci/config.yaml"]},
    "azure-pipelines": {"category": "ci", "names": [r"azure pipelines", r"(azure devops|ado)( \(ado\))? pipelines"],
                        "files": ["azure-pipelines.yml", "azure-pipelines.yaml", "*.azure-pipelines.yml", ".azuredevops/*.yml",
                                  ".azure-pipelines/*.yml"]},
    "bitbucket-pipelines": {"category": "ci", "names": [r"bitbucket pipelines"], "files": ["bitbucket-pipelines.yml"]},
    "gitlab-ci": {"category": "ci", "names": [r"gitlab ci", r"gitlab pipelines"], "files": [".gitlab-ci.yml"]},
    "argocd": {"category": "cd", "names": [r"argo ?cd"], "content": (YAML, r"apiVersion:\s*argoproj\.io/")},
    "flux": {"category": "cd", "names": [r"\bflux(cd)?\b"], "content": (YAML, r"apiVersion:\s*[a-z.]*toolkit\.fluxcd\.io/")},
    "tekton": {"category": "cd", "names": [r"tekton"], "content": (YAML, r"apiVersion:\s*tekton\.dev/")},
    "terraform": {"category": "iac", "names": [r"terraform", r"opentofu"], "files": ["*.tf", "*.tf.json"]},
    "bicep": {"category": "iac", "names": [r"bicep"], "files": ["*.bicep", "*.bicepparam"]},
    "arm": {"category": "iac", "names": [r"\barm\b", r"arm templates?"],
            "content": (("*.json",), r"schema\.management\.azure\.com/schemas/[^\"]*deploymentTemplate\.json")},
    "cloudformation": {"category": "iac", "names": [r"cloudformation", r"\bsam\b"],
                       "content": (YAML + ("*.json", "*.template"), r"AWSTemplateFormatVersion")},
    "cdk": {"category": "iac", "names": [r"\b(aws )?cdk\b"], "files": ["cdk.json"]},
    "pulumi": {"category": "iac", "names": [r"pulumi"], "files": ["Pulumi.yaml", "Pulumi.yml"]},
}
SKIP_DIRS = {".git", "node_modules", ".terraform", "vendor", "third_party", ".venv", "venv", "__pycache__",
             "_bmad", "_bmad-output", ".claude", "dist", "build", "target", ".tox"}
TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")


def devops_answers(text: str) -> list[str] | None:
    """The Answer cells of the DevOps section's table, or None when there is no DevOps section."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^#{2,3}\s+DevOps\b", l.strip(), re.I)), None)
    if start is None:
        return None
    level = len(lines[start].strip()) - len(lines[start].strip().lstrip("#"))
    answers = []
    for line in lines[start + 1:]:
        heading = re.match(r"^(#{1,6})\s", line.strip())
        if heading and len(heading.group(1)) <= level:
            break
        row = TABLE_ROW.match(line)
        if not row:
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        if len(cells) < 2 or set(cells[1]) <= set("-: ") or cells[1].lower() == "answer":
            continue
        answers.append(cells[1])
    return answers


def chosen_tools(answers: list[str]) -> list[str]:
    text = " ".join(answers).lower().replace("-", " ")
    return [tool for tool, spec in TOOLS.items() if any(re.search(n, text) for n in spec["names"])]


def project_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        files = [f for f in out.splitlines() if f]
    except (OSError, subprocess.CalledProcessError):
        files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    return sorted(f for f in files if not SKIP_DIRS.intersection(f.split("/")[:-1]))


def matches(rel: str, globs) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(rel, g) if "/" in g else fnmatch.fnmatchcase(name, g) for g in globs)


def tool_files(root: Path, files: list[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for tool, spec in TOOLS.items():
        hits = [f for f in files if matches(f, spec.get("files", []))]
        if "content" in spec:
            globs, pattern = spec["content"]
            rx = re.compile(pattern)
            for f in files:
                if matches(f, globs):
                    try:
                        if rx.search((root / f).read_text(encoding="utf-8", errors="ignore")[:200_000]):
                            hits.append(f)
                    except OSError:
                        continue
        if hits:
            found[tool] = sorted(set(hits))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_root")
    ap.add_argument("--strict", action="store_true", help="also fail when an agreed tool has no files yet")
    args = ap.parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"not a folder: {root}"}))
        return 2

    arch = spine_mod.architecture_file(root)
    result: dict = {"architecture": arch.as_posix()}
    if not arch.is_file():
        print(json.dumps({**result, "status": "no_architecture",
                          "message": "No architecture.md: no DevOps stack agreed yet (Da Vinci's principles, capability AP)."}, indent=2))
        return 0
    answers = devops_answers(arch.read_text(encoding="utf-8"))
    if answers is None:
        print(json.dumps({**result, "status": "no_devops_section",
                          "message": "architecture.md has no DevOps section yet: Da Vinci's principles round asks for it."}, indent=2))
        return 0

    chosen = chosen_tools(answers)
    checked = sorted({TOOLS[t]["category"] for t in chosen})
    found = tool_files(root, project_files(root))
    off_stack = [{"tool": t, "category": TOOLS[t]["category"], "files": fs,
                  "agreed": [c for c in chosen if TOOLS[c]["category"] == TOOLS[t]["category"]]}
                 for t, fs in found.items() if TOOLS[t]["category"] in checked and t not in chosen]
    missing = [t for t in chosen if t not in found]
    failed = bool(off_stack) or (args.strict and bool(missing))
    result.update({
        "status": "off_stack" if off_stack else ("missing" if failed else "compliant"),
        "agreed": {c: [t for t in chosen if TOOLS[t]["category"] == c] for c in checked},
        "unchecked": sorted({"ci", "cd", "iac"} - set(checked)),
        "found": {t: fs for t, fs in found.items() if t in chosen},
        "off_stack": off_stack,
        "missing": missing,
    })
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
