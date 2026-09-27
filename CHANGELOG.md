# Changelog

## 1.5.0 — 2026-09-28

### Scrooge McDuck

- **Scrooge is now a memory agent.** On first talk he builds a sanctum at `_bmad/memory/agent-scrooge/` (identity files, session logs, `estimates.md`) and remembers your currency, pricing region, rate card and spending choices. Existing `stories.json` and `savings.json` there are kept. Capability prompts and scripts stay in the skill; `wake.py` lists them each session, so later kit updates need no sanctum migration.
- **Cost estimates (CE).** Prices the solution from the BMad artifacts (spine, spec, epics, sprint status, plus anything you give him) into `<name>.xlsx` in the new `cost_estimates_folder` (default `docs/cost_estimates`): an Overall sheet with inputs (days of delivery, working days per month, hours per month, months of run, contingency, exchange rate), a team table (employees × days × allocation = mandays, priced from the rate card) and a cost summary of delivery, run and grand totals; one sheet per environment; Rate Card; Other Costs; Sources & Gaps. All totals are formulas with named inputs.
  - `azure_prices.py` looks up Azure list prices from the public Retail Prices API with meter id and date.
  - `build_estimate.py` builds the workbook from a cited model (`<name>.estimate.json`), refuses a line whose citation doesn't resolve, an unpriced line or a role missing from the rate card, prints the same figures it writes as formulas, stamps the cited files and rate card for `--drift`, and won't overwrite a hand-edited workbook without `--force`.
- **Project close-out (PC).** How long the project took (`project_timeline.py`: BMad stages from git, custom agents from their sanctums, epics and stories from the sprint status's git history, Claude work items from the ledger; calendar and working days) and total Claude API calls costed at the list prices read from Anthropic's pricing page (`claude_prices.py`), added to the workbook as Claude Usage, Claude Usage Detail, Claude Prices and Project Timeline sheets and a cost-summary line (a memo on a subscription). The ledger gains `claude_usage.csv` (tokens by type per work item and model, first and last call) and attributes Leonardo's work to its own phase.
- **Dashboard-ready.** Every data range is a named Excel table; `<name>.facts.csv` holds the cost lines as plain values for Power BI.
- **Rate card (RT). `rate-card.json` in the sanctum: currency, source, date and a day rate per role, changed only with figures you give.

### Leonardo da Vinci

- **High-Level and Low-Level Design documents (DS).** Writes `hld.docx` and `lld-<component>.docx` in the new `design_docs_folder` (default `docs/architecture/design`) from a cited model (`<name>.doc.json`) with `build-docx.py`: cover and document control, table of contents, numbered sections following the outline, every block cited, open points where they arise and in Appendix A, Appendix B traceability (ADs cited per section and ADs not cited), and the current diagrams embedded from their PNG exports. It challenges gaps before writing, as for diagrams.
- **Confluence.** Start from an existing HLD/LLD page (its headings can become the project's outline; its statements are verified against the BMad artifacts, never cited) and publish the document to Confluence as a new or updated page through the Atlassian MCP server, only after the user confirms and never over an unseen edit. `build-docx.py --formats confluence` writes the same build as Markdown for the page; `spine.py` reports the project's `confluence_wiki_url`.
- Org-default outlines in `assets/design-docs/hld.md` and `lld.md`. A project's own `templates/hld.md`, `lld.md` and `reference.docx` (Word styles, header, footer) in the design docs folder replace them, so the org's template drops in without code changes.
- The build refuses an outline section left out, a cite that doesn't resolve, a stale diagram or one from another spine, and won't replace a `.docx` changed since the last build without `--force`.
- `diagram-drift.py` checks design documents too (under `documents`); `spine.py` reports the design docs folder, its documents and which outlines and Word template apply.

### Jules and the governance questionnaires

- **`CloudAssessment.docx` is now `TechnicalArchitectureAssessment.docx`**, and the Criticality Assessment's 19 questions moved into it as questions 5–23 (after the 4 platform questions). `CriticalityAssessment.docx` is gone.
- **New `DataGovernancePrivacyAssessment.docx`**: 10 questions on personal data, purpose and lawful basis, classification, residency and cross-border transfer, retention, ownership and access, protection, third parties, data subject rights, and DPIA and breach handling.
- **New `EnterpriseAIRiskAssessment.docx`**: 20 questions for solutions that use AI: type of AI, models and inventory, use case, impact and high-impact decisions, risk rating, accountability, human oversight, kill switch, data, privacy, bias testing, disclosure, explainability, opt-out and redress, validation, monitoring, updates, third-party AI, security, and risk-framework integration. Many are drawn from the CBUAE Guidance Note on Consumer Protection and Responsible Adoption and Use of AI (issued 11/2/2026), sections 2–9.
- Jules routes each question to the lead who signs it, since each questionnaire now mixes Product Lead and Tech Lead questions.
- **Jules and Scrooge are offered at the right moments.** When `bmad-architecture` completes, its override's `on_complete` asks once whether Jules should fill in the three assessments and whether Scrooge should price the solution. When `bmad-build` or `bmad-build-auto` completes and every epic and story in the sprint status is done (and no close-out exists yet), it offers Scrooge's project close-out. Each agent starts only on a yes, with a fresh session (`/clear`) suggested. Projects that already have these `_bmad/custom` files get the lines to merge from `org-setup`, which never replaces their files.
- **Custom templates.** Jules asks (at First Breath, and before answering until the owner has said) whether the organisation has its own governance templates, and asks for them in the governance folder, stating whether they replace the standard three or come in addition. Jules tells the owner it's trained on the three standard templates, and ports similar questions over: each custom question is matched to the standard question asking the same thing, and its answer carries over with re-checked evidence and a note naming the source question. Only unmatched questions are answered from scratch. `questionnaire.py` now finds the question table even when a template opens with a cover or document-control table.
- **Jules answers all three assessments** when asked, in one session (Technical Architecture, Data Governance & Privacy, then Enterprise AI Risk), unless a single questionnaire is named. The AI assessment is answered even without AI, stating so from the artifacts. The hand-back is one list per lead across all three, plus any answers that disagree between questionnaires.
- **Upgrading a project:** `org-setup` copies the three new files but never deletes; the old `CloudAssessment.docx` and `CriticalityAssessment.docx` stay in the governance folder until you remove them.

### Kit

- New settings `cost_estimates_folder` and `design_docs_folder`; `bmad-help` lists CE, RT and DS.

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
