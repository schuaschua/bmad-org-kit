# Org Kit (`org`)

A BMad module that adds the organisation layer to any BMad Method (`bmm`) project:

- **Org standards baselines** — `azure.md`, `terraform.md`, `security.md` and `coding-style.md` (org baseline 1.0.0). Projects copy them and extend them with their own names, rules and accepted exceptions.
- **Blank governance questionnaires** — `TechnicalArchitectureAssessment.docx` (platform questions, then business criticality: 23 questions), `DataGovernancePrivacyAssessment.docx` (10) and `EnterpriseAIRiskAssessment.docx` (20, for solutions that use AI; many drawn from the CBUAE AI guidance note).
- **BMad customization overrides** — the dev agent and the architecture, build, code-review and test-design workflows load the project's standards as persistent facts; when the architecture workflow finishes it offers Jules (governance assessments) and Scrooge McDuck (cost estimate), and when the build finishes the last story it offers Scrooge's project close-out; epics-and-stories uses the org's hybrid story structure and offers to sync to the project's Jira.
- **Scrooge McDuck (`agent-scrooge`), Token Usage Accountant and Cost Estimator** — a memory agent. Counts every API call in the project's Claude Code logs, attributes it to a story (by the project's Jira key) or planning phase, a step and an activity, writes a gitignored ledger, and sternly audits it for savings; background hooks keep the ledger current. Prices the solution from whatever the BMad work has produced so far (spine, spec, epics, plus anything you tell it) into an Excel workbook: a sheet per environment at Azure list prices, an employee rate card, other costs, and an overall summary where days of delivery, employees and mandays are inputs you can change.
- **Leonardo da Vinci (`leonardo-da-vinci`), Architecture Diagrams and Design Documents** — writes cited High-Level and Low-Level Design Word documents, and draws draw.io diagrams (C4 context, C4 containers, cloud deployment with Azure and Kubernetes icons, data flow with trust boundaries and PII/PHI, sequence for a named flow) from the project's architecture spine, spec and UX docs only. Every box and arrow cites its AD or section, gaps are listed rather than drawn, it challenges the architecture before drawing, and a drift check flags diagrams older than their spine.
- **Jules (`agent-jules`), IT Governance** — drafts, coaches and routes the Technical Architecture, Data Governance & Privacy and Enterprise AI Risk Assessment answers for the Product Lead and Tech Lead from the project's BMad artifacts, replies to reviewer comments and checks answers for drift. Jules asks whether your organisation has its own questionnaire templates (put them in the governance folder), and ports answers to similar questions over from the three standard ones. Jules also considers the regulatory documents of the region the solution is developed in, chosen at setup, citing the clause it relies on and checking each document's date before relying on it.

Version 1.5.0 (see [CHANGELOG.md](CHANGELOG.md)). Expansion of BMad Method.

## What this adds to BMad, and why it's different

BMad Method takes a project from idea to working code: brief, spec, architecture, epics and stories, build, review. What it doesn't cover is the work an organisation needs around that code. That means following the org's engineering standards, getting governance sign-off, knowing what the solution will cost to build and run, producing the design documents and diagrams reviewers ask for, and knowing what the AI-assisted delivery itself cost. Teams usually do that work by hand, after the fact, in documents that drift away from the design. The Org Kit does it inside the BMad flow, from the same artifacts.

- **One source of truth.** Everything the kit produces is derived from what BMad already writes: the architecture spine, the spec, the UX docs, the epics and the sprint status. There is no second model of the system to keep in step. Diagrams, design documents, cost estimates and governance answers are all read from the project's own BMad artifacts.
- **Cited, never guessed.** Every box in a diagram, sentence in a design document, line in a cost estimate and answer in a governance questionnaire names the architecture decision (AD) or section it came from. Whatever the artifacts don't settle is listed as a gap or an open point for the person who owns it, never filled with something plausible. The scripts refuse a citation that doesn't resolve. A reviewer can check any claim without the author in the room.
- **It challenges before it produces.** Leonardo, Scrooge and Jules each put the gaps, contradictions and risky choices to you first, most consequential first. Answers you approve become AD text in the spine, so the architecture itself improves, not just the document.
- **It notices when things change.** Each diagram, design document and estimate records which version of its sources it was built from. Drift checks name the decisions that changed since then, so a stale diagram or an answer resting on an old decision doesn't go unnoticed.
- **Standards live in BMad's own workflows.** The org's standards are loaded as persistent facts into the dev agent and the architecture, build, code-review and test-design workflows through BMad's customisation overrides. BMad itself isn't forked, so a BMad update keeps working.
- **It shows up at the right moment.** When the architecture is done, you're offered the governance assessments (Jules) and the cost estimate (Scrooge). When the last story is delivered, you're offered the project close-out. Epics and stories can sync to Jira, and HLD/LLD documents can be published to Confluence.
- **It measures itself.** Scrooge counts every Claude API call the project made, attributed to its story, planning phase, step and activity, and prices it at Anthropic's list prices. The close-out records how long each BMad stage and epic took. You get evidence of what AI-assisted delivery cost and where it was spent, not an impression, and the data feeds a Power BI dashboard.
- **People decide; agents prepare.** The agents draft, explain and route. The Product Lead and Tech Lead sign governance answers, and leads are referred to by role, never by name. Nothing is applied to a document, published to Confluence, synced to Jira or sent to governance without an explicit yes. Cloud and Claude prices come from their public price lists, with the date they were read, and day rates only ever come from your own rate card.
- **Org-owned, project-extended.** Standards baselines, questionnaires, design-document outlines and Word templates are the organisation's defaults. Each project copies them and extends them, and the kit never overwrites a project's own version. Your own governance templates can replace the standard ones, and answers to similar questions port over. Regional regulation (for example the CBUAE's AI guidance) is a setting, and cited clause by clause.
- **Agents that remember.** Jules and Scrooge are memory agents. Each keeps what it has learned about the project, its people and their decisions in the project's `_bmad/memory/`, and kit updates never overwrite it.

| BMad stage | What the Org Kit adds |
| --- | --- |
| Architecture | Org standards applied; diagrams and HLD/LLD documents drawn from the spine; its gaps challenged; governance assessments and cost estimate offered |
| Epics and stories | Org story structure; Jira sync |
| Build and review | Standards enforced in the dev agent, build and code review; every Claude call counted per story |
| Delivery complete | Close-out: duration by stage and epic, Claude API calls and cost, dashboard-ready workbook |
| Any time | Governance answers, reviewer replies and drift checks (Jules); cost and savings audits (Scrooge); diagram and document drift (Leonardo) |

## Contents

```text
skills/
  agent-jules/          # Jules: SKILL.md, sanctum templates, capability prompts, scripts (+ tests)
    assets/regions.toml # regional regulation registry: region -> regulator, web domains, source documents
  agent-scrooge/        # Scrooge: SKILL.md, sanctum templates, capability prompts, token_report.py,
                        #   azure_prices.py, build_estimate.py, wake/init-sanctum (+ tests)
  leonardo-da-vinci/    # SKILL.md, per-diagram-type and design-doc references, HLD/LLD outlines, stencil catalogues,
                        #   spine/build-drawio/build-docx/drift/stencil scripts (+ tests)
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

1. Install the kit as a module with the BMad installer, from its GitHub repository, in a terminal in the project folder:

   ```bash
   npx bmad-method install --custom-source https://github.com/darrel1234/bmad-org-kit
   ```

   Pick the Org Kit (`org`) module and Claude Code as the tool. To install without prompts, add `--modules bmm,org --tools claude-code --yes --set org.jira_site=https://<site>.atlassian.net --set org.jira_project_key=<KEY>` (plus `--set org.<key>=<value>` for any other question below). The installer asks the questions below, writes them to `[modules.org]` in `_bmad/config.toml`, and registers Jules and the capabilities in `bmad-help`.
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
   | `cost_estimates_folder` | where Scrooge writes cost estimate models and Excel workbooks | `{project-root}/docs/cost_estimates` |
   | `diagrams_folder` | where Leonardo da Vinci writes `.drawio` files, their models and exports | `{project-root}/docs/architecture/diagrams` |
   | `design_docs_folder` | where Leonardo da Vinci writes HLD/LLD `.docx` files and their models | `{project-root}/docs/architecture/design` |
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

## Architecture diagrams (Leonardo da Vinci)

Ask Leonardo for a diagram ("draw the deployment diagram", "C4 containers", "sequence diagram for one chat turn"). The skill reads the spine at `_bmad-output/planning-artifacts/architecture/<name>/ARCHITECTURE-SPINE.md` with the spec and UX docs, and nothing else.

- **Challenge first.** Before drawing it puts the gaps, contradictions and risky choices to you, most consequential first. Each answer becomes proposed AD wording, which it adds to the spine only once you approve the exact text, so the diagram can cite it.
- **Cited, not guessed.** Each diagram has a `<name>.model.json` beside its `.drawio`, listing every element with its citation and the gaps. The build refuses an element whose citation doesn't resolve to a real AD or source section, and a gap is listed on the page, never drawn.
- **Org drawing rules** (deployment): a service that hosts workloads, such as AKS, is a box with its icon; workloads inside it use a container icon; data services sit outside compute clusters in their own subnet; multi-region is one set of boxes per region (two when the spine doesn't count them) inside one enclosing box.
- **Icons** come from draw.io's own shape libraries: `skills/leonardo-da-vinci/assets/stencils/azure.json` (645 Azure stencils) and `kubernetes.json`. Another provider is one command away: `uv run skills/leonardo-da-vinci/scripts/stencils.py extract --index <draw.io search-index.json> --provider aws --prefix mxgraph.aws4.`.
- **Nothing overlaps.** Every label is measured and every arrow is routed in its own lane; a final check proves no text, icon, box or header collides, and the build refuses a diagram that would. It never squeezes the layout to save paper.
- **Paper.** It asks for size and orientation (default A4 portrait) and fits the diagram to one page or two; when that would print too small, it names the smallest paper that works (A4, A3, A2) before any split.
- **Stamped and checked for drift.** Each file records the spine's commit (or date) and a hash of every AD. `uv run skills/leonardo-da-vinci/scripts/diagram-drift.py <project-root>` names the ADs that changed and exits 1 when a diagram is stale, so it also works as a CI or pre-commit check.
- **Exports** (PNG, SVG) need draw.io desktop; the draw.io MCP server (`claude mcp add drawio -- npx -y @drawio/mcp`) adds an in-browser preview. Neither is required.

Jules may cite a current diagram in a Technical Architecture Assessment answer, beside the AD it was drawn from.

## Cost estimates (Scrooge McDuck)

Ask Scrooge for a cost estimate ("what will this cost to build and run?", "price the architecture", "update the estimate"). On first talk Scrooge builds its sanctum at `_bmad/memory/agent-scrooge/` (your existing `stories.json` and `savings.json` stay put) and asks for your reporting currency, Azure region and rate card.

- **From the BMad artifacts.** The spine decides the components, environments and regions; the spec sizes them; the epics and sprint status size the team. Feed it more at any time: a vendor quote, a figure in chat, a what-if scenario (each scenario is its own estimate).
- **Challenges first.** Gaps and contradictions that move the price (an unsized database, unstated DR) are put to you, most expensive first, before anything is priced.
- **Priced at source.** Cloud lines use Microsoft's public Retail Prices API (`skills/agent-scrooge/scripts/azure_prices.py`), at list price, with the meter id and date. Day rates come only from your rate card (`rate-card.json` in the sanctum). Discounts only when you give them.
- **Cited, not guessed.** Each line cites its AD or section, `owner: <who, date>`, or an agreed `assumption:`. Anything undecided is a gap listed in the workbook, never in a total.
- **The workbook** (`<name>.xlsx`, built by `build_estimate.py` from `<name>.estimate.json`): **Overall** (inputs: days of delivery, working days per month, hours per month, months of run, contingency, exchange rate; the team table with role, day rate, employees, days, allocation, mandays and cost; and the cost summary of delivery, run and grand totals), one sheet per **environment**, **Rate Card**, **Other Costs**, and **Sources & Gaps**. Every total is a formula, so changing a blue cell recalculates it in Excel.
- **Kept current.** `uv run skills/agent-scrooge/scripts/build_estimate.py <project-root> <name>.estimate.json --drift` names the cited files and rate card that changed since the build. A rebuild refuses to overwrite a workbook you edited by hand; Scrooge carries your edits into the model first.

- **Close-out.** At the end of the project Scrooge records how long it took: each BMad stage (from git), each custom agent (from its sanctum), each epic and story (from the sprint status's git history), start to finish in calendar and working days. He adds the total Claude API calls, costed at the list prices read from Anthropic's pricing page, as the Claude Usage, Claude Prices and Project Timeline sheets and a line in the cost summary (a memo when Claude Code was on a subscription).
- **Dashboards.** Every data range is a named Excel table (`tblCostSummary`, `tblTeam`, `tblEnv<name>`, `tblClaudeUsage`, `tblTimeline` ...) for Power BI or Excel Online. Power BI reads the values Excel last saved, so open and save a fresh build once, or use the plain-value CSVs: `<name>.facts.csv` beside the workbook, and `claude_usage.csv` and `project_timeline.csv` in the token usage folder.

Estimates are in US dollars unless a project asks Scrooge for another currency. To see a finished workbook before running one, open the synthetic sample in `skills/agent-scrooge/assets/examples/falcon-portal/` (`falcon-portal.xlsx`, with the model, inputs and a rebuild command in its README).

The workbooks carry the rate card; gitignore the cost estimates folder if the rates shouldn't be in the repository.

## Design documents (Leonardo da Vinci)

Ask Leonardo for the high-level design ("write the HLD") or a low-level design for a component ("LLD for the Chat API"). It writes `hld.docx` or `lld-<component>.docx` in the design documents folder, from a `<name>.doc.json` model beside it.

- **Same rules as the diagrams.** Only the BMad artifacts (spine, spec, UX, and the epics and test design where an LLD needs them), never code or the web. Every paragraph, list and table cites its AD or section in grey; what the sources don't settle is an *open point*, printed where it arises and collected in Appendix A. Appendix B traces each AD to the sections citing it and lists the ADs the document doesn't cite. It challenges the gaps before writing, and approved answers become AD text in the spine.
- **Diagrams included.** The document embeds the current diagrams its sections call for (C4, data flow and deployment for the HLD; sequences and deployment for an LLD), offering to draw missing ones first.
- **Org outline until you have a template.** The kit's default sections are `skills/leonardo-da-vinci/assets/design-docs/hld.md` and `lld.md`. When your organisation's template arrives, put its sections in `<design docs folder>/templates/hld.md` / `lld.md` and its Word file as `templates/reference.docx` (styles, header, footer, logo); Leonardo can set both up from the Word template.
- **Confluence.** When an HLD or LLD already lives on Confluence, Leonardo can start from it: its headings can become the project's outline, and its statements are checked against the BMad artifacts (what they support is cited, what they don't is put to you and becomes AD text only on approval). It can also publish the document to Confluence, as a new page under the project's wiki page or over the existing one, through the Atlassian MCP server. It asks before every create or update, and never overwrites an edit made on the page without showing it to you first. The page location comes only from the project's own settings or from you.
- **Word is for review, the model is the source.** A rebuild won't replace a `.docx` changed since the last build; Leonardo carries reviewers' changes into the model first. `diagram-drift.py` flags documents whose ADs changed.

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
| AQ | agent-jules | Answer the questionnaires (all three by default) |
| CL | agent-jules | Coach the Product Lead or Tech Lead |
| RC | agent-jules | Reply to reviewer comments |
| CW | agent-jules | Comment watch (pulse) |
| DR | agent-jules | Drift check |
| AL | agent-jules | Answer library |
| RF | agent-scrooge | Refresh the token ledger |
| SC | agent-scrooge | What a story or phase cost |
| CD | agent-scrooge | Cost drivers and savings audit |
| CL | agent-scrooge | Story cost line for PRs and Jira |
| CE | agent-scrooge | Cost estimate workbook (build or update) |
| RT | agent-scrooge | Employee rate card |
| PC | agent-scrooge | Project close-out: duration, Claude API calls and cost |
| DG | leonardo-da-vinci | Draw an architecture diagram |
| DS | leonardo-da-vinci | High-Level or Low-Level Design document |
| DD | leonardo-da-vinci | Diagram and document drift check |

## Updating

- Update the kit through the BMad installer (it refreshes the `org` config and help entries), then run `org-setup` again for any new project files.
- Standards, questionnaires and overrides that already exist in the project are left alone, so project extensions survive. To adopt a newer baseline, diff your copy against `skills/org-setup/assets/standards/` and merge by hand; each baseline carries its version in its header.
- Jules's sanctum (`_bmad/memory/agent-jules/`) is never touched by an update. Sanctum files and its copies of the capability prompts are created at First Breath, so template and prompt changes reach an existing sanctum only by hand; CHANGELOG.md lists what to carry over for each release.
- Scrooge's sanctum and project data (`_bmad/memory/agent-scrooge/`: identity files, `stories.json`, `savings.json`, `rate-card.json`) are never touched by an update. Its capability prompts and scripts stay in the skill, so they update with the kit without a migration.

## Developing the kit

```bash
uv run skills/org-setup/scripts/tests/test-install-org-assets.py
for t in skills/agent-jules/scripts/tests/*.py; do uv run "$t"; done
uv run --with pytest --with openpyxl pytest -q skills/agent-scrooge/scripts/tests   # add --with formulas to recalculate the workbook too
for t in skills/leonardo-da-vinci/scripts/tests/test_*.py; do uv run "$t"; done
```

Validate the module with the BMad Module Builder's Validate Module (VM) path on `skills/`.

## License

TODO (owner to choose).
