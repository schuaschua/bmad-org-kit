# Org Kit (`org`)

A BMad module that adds the organisation layer to a BMad Method (`bmm`) project: org standards, governance sign-off, cost estimates, design documents and diagrams, and a count of what the AI-assisted delivery itself cost. Everything is produced inside the BMad flow, from the artifacts BMad already writes: the spine, spec, UX docs, epics and sprint status.

Version 1.13.0 ([CHANGELOG.md](CHANGELOG.md)). Requires BMad 6.12. BMad 6.13 replaces the epics and sprint planning skills with `bmad-ticket`; Org Kit 2.0 will support it.

## What's in it

| Part | What it does |
| --- | --- |
| **Standards baselines** | `azure.md`, `terraform.md`, `security.md`, `coding-style.md` (org baseline 1.0.0). Copied into each project, which extends them. |
| **Governance questionnaires** | Technical Architecture (23 questions), Data Governance & Privacy (10) and Enterprise AI Risk (20) Assessments, as blank `.docx`. |
| **BMad overrides** | Load the standards into the dev agent and the architecture, build, code-review and test-design workflows, and make the agents below show up at the right moment. BMad itself isn't forked. |
| **Jules** (`agent-jules`) | IT governance: drafts the assessment answers for the Product Lead and Tech Lead, replies to reviewers, checks for drift, and cites regional regulation. |
| **Da Vinci** (`agent-davinci`) | Agrees the architecture principles with you before `bmad-architecture`, then draws draw.io diagrams (C4, deployment, data flow, sequence) and writes HLD/LLD Word documents. |
| **Scrooge McDuck** (`agent-scrooge`) | Token ledger and budgets, cost estimates in Excel, infrastructure OPEX, and the project close-out. |

## How it works

- **Cited, never guessed.** Every diagram box, document paragraph, estimate line and governance answer names the AD or section it came from. What the artifacts don't settle is listed as a gap, and the scripts refuse a citation that doesn't resolve.
- **Challenges first.** The agents put the gaps and contradictions to you before producing anything, most consequential first. Answers you approve become AD text in the spine.
- **Drift checks.** Every output records the sources it was built from and flags the decisions that changed since.
- **People decide.** Nothing is published, synced to Jira or sent to governance without an explicit yes. Prices come from public price lists, with the date read. Day rates come only from your rate card.
- **Org-owned, project-extended.** The kit never overwrites a project's own copy of a standard, template or override. Jules, Scrooge and Da Vinci keep their memory in `_bmad/memory/`, which updates never touch.
- **Everything lands in `docs/`.** Governance in `docs/governance/`, costing in `docs/costing/`, architecture principles, diagrams and design documents in `docs/architecture/`.

## When it shows up

| Moment | What you're offered or asked |
| --- | --- |
| `bmad-spec`, `bmad-architecture` or `bmad-build` starts, with no `docs/architecture/architecture.md` | Stops and sends you to Da Vinci to agree the architecture principles first (you can choose to go on without) |
| `bmad-build` finishes, or `bmad-code-review` runs | Da Vinci's DevOps stack check: pipeline or IaC files for a tool you didn't agree |
| `bmad-architecture` finishes | Any of: diagrams (Da Vinci), governance assessments (Jules), cost estimate (Scrooge) |
| `bmad-create-epics-and-stories` finishes | Jira sync; then Scrooge's token budgets, if none are set |
| `bmad-sprint-planning` finishes | Scrooge's token budgets (or a review that adds sprint budgets) |
| `bmad-build` finishes an epic, or `bmad-retrospective` finishes | Rate the AI on the epic, 1 to 5; if 1 or 2, what went wrong |
| `bmad-build` finishes the last story | Scrooge's project close-out |
| Scrooge wakes | Any unrated epic, then any missing budgets |

The ratings go to `_bmad/memory/agent-scrooge/ai-feedback.csv`; commit that file with the project. An epic counts as finished only when the sprint status says so.

## Install

Prerequisites: BMad Method in the project (`_bmad/`) and [`uv`](https://docs.astral.sh/uv/). Recommended: the Atlassian MCP server (Jira, Confluence) and the safe-docx MCP server (Jules's tracked changes).

1. In the project folder, install the module and pick Org Kit (`org`) and Claude Code:

   ```bash
   npx bmad-method install --custom-source https://github.com/schuaschua/bmad-org-kit
   ```

   To skip the prompts: `--modules bmm,org --tools claude-code --yes --set org.jira_site=https://<site>.atlassian.net --set org.jira_project_key=<KEY>`.
2. Run **"setup Org Kit"**. After a dry run, it:
   - copies the standards and questionnaires;
   - writes the `_bmad/custom` overrides and links the skills into `.claude/skills/`;
   - gitignores the token ledger and adds Scrooge's refresh hooks;
   - checks the tooling.

   It never overwrites a file the project already has. For an existing override, it shows the lines to merge instead.

| Setting | Default |
| --- | --- |
| `jira_site`, `jira_project_key` | required |
| `confluence_wiki_url` | optional |
| `governance_folder` | `{project-root}/docs/governance` |
| `standards_folder` | `{project-root}/docs/standards` |
| `token_usage_folder` (gitignored) | `{project-root}/docs/costing/token_usage` |
| `cost_estimates_folder` | `{project-root}/docs/costing` |
| `architecture_folder` (holds `architecture.md` and the per-cloud files) | `{project-root}/docs/architecture` |
| `diagrams_folder` | `{project-root}/docs/architecture/diagrams` |
| `design_docs_folder` | `{project-root}/docs/architecture/design` |
| `region` (`none`, `uae`) | `none` |

### Check it's working

Run these after installing and after every kit update:

```bash
ls _bmad/custom/                                          # one file per override
grep -L "architecture.md"     _bmad/custom/bmad-architecture.toml _bmad/custom/bmad-spec.toml _bmad/custom/bmad-build.toml
grep -L "stack-check.py"      _bmad/custom/bmad-build*.toml _bmad/custom/bmad-code-review.toml
grep -L "ai_feedback.py"    _bmad/custom/bmad-build*.toml _bmad/custom/bmad-retrospective.toml
grep -L "token budgets"     _bmad/custom/bmad-create-epics-and-stories.toml _bmad/custom/bmad-sprint-planning.toml
uv run .claude/skills/agent-scrooge/scripts/ai_feedback.py . pending   # should print "status": "ok"
```

The `grep -L` lines list any override that is out of date. Merge the kit's version from `skills/org-setup/assets/custom/` into it, or that prompt won't appear.

"No such file" from the last command means the skills aren't in `.claude/skills/`. Rerun setup with `--skills-mode link` or `copy`.

## Da Vinci: principles, diagrams and design documents

Da Vinci is a memory agent. He remembers the principles you held firm on and the drawing choices you prefer.

- **Architecture principles.** Before `bmad-architecture`, say "Da Vinci, set the architecture principles".
  - He first reads the brief, spec, PRD, your region's regulation and any policies you've put in `docs/architecture/`. He never asks what they already answer; those answers are recorded with their source. The kit's org standards don't count as answers.
  - He opens with "Bonjournio, I am the architecture design guardian & artist ..." and lists what he found in your files, each with its source.
  - He then asks how to go on: **answer the questions**, **pick everything for me** (he answers from your documents and safe defaults, marking each pick), or **skip the questions** (only what the documents say; the rest stays open). Run unattended, he skips.
  - The six questions, one at a time, each asking only its open parts:
    1. where it runs and how it connects: cloud, hybrid or on-premises; the cloud platforms; IaaS or PaaS; regions and high availability; the on-premises link;
    2. rules and priorities: your architecture policies (put them in `docs/architecture/`; the rest is then answered from them first), a 1 to 6 ranking of the Well-Architected pillars, the security level, naming and tags;
    3. solution shape and stack: web, mobile or hybrid; event-driven, microservices or monolith; migration; the approved front end, back end and database;
    4. data and AI: how much AI, familiarity, data quality, building your own models, the AI platform; heavy analytics;
    5. DevOps, build and deploy: CI (GitHub Actions, Jenkins, CircleCI, Azure DevOps, Bitbucket Pipelines), CD and GitOps (Argo CD, Flux, Tekton), source control and branching, infrastructure as code;
    6. DevOps, environments and release: the environments and their separation, approval gates and release strategy, secrets and scans (SAST, DAST, dependency, image).

    DevOps is always asked, even when your documents mention it.
  - The answers become a Context table, and the ones that constrain the design become principles (`P-1`, `P-2` ...): testable rules with their reason, pillar and source. Skipped questions stay open.
  - He shows you a summary of every answer, the principles and the open questions, and writes only once you confirm it.
  - Cloud-neutral answers go in `docs/architecture/architecture.md`. Each cloud you name gets its own file beside it (`azure.md`, `aws.md` ...), holding its services, naming, tags, regions, connectivity and principles. Principle numbers are unique across the files.
  - `bmad-architecture` loads every `.md` in `docs/architecture/` as standing facts: every AD honours each principle or names the one it departs from and why. So do `bmad-build`, `bmad-build-auto`, `bmad-code-review` and the dev agent.
  - **The build keeps to the DevOps stack.** `uv run skills/agent-davinci/scripts/stack-check.py <project-root>` flags pipeline and infrastructure files for a tool you didn't agree (Bicep when you chose Terraform, a GitHub Actions workflow when you chose Jenkins). `bmad-build` won't call work finished until they're fixed or you keep them, `bmad-build-auto` reports them, and `bmad-code-review` raises them as findings. `--strict` also fails when an agreed tool has no files yet.
- **No spine, no drawing.** Diagrams, documents and the drift check need a spine. Without one Da Vinci stops, even when told not to ask questions or to just sketch; there's no draft mode.
- **Diagrams**: "draw the deployment diagram", "sequence diagram for one chat turn". A `.drawio` file with a `<name>.model.json` beside it listing each element's citation. They use Azure and Kubernetes icons from draw.io's libraries and follow the org's drawing rules. Nothing overlaps, and the paper size is chosen to fit. PNG and SVG exports need draw.io desktop.
- **Documents**: "write the HLD", "LLD for the Chat API". `hld.docx` or `lld-<component>.docx`, with the current diagrams embedded, open points collected in an appendix, and a trace from each AD to where it's cited. They follow the org outline, or your template in `<design docs folder>/templates/`. Da Vinci can start from an existing Confluence page and publish to Confluence, asking first.
- **Drift**: `uv run skills/agent-davinci/scripts/diagram-drift.py <project-root>` names the ADs that changed. It exits 1 when anything is stale, so it also works in CI. Da Vinci also checks the spine still honours the principles.

Diagrams and documents come only from the spine, spec and UX docs (plus the epics and test design for an LLD). Da Vinci challenges their gaps and any departure from the principles before drawing.

## Scrooge McDuck: tokens and costs

- **Token ledger.** Every Claude API call in the project's logs is counted by story or planning phase, step, activity and model. The ledger in `token_usage_folder` refreshes after every turn. `token_usage_summary.csv` splits each story into six categories: AI comprehension (reading / shell), AI reasoning (thinking / reporting), Writing code, Writing tests, Running tests and checks, and MCP usage (git / Jira / PR and every MCP server call). `token_usage_summary_final.csv` does the same for all stories combined. `agent_runs.csv` records orchestration: one row per subagent, with who started it (the main session or another agent), whether an `Agent` call or a `Workflow` started it, its work item, when it ran, how many other agents ran alongside it, and its cost. Ask Scrooge what a story cost, what drives the spend, or for a one-line cost summary for a pull request. Each person's logs stay on their own machine, so the ledger counts your sessions only. For the whole team, set `team_logs_folder` to a shared folder outside the repository (in your `_bmad/custom/config.user.toml`). Everyone exports their logs there (`token_report.py --export`), and the ledger then gains a `person` column and tables by person.
- **Token budgets.** Once the epics and sprint plan exist, you set a Claude API budget in money for each epic, each sprint (optional) and each remaining phase. They're kept in `_bmad/memory/agent-scrooge/token-budgets.json`. `token_usage_summary_final.csv` and `report.md` then show budget against actual and the variance.
- **Cost estimate.** "What will this cost to build and run?" Scrooge prices the solution from the spine, spec and epics into `<name>.xlsx`, built from `<name>.estimate.json`:
  - cloud at Azure list prices;
  - the team from your rate card;
  - the build plus 3 to 5 years of run.

  The workbook has these sheets:
  - Overall (inputs, team, run support, cost summary);
  - Epics and Sprints (forecast against actual);
  - Phase Budgets;
  - Multi-Year (net, payback, return);
  - Revenue, Run Costs, one sheet per environment, Rate Card, Other Costs, and Sources & Gaps.

  Every total is a formula, so a blue input cell can be changed in Excel. `--drift` names the sources that changed since the last build.
- **Infrastructure OPEX.** Every build writes `<name>.infra_cost.csv`: each cloud line, each environment and the total, as daily, weekly, monthly and annual cost after go-live.
- **Close-out.** Records how long each BMad stage, epic and story took, and the Claude API calls and cost at Anthropic's list prices. It adds these, with the AI ratings, to the workbook.
- **Dashboards.** Every range is a named Excel table for Power BI. Plain-value CSVs sit beside the workbook (`facts`, `infra_cost`, `epics`, `sprints`, `phases`) and in the token usage folder (`claude_usage`, `claude_usage_daily`, `project_timeline`).

Estimates are in USD unless you ask otherwise. The workbooks contain the rate card, so gitignore the cost estimates folder if the rates shouldn't be in the repository. For a finished sample, see `skills/agent-scrooge/assets/examples/falcon-portal/`.

## Jules: governance and regions

Jules drafts the three assessments from the BMad artifacts, coaches the Product Lead and Tech Lead, replies to reviewer comments and checks answers for drift. The leads sign; they're referred to by role, never by name. Your organisation's own questionnaires can go in the governance folder, and answers to similar questions carry over.

The `region` setting picks the regulatory documents Jules cites, clause by clause, from the regulator's site. It checks each document's date and never claims the project complies.

| Region | Regulator | Documents |
| --- | --- | --- |
| `uae` | Central Bank of the UAE | [Guidelines for Financial Institutions Adopting Enabling Technologies](https://rulebook.centralbank.ae/en/rulebook/guidelines-financial-institutions-adopting-enabling-technologies); [AI Guidance Note](https://rulebook.centralbank.ae/en/rulebook/guidance-note-consumer-protection-and-responsible-adoption-and-use-artificial-intelligence) (solutions that use AI) |

To add a region, add `[regions.<code>]` to `skills/agent-jules/assets/regions.toml` and the same code to the `region` choices in `skills/org-setup/assets/module.yaml`.

## Capabilities

| Skill | Codes |
| --- | --- |
| org-setup | SU set up or reconfigure |
| agent-jules | AQ answer questionnaires · CL coach · RC reply to reviewers · CW comment watch · DR drift check · AL answer library |
| agent-scrooge | RF refresh ledger · SC story or phase cost · CD cost drivers · CL story cost line · TB token budgets · CE cost estimate · RT rate card · PC close-out · EF epic AI feedback |
| agent-davinci | AP architecture principles · DG diagram · DS design document · DD drift check |

## Updating

Update through the BMad installer, then run "setup Org Kit" again and merge any override it lists as waiting. Then run [the checks](#check-its-working). Existing standards and overrides are never overwritten. To adopt a newer baseline, diff your copy against `skills/org-setup/assets/standards/`.

Agent memory under `_bmad/memory/` is never touched. Scrooge's and Da Vinci's prompts and scripts update with the kit. Jules's copied prompts need the carry-overs listed in the CHANGELOG.

## Developing the kit

```bash
uv run skills/org-setup/scripts/tests/test-install-org-assets.py
for t in skills/agent-jules/scripts/tests/*.py; do uv run "$t"; done
uv run --with pytest --with openpyxl pytest -q skills/agent-scrooge/scripts/tests   # --with formulas also recalculates the workbook
for t in skills/agent-davinci/scripts/tests/test_*.py; do uv run "$t"; done
```

Validate the module with the BMad Module Builder's Validate Module (VM) path on `skills/`.

## License

MIT. See [LICENSE](LICENSE).
