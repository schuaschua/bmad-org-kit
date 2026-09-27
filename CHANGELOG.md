# Changelog

## 1.2.0 — 2026-09-27

### Added

- **Region setting.** New `region` question at kit setup (`none` | `uae`, default `none`), stored under `[modules.org]`. `org-setup` shows the chosen region's regulatory documents in its summary.
- **Regional regulation registry** (`skills/agent-jules/assets/regions.toml`) and resolver (`skills/agent-jules/scripts/region-sources.py`, with tests). `uae` points to the CBUAE Rulebook's Guidelines for Financial Institutions Adopting Enabling Technologies and its Guidance Note on Consumer Protection and Responsible Adoption and Use of Artificial Intelligence.
- **Jules considers the region's regulation.** New source tier in the CREED: Jules reads the region's documents only on the regulator's listed domains, cites the clause with URL and dates in the reasoning note, keeps the requirement apart from the project's own commitments and never claims compliance. New standing order *Regulatory source dates*: each document's date is recorded in the sanctum's `regulatory-sources.md` and re-checked on first use each session; a changed date is reported and flags the citing answers for drift check.

### Upgrading an existing Jules

A sanctum created before 1.2.0 keeps its own copies, so carry these over by hand into `_bmad/memory/agent-jules/`:

- `CREED.md`: from `skills/agent-jules/assets/CREED-template.md`, the *Stay inside the fence* value, source-order tier 2 (and renumbered tiers 3–5), the regional-source sentence in *Reasoning note on everything*, the *Regulatory source dates* standing order, the *Never claim regulatory compliance* boundary, the *Waving at a regulation* anti-pattern and the second web line under *Read Access*.
- `INDEX.md`: the `regulatory-sources.md` line under *My Files*.
- `references/answer-questionnaire.md` and `references/drift-check.md`: copy from `skills/agent-jules/references/`.

Then set `region` (rerun `org-setup` after updating through the BMad installer, or add it under `[modules.org]` in `_bmad/custom/config.toml`).

## 1.1.0

- **Scrooge McDuck (`agent-scrooge`), Token Usage Accountant** (PR #1): token usage ledger from the project's Claude Code logs, attributed to stories and planning phases, with background refresh hooks and a `token_usage_folder` setting.

## 1.0.0

Initial release: org standards baselines, blank governance questionnaires, BMad customization overrides with Jira sync, and Jules (IT Governance).
