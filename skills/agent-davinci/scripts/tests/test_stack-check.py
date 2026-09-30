#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Unit tests for stack-check.py (stdlib unittest).

Run from the skill root: uv run scripts/tests/test_stack-check.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arch_fixtures import *  # noqa: E402,F403

ARCH = """# Architecture: chat

## Context

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| 1 | Environment | Cloud, uses Bicep-free Azure | owner |

## DevOps

| Item | Answer | Source |
| --- | --- | --- |
| CI | Jenkins | owner |
| CD / GitOps | Argo CD, pull-based | owner |
| Source control and branching | GitHub, trunk-based | owner |
| Infrastructure as code | Terraform | owner |

## Principles
"""


class StackCheckTests(Project):
    def write(self, rel: str, text: str = "x\n") -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_no_architecture_passes_quietly(self):
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual((code, out["status"]), (0, "no_architecture"))

    def test_no_devops_section(self):
        self.write("docs/architecture/architecture.md", "# Architecture\n\n## Principles\n")
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual((code, out["status"]), (0, "no_devops_section"))

    def test_compliant_project(self):
        self.write("docs/architecture/architecture.md", ARCH)
        self.write("Jenkinsfile")
        self.write("infra/main.tf")
        self.write("deploy/app.yaml", "apiVersion: argoproj.io/v1alpha1\nkind: Application\n")
        code, out = run("stack-check.py", str(self.root), "--strict")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["agreed"], {"cd": ["argocd"], "ci": ["jenkins"], "iac": ["terraform"]})
        self.assertEqual(out["found"]["terraform"], ["infra/main.tf"])
        self.assertEqual(out["unchecked"], [])

    def test_off_stack_tools_fail(self):
        self.write("docs/architecture/architecture.md", ARCH)
        self.write(".github/workflows/ci.yml")
        self.write("infra/main.bicep")
        self.write("infra/main.tf")
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual(code, 1, out)
        off = {o["tool"]: o for o in out["off_stack"]}
        self.assertEqual(set(off), {"github-actions", "bicep"})
        self.assertEqual(off["bicep"]["agreed"], ["terraform"])
        self.assertEqual(off["github-actions"]["files"], [".github/workflows/ci.yml"])

    def test_missing_fails_only_when_strict(self):
        self.write("docs/architecture/architecture.md", ARCH)
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual((code, out["status"]), (0, "compliant"))
        self.assertEqual(set(out["missing"]), {"jenkins", "argocd", "terraform"})
        code, out = run("stack-check.py", str(self.root), "--strict")
        self.assertEqual((code, out["status"]), (1, "missing"))

    def test_unnamed_category_is_unchecked(self):
        self.write("docs/architecture/architecture.md",
                   "# A\n\n## DevOps\n\n| Item | Answer | Source |\n| --- | --- | --- |\n| CI | GitHub Actions | owner |\n")
        self.write("infra/main.bicep")
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual(code, 0, out)
        self.assertEqual(out["unchecked"], ["cd", "iac"])

    def test_ignores_dependency_and_gitignored_folders(self):
        self.write("docs/architecture/architecture.md", ARCH)
        self.write("node_modules/pkg/main.bicep")
        self.write("scratch/old.bicep")
        self.write(".gitignore", "scratch/\n")
        self.git("init", "-q")
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual(code, 0, out)

    def test_config_architecture_folder(self):
        (self.root / "_bmad").mkdir()
        (self.root / "_bmad/config.toml").write_text('[modules.org]\narchitecture_folder = "arch"\n', encoding="utf-8")
        self.write("arch/architecture.md", ARCH)
        self.write("stack.bicep")
        code, out = run("stack-check.py", str(self.root))
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
