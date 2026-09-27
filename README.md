# Org Kit (`org`)

A BMad module that adds the organisation layer to any BMad Method (`bmm`) project:

- **Org standards baselines** — `azure.md`, `terraform.md`, `security.md` and `coding-style.md` (org baseline 1.0.0). Projects copy them and extend them with their own names, rules and accepted exceptions.
- **Blank governance questionnaires** — `CriticalityAssessment.docx` and `CloudAssessment.docx`.
- **BMad customization overrides** — the dev agent and the architecture, build, code-review and test-design workflows load the project's standards as persistent facts; epics-and-stories uses the org's hybrid story structure and offers to sync to the project's Jira.
- **Scrooge McDuck (`agent-scrooge`), Token Usage Accountant** — counts every API call in the project's Claude Code logs, attributes it to a story (by the project's Jira key) or planning phase, a step and an activity, writes a gitignored ledger, and sternly audits it for savings. Background hooks keep the ledger current.
- **Jules (`agent-jules`), IT Governance** — drafts, coaches and routes the Criticality and Cloud Assessment answers for the Product Lead and Tech Lead from the project's BMad artifacts, replies to reviewer comments and checks answers for drift.

Version 1.1.0. Expansion of BMad Method.

## Contents

```text
skills/
  agent-jules/          # Jules: SKILL.md, sanctum templates, capability prompts, scripts (+ tests)
  agent-scrooge/        # Scrooge: SKILL.md, capability prompts, token_report.py (+ tests)
  org-setup/            # setup skill: standards, questionnaires, overrides, skill links, tooling check
    assets/
      module.yaml       # module identity, agent roster, config questions
      module-help.csv   # capabilities for bmad-help
      standards/        # org baselines copied into the project's standards folder
      governance/       # blank questionnaires copied into the governance folder
      custom/           # _bmad/custom/*.toml override templates
    scripts/            # install-org-assets (+ tests)
.claude-plugin/marketplace.json
```

## Install into a project

Prerequisites: BMad Method installed in the project (`_bmad/`), [`uv`](https://docs.astral.sh/uv/), and ideally the Atlassian MCP server (Jira sync) and the safe-docx MCP server (Jules's tracked changes and comment replies).

1. Install the kit as a module with the BMad installer, from `https://github.com/darrel1234/bmad-org-kit`. The installer asks the questions below, writes them to `[modules.org]` in `_bmad/config.toml`, and registers Jules and the capabilities in `bmad-help`.
2. Run the setup skill ("setup Org Kit"). It copies the standards and blank questionnaires, writes the `_bmad/custom` overrides and checks the tooling. Nothing the project already has is overwritten.
3. The questions (asked by the installer; `org-setup` asks them itself only when the kit was added without the installer):

   | Key | Asks for | Default |
   | --- | --- | --- |
   | `jira_site` | Jira site, `https://<site>.atlassian.net` | required |
   | `jira_project_key` | Jira project key (`^[A-Z][A-Z0-9]+$`) | required |
   | `confluence_wiki_url` | project wiki page | optional |
   | `governance_folder` | where the questionnaires live | `{project-root}/docs/governance` |
   | `standards_folder` | where the standards live | `{project-root}/docs/standards` |
   | `token_usage_folder` | where Scrooge writes the token ledger (gitignored) | `{project-root}/docs/token_usage` |

4. Talk to Jules. On first activation Jules builds its sanctum at `_bmad/memory/agent-jules/` and picks up the governance and standards folders from the `org` config.

## What setup does

1. Reads the `[modules.org]` values the BMad installer wrote to `_bmad/config.toml` (install the kit as a module from its GitHub repository first; the installer registers Jules and the `bmad-help` entries). It never writes installer-managed files or deletes anything under `_bmad/`.
2. Copies the standards baselines into `standards_folder` and the blank questionnaires into `governance_folder`. Existing files are never overwritten; skipped files are reported.
3. Writes `_bmad/custom/<skill>.toml` overrides only where no file exists yet. For an existing file it shows the lines to add so you can merge them yourself.
4. Links the kit's skills into `.claude/skills/` (relative symlinks; `copy` or `skip` on request).
5. Adds the token ledger folder to `.gitignore` and Scrooge's background refresh hooks to `.claude/settings.local.json` (skip with `--no-hooks`).
6. Checks for `uv`, the Atlassian MCP server and the safe-docx MCP server, and says how to add any that are missing.

Setup runs a dry run first and shows you what it would change.

## Capabilities

| Code | Skill | Capability |
| --- | --- | --- |
| SU | org-setup | Set up or reconfigure the Org Kit |
| AQ | agent-jules | Answer a questionnaire |
| CL | agent-jules | Coach the Product Lead or Tech Lead |
| RC | agent-jules | Reply to reviewer comments |
| CW | agent-jules | Comment watch (pulse) |
| DR | agent-jules | Drift check |
| AL | agent-jules | Answer library |
| RF | agent-scrooge | Refresh the token ledger |
| SC | agent-scrooge | What a story or phase cost |
| CD | agent-scrooge | Cost drivers and savings audit |
| CL | agent-scrooge | Story cost line for PRs and Jira |

## Updating

- Update the kit through the BMad installer (it refreshes the `org` config and help entries), then run `org-setup` again for any new project files.
- Standards, questionnaires and overrides that already exist in the project are left alone, so project extensions survive. To adopt a newer baseline, diff your copy against `skills/org-setup/assets/standards/` and merge by hand; each baseline carries its version in its header.
- Jules's sanctum (`_bmad/memory/agent-jules/`) is never touched by an update. Sanctum files are created at First Breath from the templates, so template changes reach an existing sanctum only by hand.
- Scrooge's project data (`_bmad/memory/agent-scrooge/stories.json`, `savings.json`) is never touched by an update.

## Developing the kit

```bash
uv run skills/org-setup/scripts/tests/test-install-org-assets.py
for t in skills/agent-jules/scripts/tests/*.py; do uv run "$t"; done
uv run --with pytest pytest -q skills/agent-scrooge/scripts/tests
```

Validate the module with the BMad Module Builder's Validate Module (VM) path on `skills/`.

## License

TODO (owner to choose).
