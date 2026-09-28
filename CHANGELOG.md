# Changelog

## 1.9.0 — 2026-09-28

### Da Vinci (was Leonardo da Vinci)

- **Renamed and now an agent.** The `leonardo-da-vinci` skill is now `agent-davinci`: a memory agent like Jules and Scrooge.
  - He has a persona and a sanctum in `_bmad/memory/agent-davinci/`, and remembers the principles you held firm on, the gaps you deferred and your drawing preferences.
  - He is registered in the module's agent roster.
  - His capabilities are AP (architecture principles), DG (draw), DS (design document) and DD (drift check).
- **Architecture principles (AP).** Before `bmad-architecture` begins, Da Vinci settles the architecture questions and guardrails with you, confirms a summary, and writes `docs/architecture/architecture.md` plus one file per cloud provider you name (`azure.md`, `aws.md` ...).
  - He first reads the brief, spec, PRD, regulator documents and any policies in `docs/architecture/` (not the kit's org standards), and never asks what they already answer; he records those answers with their source.
  - He then asks the rest of fifteen architecture questions, in order:
    - environment (cloud, hybrid or on-premises), the cloud platforms and the service model (IaaS or PaaS);
    - a 1 to 6 ranking of the Well-Architected pillars;
    - existing architecture policies: if you have them, put them in `docs/architecture/`, and questions 6 to 15 are then answered from them first;
    - naming convention per provider (suggesting `<orgname>-<region>-<appname>-<resourceType>-<number>`) and tags;
    - regions and availability, on-premises integration and its network link, and AI use, maturity and data quality;
    - the environments and how strict the rules between them are, and the architecture style;
    - for a migration, comfort with AI carrying it out;
    - the security level (Very strict to Relaxed), and the approved front-end, back-end, database, CI/CD and AI stack.
  - Before writing, he shows a summary of every answer (asked, or from which document), the principles and the open questions, and writes only once you confirm.
  - `architecture.md` holds the cloud-neutral answers in a Context table with their sources, the policies, the principles (`P-1` ...: testable rules with their reason, Well-Architected pillar and source) and the open questions.
  - Each provider file holds that provider's service choices, naming, tags, regions, connectivity, stack and principles. Principle numbers are unique across all the files.
- **`bmad-architecture` follows the principles.** Its override loads every `.md` in the architecture folder as persistent facts (`architecture.md` and the provider files): every AD honours each principle, or names the one it departs from and why. A new `activation_steps_prepend` stops before the architecture begins when there are no principles yet and sends you to Da Vinci. You can choose to continue without, and headless runs record the gap as an open question.
- Da Vinci's challenge before drawing, and his drift check, now also flag ADs that depart from a principle without saying why. Jules may cite a principle by number in a governance answer.
- New org config value `architecture_folder` (default `docs/architecture`), which holds `architecture.md` and the provider files. `spine.py` reports the file, whether it exists, and the other documents beside it.

### Everything under docs/

- Scrooge's defaults move to `docs/costing/`: `cost_estimates_folder` is now `docs/costing`, and `token_usage_folder` (gitignored) is now `docs/costing/token_usage`. Jules stays in `docs/governance/` and Da Vinci in `docs/architecture/`.
- Scrooge's ledger phase for Da Vinci's work is now `architecture docs (Da Vinci)`.

### Upgrading

- **Folders.** A project keeps the folders already in its config. To use the new defaults, change `token_usage_folder` and `cost_estimates_folder` in `[modules.org]`, move the files, and update the `.gitignore` entry.
- **Da Vinci's skill link.** Rerun "setup Org Kit": it links `agent-davinci`. Delete the old `.claude/skills/leonardo-da-vinci` link yourself.
- **Overrides.** In a project that already has `_bmad/custom/bmad-architecture.toml`, merge the suggested `activation_steps_prepend`, the `file:<architecture_folder>/*.md` persistent fact and the new `on_complete`.
- **Token budgets.** If `token-budgets.json` budgets the phase `diagrams & design docs (Leonardo)`, rename that key to `architecture docs (Da Vinci)`.

## 1.8.0 — 2026-09-28

### Scrooge McDuck

- **Token budgets (TB).** Once the epics and the sprint plan are done, Scrooge asks for a Claude API budget, in money, for each epic, each sprint (optional) and each planning phase still to run (test design, governance, diagrams, course corrections ...). He proposes figures from the story count and the cost per story so far; the owner sets them.
  - Who asks: the `bmad-create-epics-and-stories` override, after the Jira sync offer, when no budgets are set yet; the new `bmad-sprint-planning` override, when the sprint plan is done (or offers to review the budgets and add sprint budgets); and Scrooge on waking, when the sprint status exists and no budgets are set.
  - The budgets live in `_bmad/memory/agent-scrooge/token-budgets.json` (USD, Claude API list prices) and are copied into the estimate model in its reporting currency: `api_budget` on the epics and sprints, and the new `phase_budgets`.
- **Actual against budget in the token ledger.** `token_usage_summary_final.csv` gains `actual_usd`, `budget_usd`, `variance_usd` and `variance_pct` columns, filled once Claude's prices are saved, and one row per epic, a breakdown of All stories. A budgeted phase with no spend yet still gets a row. `report.md` gets a budget-against-actual table, and `token_report.py` prints a `budgets` list. Refreshed after every turn by the background hooks.
- **Phase Budgets sheet.** The estimate workbook has a new **Phase Budgets** sheet (`tblPhaseBudgets`, and `<name>.phases.csv`): each phase's budget against its actual from Claude Usage Detail once the close-out sheets are in, with the variance. It's a control figure, never added to a total.
- **Infrastructure OPEX file.** Every estimate build also writes `<name>.infra_cost.csv` beside the workbook, once the environments are priced from the architecture. It has each priced cloud line, each environment's total and the grand total, as daily, weekly, monthly and annual cost after go-live (annual = monthly × run months per year; year-one list prices). The build's figures carry the totals as `infra_opex`, and Scrooge reports them with the estimate.
- The close-out and refresh reports name any phase or epic over its budget. The Falcon Portal sample has phase budgets.

### Upgrading

- Setup never overwrites an existing override. `bmad-sprint-planning.toml` is new and is written as is. In a project that already has `_bmad/custom/bmad-create-epics-and-stories.toml`, rerun "setup Org Kit" and merge the suggested `on_complete`.

## 1.7.0 — 2026-09-28

### Scrooge McDuck

- **End-of-epic AI feedback (EF).** At the end of every epic the team is asked to rate the AI from 1 (very poor) to 5 (excellent). Only for a poor rating (1 or 2), a second question asks what went wrong, one or more of: AI coding standard not up to quality; AI testing standards not up to quality; AI decision-making was flawed; AI answers were not grounded in company data; Poor AI security / compliance suggestions; Other (please specify).
  - Who asks: the `bmad-build` override, after the story that finishes an epic; the new `bmad-retrospective` override, after the epic retrospective; and Scrooge on waking, for any finished epic still unrated. `bmad-build-auto` runs unattended, so it only mentions the epics waiting to be rated.
  - `ai_feedback.py` finds finished epics from the sprint status (`pending`), validates and records the answers (`record`, or `--skip` when the team declines), one row per epic, in `_bmad/memory/agent-scrooge/ai-feedback.csv`, committed with the project.
  - The close-out asks for any missing rating, adds an **AI Feedback** sheet (`tblAIFeedback`, with the average rating) to the workbook and reports the poor epics and recurring reasons.

### Leonardo da Vinci

- **Offered after the architecture.** When `bmad-architecture` finishes, its override now offers Leonardo's architecture diagrams alongside Jules's assessments and Scrooge's cost estimate (Leonardo first when Jules is chosen too, so the answers can cite the diagrams).

### Repository

- The kit moved to the `schuaschua` organisation: install with `npx bmad-method install --custom-source https://github.com/schuaschua/bmad-org-kit`. The old `darrel1234/bmad-org-kit` URL redirects.
- The "Check it's working" section of the README lists the checks to run after installing or updating: overrides, skill paths, `uv`, and when each prompt should appear.

### Upgrading

- Setup never overwrites an existing override. In a project that already has `_bmad/custom/bmad-architecture.toml`, `bmad-build.toml` or `bmad-build-auto.toml`, rerun "setup Org Kit" and merge the suggested `on_complete` it shows; `bmad-retrospective.toml` is new and is written as is.

## 1.6.0 — 2026-09-28

### Scrooge McDuck

- **Multi-year estimates.** An estimate now covers the build and then 3 to 5 years of run after go-live (`horizon_years`, default 5), with an optional yearly increase in run costs (`cost_escalation_pct`). A new **Multi-Year** sheet has columns Build and Year 1 to Year 5, zero past the horizon, so changing the horizon in Excel recalculates it. It shows revenue, every cost, contingency, net, cumulative net, the payback year and the return on cost.
- **Revenue.** A new **Revenue** sheet holds yearly revenue per stream (`revenue`: amounts per year, basis, cite), from the owner or a cited business case, never estimated. Without revenue, the workbook shows costs only and lists the missing revenue as a gap.
- **Run costs (OPEX).**
  - A run support table on Overall: role × mandays per year × day rate (`support`), for IT support and maintenance.
  - A **Run Costs** sheet for recurring yearly costs (`run_costs`: support contracts, licences).
  - `run_months_per_year` for environments that don't run all year.
  - The cost summary shows run per year and run over the horizon.
- **Daily costs.**
  - Each environment sheet has a daily cost column (monthly × 12 / 365).
  - The ledger writes `claude_usage_daily.csv`: Claude calls, tokens and cost in USD per day, work item and model, refreshed by the background hooks. It's costed once `claude_prices.py --save` has run.
  - The close-out adds it to the workbook as **Claude Usage Daily** (`tblClaudeUsageDaily`).
- **Epics sheet.** One row per epic (`epics`: number, name, deliverables, working days, optional Claude API budget, cite).
  - It shows working days, weeks and dates (from the new optional `start_date`, epics one after another), and the epic's share of the build: team mandays and cost, and infra during delivery.
  - One-off costs are tagged to an epic with `epic` on the Other Costs line, which gains an Epic column.
  - **Forecast against actual.** Forecast: team + infra + one-off + the Claude API budget. Actual, once an epic has actual start and end dates (from the timeline, or `actual_start` / `actual_end`): working days (NETWORKDAYS, like for like with the plan), days variance and %, the Claude API actual from the ledger, the actual cost (team and infra scaled by actual ÷ planned days, or the timesheet `actual_team_cost`) and the cost variance.
  - Every figure is a formula, with spare rows to add epics in Excel; `<name>.epics.csv` holds the same as plain values (`tblEpics` in the workbook).
- **Sprints sheet.** Fixed timeboxes of `sprint_days` (default 10) from the delivery start date, laid out by the sheet itself (`tblSprints`, `<name>.sprints.csv`).
  - Forecast: planned days at the delivery team's and environments' daily cost, planned stories and an optional Claude API budget per sprint (`sprints`).
  - Actual, up to the last actual activity (latest completed story or day of Claude usage): days worked, stories completed within the sprint's dates, Claude API cost on those days, team at the days worked or the timesheet `actual_team_cost`, and the cost variance.
  - Sprints past the plan appear when work runs over.
- **Dashboard facts in long format.** `<name>.facts.csv` is now one row per period, category and item (`estimate, currency, period, year, category, item, amount`), ready for Power BI.
- **Actual cloud spend.** Scrooge asks (at First Breath and after the first estimate) whether Azure Cost Management, or its daily exports, is available for the subscription, and records the answer so actuals can sit beside the estimate later.
- The sample (`assets/examples/falcon-portal/`) now covers five years, with revenue, run support, recurring run costs and daily Claude usage.

### Upgrading

- Estimate models from 1.5.0 need two changes before they rebuild: `assumptions.run_months` becomes `horizon_years` (3 to 5), and an environment's `run_months` becomes `run_months_per_year`. The build names both.
- The facts CSV's columns changed; point existing dashboards at the new long format.


## 1.5.0 — 2026-09-28

### Scrooge McDuck

- **Scrooge is now a memory agent.** On first talk he builds a sanctum at `_bmad/memory/agent-scrooge/` (identity files, session logs, `estimates.md`) and remembers your currency, pricing region, rate card and spending choices. Existing `stories.json` and `savings.json` there are kept. Capability prompts and scripts stay in the skill; `wake.py` lists them each session, so later kit updates need no sanctum migration.
- **Cost estimates (CE).** Prices the solution from the BMad artifacts (spine, spec, epics, sprint status, plus anything you give him) into `<name>.xlsx` in the new `cost_estimates_folder` (default `docs/cost_estimates`): an Overall sheet with inputs (days of delivery, working days per month, hours per month, months of run, contingency, exchange rate), a team table (employees × days × allocation = mandays, priced from the rate card) and a cost summary of delivery, run and grand totals; one sheet per environment; Rate Card; Other Costs; Sources & Gaps. All totals are formulas with named inputs.
  - `azure_prices.py` looks up Azure list prices from the public Retail Prices API with meter id and date.
  - `build_estimate.py` builds the workbook from a cited model (`<name>.estimate.json`), refuses a line whose citation doesn't resolve, an unpriced line or a role missing from the rate card, prints the same figures it writes as formulas, stamps the cited files and rate card for `--drift`, and won't overwrite a hand-edited workbook without `--force`.
- **Project close-out (PC).** How long the project took (`project_timeline.py`: BMad stages from git, custom agents from their sanctums, epics and stories from the sprint status's git history, Claude work items from the ledger; calendar and working days) and total Claude API calls costed at the list prices read from Anthropic's pricing page (`claude_prices.py`), added to the workbook as Claude Usage, Claude Usage Detail, Claude Prices and Project Timeline sheets and a cost-summary line (a memo on a subscription). The ledger gains `claude_usage.csv` (tokens by type per work item and model, first and last call) and attributes Leonardo's work to its own phase.
- **Sample workbook.** `skills/agent-scrooge/assets/examples/falcon-portal/`: a synthetic project's estimate and close-out in USD (`falcon-portal.xlsx`, `.facts.csv`, the model and its inputs), rebuildable with one command; a test keeps it building.
- **USD by default.** Estimates and the rate card are in US dollars unless the owner asks for another currency.
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
