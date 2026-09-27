# Org Kit (`org`)

A BMad module that adds the organisation layer to any BMad Method (`bmm`) project:

- **Org standards baselines** — `azure.md`, `terraform.md`, `security.md` and `coding-style.md` (org baseline 1.0.0). Projects copy them and extend them with their own names, rules and accepted exceptions.
- **Blank governance questionnaires** — `CriticalityAssessment.docx` and `CloudAssessment.docx`.
- **BMad customization overrides** — the dev agent and the architecture, build, code-review and test-design workflows load the project's standards as persistent facts; epics-and-stories uses the org's hybrid story structure and offers to sync to the project's Jira.
- **Scrooge McDuck (`agent-scrooge`), Token Usage Accountant** — counts every API call in the project's Claude Code logs, attributes it to a story (by the project's Jira key) or planning phase, a step and an activity, writes a gitignored ledger, and sternly audits it for savings. Background hooks keep the ledger current.
- **Architecture diagrams (`arch-diagrams`)** — draws draw.io diagrams (C4 context, C4 containers, cloud deployment with Azure and Kubernetes icons, data flow with trust boundaries and PII/PHI, sequence for a named flow) from the project's architecture spine, spec and UX docs only. Every box and arrow cites its AD or section, gaps are listed rather than drawn, it challenges the architecture before drawing, and a drift check flags diagrams older than their spine.
- **Jules (`agent-jules`), IT Governance** — drafts, coaches and routes the Criticality and Cloud Assessment answers for the Product Lead and Tech Lead from the project's BMad artifacts, replies to reviewer comments and checks answers for drift. Jules also considers the regulatory documents of the region the solution is developed in, chosen at setup, citing the clause it relies on and checking each document's date before relying on it.

Version 1.3.0 (see [CHANGELOG.md](CHANGELOG.md)). Expansion of BMad Method.

## Contents

```text
skills/
  agent-jules/          # Jules: SKILL.md, sanctum templates, capability prompts, scripts (+ tests)
    assets/regions.toml # regional regulation registry: region -> regulator, web domains, source documents
  agent-scrooge/        # Scrooge: SKILL.md, capability prompts, token_report.py (+ tests)
  arch-diagrams/        # SKILL.md, per-diagram-type references, stencil catalogues, spine/build/drift/stencil scripts (+ tests)
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
   | `diagrams_folder` | where arch-diagrams writes `.drawio` files, their models and exports | `{project-root}/docs/architecture/diagrams` |
   | `region` | region the solution is developed in (`none`, `uae`); picks the regulatory documents Jules considers | `none` |

4. Talk to Jules. On first activation Jules builds its sanctum at `_bmad/memory/agent-jules/` and picks up the governance and standards folders from the `org` config.

## What setup does

1. Reads the `[modules.org]` values the BMad installer wrote to `_bmad/config.toml` (install the kit as a module from its GitHub repository first; the installer registers Jules and the `bmad-help` entries). It never writes installer-managed files or deletes anything under `_bmad/`.
2. Copies the standards baselines into `standards_folder` and the blank questionnaires into `governance_folder`. Existing files are never overwritten; skipped files are reported.
3. Writes `_bmad/custom/<skill>.toml` overrides only where no file exists yet. For an existing file it shows the lines to add so you can merge them yourself.
4. Links the kit's skills into `.claude/skills/` (relative symlinks; `copy` or `skip` on request).
5. Adds the token ledger folder to `.gitignore` and Scrooge's background refresh hooks to `.claude/settings.local.json` (skip with `--no-hooks`).
6. Shows the chosen region and its regulatory documents.
7. Checks for `uv`, the Atlassian MCP server, the safe-docx MCP server, draw.io desktop (diagram exports) and the draw.io MCP server (diagram previews), and says how to add any that are missing.

Setup runs a dry run first and shows you what it would change.

## Architecture diagrams

Ask for a diagram ("draw the deployment diagram", "C4 containers", "sequence diagram for one chat turn"). The skill reads the spine at `_bmad-output/planning-artifacts/architecture/<name>/ARCHITECTURE-SPINE.md` with the spec and UX docs, and nothing else.

- **Challenge first.** Before drawing it puts the gaps, contradictions and risky choices to you, most consequential first. Each answer becomes proposed AD wording, which it adds to the spine only once you approve the exact text, so the diagram can cite it.
- **Cited, not guessed.** Each diagram has a `<name>.model.json` beside its `.drawio`, listing every element with its citation and the gaps. The build refuses an element whose citation doesn't resolve to a real AD or source section, and a gap is listed on the page, never drawn.
- **Org drawing rules** (deployment): a service that hosts workloads, such as AKS, is a box with its icon; workloads inside it use a container icon; data services sit outside compute clusters in their own subnet; multi-region is one set of boxes per region (two when the spine doesn't count them) inside one enclosing box.
- **Icons** come from draw.io's own shape libraries: `skills/arch-diagrams/assets/stencils/azure.json` (645 Azure stencils) and `kubernetes.json`. Another provider is one command away: `uv run skills/arch-diagrams/scripts/stencils.py extract --index <draw.io search-index.json> --provider aws --prefix mxgraph.aws4.`.
- **Paper.** It asks for size and orientation (default A4 portrait) and fits the diagram to one page or two.
- **Stamped and checked for drift.** Each file records the spine's commit (or date) and a hash of every AD. `uv run skills/arch-diagrams/scripts/diagram-drift.py <project-root>` names the ADs that changed and exits 1 when a diagram is stale, so it also works as a CI or pre-commit check.
- **Exports** (PNG, SVG) need draw.io desktop; the draw.io MCP server (`claude mcp add drawio -- npx -y @drawio/mcp`) adds an in-browser preview. Neither is required.

Jules may cite a current diagram in a Cloud Assessment answer, beside the AD it was drawn from.

## Regions

The `region` setting points Jules at the regulator's documents for where the solution is developed. Jules reads the setting fresh each session (`uv run skills/agent-jules/scripts/region-sources.py <project-root>`), so changing it takes effect at once: rerun `org-setup`, or set `region` under `[modules.org]` in `_bmad/custom/config.toml`.

| Region | Regulator | Documents |
| --- | --- | --- |
| `none` | — | none |
| `uae` | Central Bank of the UAE | [Guidelines for Financial Institutions Adopting Enabling Technologies](https://rulebook.centralbank.ae/en/rulebook/guidelines-financial-institutions-adopting-enabling-technologies) (every solution); [Guidance Note on Consumer Protection and Responsible Adoption and Use of Artificial Intelligence](https://rulebook.centralbank.ae/en/rulebook/guidance-note-consumer-protection-and-responsible-adoption-and-use-artificial-intelligence) (solutions that use AI) |

When a question touches something a source governs, Jules reads the document on the regulator's own site, cites the clause with its URL and dates in the reasoning note, and keeps the regulator's requirement apart from what the project's artifacts commit to; it never claims the project complies. It records each document's date in its sanctum (`regulatory-sources.md`) and re-checks it on first use each session; a changed date is reported to you and flags the answers citing it for a drift check.

To add a region, add a `[regions.<code>]` table to `skills/agent-jules/assets/regions.toml` and the same code to the `region` choices in `skills/org-setup/assets/module.yaml`; the tests check the two match.

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
| DG | arch-diagrams | Draw an architecture diagram |
| DD | arch-diagrams | Diagram drift check |

## Updating

- Update the kit through the BMad installer (it refreshes the `org` config and help entries), then run `org-setup` again for any new project files.
- Standards, questionnaires and overrides that already exist in the project are left alone, so project extensions survive. To adopt a newer baseline, diff your copy against `skills/org-setup/assets/standards/` and merge by hand; each baseline carries its version in its header.
- Jules's sanctum (`_bmad/memory/agent-jules/`) is never touched by an update. Sanctum files and its copies of the capability prompts are created at First Breath, so template and prompt changes reach an existing sanctum only by hand; CHANGELOG.md lists what to carry over for each release.
- Scrooge's project data (`_bmad/memory/agent-scrooge/stories.json`, `savings.json`) is never touched by an update.

## Developing the kit

```bash
uv run skills/org-setup/scripts/tests/test-install-org-assets.py
for t in skills/agent-jules/scripts/tests/*.py; do uv run "$t"; done
uv run --with pytest pytest -q skills/agent-scrooge/scripts/tests
for t in skills/arch-diagrams/scripts/tests/test_*.py; do uv run "$t"; done
```

Validate the module with the BMad Module Builder's Validate Module (VM) path on `skills/`.

## License

TODO (owner to choose).
