#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Unit tests for install-org-assets.py against a throwaway project root.

Run from the skill root: uv run scripts/tests/test-install-org-assets.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent.parent
SCRIPT = SKILL / "scripts" / "install-org-assets.py"


def run(*args: str) -> tuple[int, dict]:
    out = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return out.returncode, json.loads(out.stdout)


class InstallOrgAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.tmp.name).resolve()
        (self.root / "_bmad").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def base_args(self, *extra: str) -> list[str]:
        return [
            "--project-root", str(self.root),
            "--standards-folder", "{project-root}/docs/standards",
            "--governance-folder", "{project-root}/docs/governance",
            "--jira-site", "https://example.atlassian.net/",
            "--jira-project-key", "PROJ",
            "--skills-mode", "skip",
            *extra,
        ]

    def test_fresh_install_copies_everything(self):
        code, out = run(*self.base_args())
        self.assertEqual(code, 0, out)
        for name in ["azure.md", "terraform.md", "security.md", "coding-style.md"]:
            self.assertTrue((self.root / "docs" / "standards" / name).is_file(), name)
        for name in ["CloudAssessment.docx", "CriticalityAssessment.docx"]:
            self.assertTrue((self.root / "docs" / "governance" / name).is_file(), name)
        custom = self.root / "_bmad" / "custom"
        self.assertEqual(len(out["overrides"]["written"]), 7)
        dev = tomllib.loads((custom / "bmad-agent-dev.toml").read_text(encoding="utf-8"))
        self.assertEqual(dev["agent"]["persistent_facts"], ["file:docs/standards/*.md"])
        epics = tomllib.loads((custom / "bmad-create-epics-and-stories.toml").read_text(encoding="utf-8"))
        self.assertIn("Jira project PROJ (https://example.atlassian.net)", epics["workflow"]["on_complete"])
        self.assertEqual(len(epics["workflow"]["persistent_facts"]), 1)

    def test_never_overwrites_existing_files(self):
        standards = self.root / "docs" / "standards"
        standards.mkdir(parents=True)
        (standards / "azure.md").write_text("project version", encoding="utf-8")
        custom = self.root / "_bmad" / "custom"
        custom.mkdir()
        (custom / "bmad-build.toml").write_text("# mine\n", encoding="utf-8")
        code, out = run(*self.base_args())
        self.assertEqual(code, 0, out)
        self.assertEqual((standards / "azure.md").read_text(encoding="utf-8"), "project version")
        self.assertIn(str(standards / "azure.md"), [s["file"] for s in out["standards"]["skipped"]])
        self.assertEqual((custom / "bmad-build.toml").read_text(encoding="utf-8"), "# mine\n")
        existing = {Path(e["file"]).name: e["suggested"] for e in out["overrides"]["existing"]}
        self.assertIn("file:docs/standards/*.md", existing["bmad-build.toml"])

    def test_dry_run_writes_nothing(self):
        code, out = run(*self.base_args("--dry-run"))
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / "docs").exists())
        self.assertFalse((self.root / "_bmad" / "custom").exists())
        self.assertEqual(len(out["standards"]["copied"]), 4)

    def test_links_skills_once(self):
        args = [a for a in self.base_args() if a not in ("--skills-mode", "skip")]
        code, out = run(*args)
        self.assertEqual(code, 0, out)
        link = self.root / ".claude" / "skills" / "org-setup"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), SKILL)
        code, again = run(*args)
        self.assertEqual(again["skills"]["installed"], [])
        self.assertTrue(all(s["reason"] == "already installed from this kit" for s in again["skills"]["skipped"]))

    def test_rejects_bad_project_key(self):
        args = self.base_args()
        args[args.index("PROJ")] = "proj"
        code, out = run(*args)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "error")

    def test_rejects_unresolved_project_root(self):
        args = self.base_args()
        args[1] = "{project-root}"
        code, out = run(*args)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
