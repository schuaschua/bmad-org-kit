# Changelog

## 1.4.1 — 2026-09-27

### Leonardo da Vinci

- **Nothing overlaps.** New drawing rule, enforced by the build: every label is measured and wrapped where it was measured, every arrow is routed in its own lane between rows (long arrows through channels clear of boxes and headers), arrow labels sit on their own path clear of everything else, and a box's contents start right of the headers above them. A final check tests every pair of texts, icons, boxes, headers and arrow paths; the build spreads the layout until it's clean and refuses to write a diagram that still collides. Layout is never squeezed to save paper: when the chosen paper would print too small, the build suggests the smallest readable paper (A4, A3, A2; one or two pages).
- **Stricter checks.** A cited spec or UX section must exist in its file (`SPEC.md §9.9` no longer passes when there is no 9.9). The spine is read more carefully: an AD is defined only by a heading or a bold id, so a sentence that mentions another AD no longer splits or steals it (diagrams of spines that had such lines may report drift once). Data services (databases, storage) are refused inside a compute cluster or its subnet.
- **Challenge step:** writes the model first and records deferred points as gaps straight away, asks after each round whether to keep going or draw, and on a redraw raises only what changed since the diagram was drawn.
- **Smaller fixes:** sequence participants ordered by first appearance; the sequence reference carries its own PII/PHI rule; the setup script reports the next free AD number and the user's name and language.
- **Evaluation cases** (`skills/leonardo-da-vinci/evals/`): three burdeebur.com cases for `bmad-eval-runner` (challenge before drawing, draw two regions by the org rules, name the ADs a drift changed). Running them needs `ANTHROPIC_API_KEY`.

### Kit

- `.gitignore` covers builder review runs (`.analysis/`).

## 1.4.0 — 2026-09-27

### Changed

- **`arch-diagrams` is now Leonardo da Vinci (`leonardo-da-vinci`).** Same skill, new name: ask for "Leonardo" or any diagram. The `bmad-help` entries (DG, DD), the plugin manifest, org-setup and Jules's diagram citation all use the new name. Diagrams drawn with 1.3.0 keep working, including their drift check.
- **Upgrading a project from 1.3.0:** update the kit through the BMad installer (it installs `leonardo-da-vinci`), then delete the old `.claude/skills/arch-diagrams` folder if it's still there.

### Fixed

- `org-setup` no longer lists every skill in `.claude/skills` (BMad's included) as the kit's when the BMad installer has already installed the kit there; it reports the skills as installed in place.

### Docs

- README: the verified install command, `npx bmad-method install --custom-source https://github.com/darrel1234/bmad-org-kit`, with the flags for a prompt-free install.

## 1.3.0 — 2026-09-27

### Added

- **`arch-diagrams` skill** (built with BMad Builder's `bmad-workflow-builder`): draws cited draw.io diagrams from the architecture spine, spec and UX docs only: C4 system context, C4 containers, cloud deployment, data flow with trust boundaries and PII/PHI, and a sequence for a named flow.
  - Challenges the user on gaps, contradictions and risky choices before drawing; approved answers are added to the spine as AD text.
  - Every element cites its AD or section; `build-drawio.py` validates each citation against the spine and sources before drawing, and gaps are listed on the page, never drawn.
  - Diagram models (`<name>.model.json`) sit beside the `.drawio` files; layered layout; page size and orientation asked (default A4 portrait), fitted to one or two pages.
  - Deployment drawing rules: workload hosts (AKS) as boxes with their icon, container icons for workloads, data services in their own subnet outside clusters, multi-region as one set of boxes per region inside one enclosing box.
  - Stencil catalogues from draw.io's shape index: Azure (645) and Kubernetes (39); more providers via `stencils.py extract`.
  - Stamp (spine commit or date, AD hashes) on every file; `diagram-drift.py` names the ADs that changed and exits 1 when a diagram is stale.
  - PNG/SVG exports with draw.io desktop; optional previews with the draw.io MCP server.
- **`diagrams_folder`** setting (default `docs/architecture/diagrams`); `org-setup` links the new skill, lists it in `bmad-help` (DG, DD) and checks for draw.io desktop and the draw.io MCP server.
- **Jules** may cite a current architecture diagram in a Cloud Assessment answer, beside the AD it was drawn from.

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
