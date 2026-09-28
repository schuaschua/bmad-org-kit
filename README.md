# Org Kit (`org`)

A BMad module that adds the organisation layer to a BMad Method (`bmm`) project: org standards, governance sign-off, cost estimates, design documents and diagrams, and a count of what the AI-assisted delivery itself cost. Everything is produced inside the BMad flow, from the artifacts BMad already writes: the spine, spec, UX docs, epics and sprint status.

Version 1.8.0 ([CHANGELOG.md](CHANGELOG.md)).

## What's in it

| Part | What it does |
| --- | --- |
| **Standards baselines** | `azure.md`, `terraform.md`, `security.md`, `coding-style.md` (org baseline 1.0.0). Copied into each project, which extends them. |
| **Governance questionnaires** | Technical Architecture (23 questions), Data Governance & Privacy (10) and Enterprise AI Risk (20) Assessments, as blank `.docx`. |
| **BMad overrides** | Load the standards into the dev agent and the architecture, build, code-review and test-design workflows, and make the agents below show up at the right moment. BMad itself isn't forked. |
| **Jules** (`agent-jules`) | IT governance: drafts the assessment answers for the Product Lead and Tech Lead, replies to reviewers, checks for drift, and cites regional regulation. |
| **Leonardo da Vinci** (`leonardo-da-vinci`) | draw.io diagrams (C4, deployment, data flow, sequence) and HLD/LLD Word documents. |
| **Scrooge McDuck** (`agent-scrooge`) | Token ledger and budgets, cost estimates in Excel, infrastructure OPEX, and the project close-out. |

## How it works

- **Cited, never guessed.** Every diagram box, document paragraph, estimate line and governance answer names the AD or section it came from. What the artifacts don't settle is listed as a gap, and the scripts refuse a citation that doesn't resolve.
- **Challenges first.** The agents put the gaps and contradictions to you before producing anything, most consequential first. Answers you approve become AD text in the spine.
- **Drift checks.** Every output records the sources it was built from and flags the decisions that changed since.
- **People decide.** Nothing is published, synced to Jira or sent to governance without an explicit yes. Prices come from public price lists, with the date read. Day rates come only from your rate card.
- **Org-owned, project-extended.** The kit never overwrites a project's own copy of a standard, template or override. Jules and Scrooge keep their memory in `_bmad/memory/`, which updates never touch.

## When it shows up

| Moment | What you're offered or asked |
| --- | --- |
| `bmad-architecture` finishes | Any of: diagrams (Leonardo), governance assessments (Jules), cost estimate (Scrooge) |
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
| `token_usage_folder` (gitignored) | `{project-root}/docs/token_usage` |
| `cost_estimates_folder` | `{project-root}/docs/cost_estimates` |
| `diagrams_folder` | `{project-root}/docs/architecture/diagrams` |
| `design_docs_folder` | `{project-root}/docs/architecture/design` |
| `region` (`none`, `uae`) | `none` |

### Check it's working

Run these after installing and after every kit update:

```bash
ls _bmad/custom/                                          # one file per override
grep -L "leonardo-da-vinci" _bmad/custom/bmad-architecture.toml
grep -L "ai_feedback.py"    _bmad/custom/bmad-build*.toml _bmad/custom/bmad-retrospective.toml
grep -L "token budgets"     _bmad/custom/bmad-create-epics-and-stories.toml _bmad/custom/bmad-sprint-planning.toml
uv run .claude/skills/agent-scrooge/scripts/ai_feedback.py . pending   # should print "status": "ok"
```

The `grep -L` lines list any override that is out of date. Merge the kit's version from `skills/org-setup/assets/custom/` into it, or that prompt won't appear.

"No such file" from the last command means the skills aren't in `.claude/skills/`. Rerun setup with `--skills-mode link` or `copy`.

## Leonardo da Vinci: diagrams and design documents

Ask for a diagram ("draw the deployment diagram", "sequence diagram for one chat turn") or a document ("write the HLD", "LLD for the Chat API"). Leonardo reads only the spine, spec and UX docs (plus the epics and test design for an LLD).

- **Diagrams**: a `.drawio` file with a `<name>.model.json` beside it listing each element's citation. They use Azure and Kubernetes icons from draw.io's libraries and follow the org's drawing rules. Nothing overlaps, and the paper size is chosen to fit. PNG and SVG exports need draw.io desktop.
- **Documents**: `hld.docx` or `lld-<component>.docx`, with the current diagrams embedded, open points collected in an appendix, and a trace from each AD to where it's cited. They follow the org outline, or your template in `<design docs folder>/templates/`. Leonardo can start from an existing Confluence page and publish to Confluence, asking first.
- **Drift**: `uv run skills/leonardo-da-vinci/scripts/diagram-drift.py <project-root>` names the ADs that changed. It exits 1 when anything is stale, so it also works in CI.

## Scrooge McDuck: tokens and costs

- **Token ledger.** Every Claude API call in the project's logs is counted by story or planning phase, step, activity and model. The ledger in `token_usage_folder` refreshes after every turn. Ask Scrooge what a story cost, what drives the spend, or for a one-line cost summary for a pull request.
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
| leonardo-da-vinci | DG diagram · DS design document · DD drift check |

## Updating

Update through the BMad installer, then run "setup Org Kit" again and merge any override it lists as waiting. Then run [the checks](#check-its-working). Existing standards and overrides are never overwritten. To adopt a newer baseline, diff your copy against `skills/org-setup/assets/standards/`.

Agent memory under `_bmad/memory/` is never touched. Scrooge's prompts and scripts update with the kit. Jules's copied prompts need the carry-overs listed in the CHANGELOG.

## Developing the kit

```bash
uv run skills/org-setup/scripts/tests/test-install-org-assets.py
for t in skills/agent-jules/scripts/tests/*.py; do uv run "$t"; done
uv run --with pytest --with openpyxl pytest -q skills/agent-scrooge/scripts/tests   # --with formulas also recalculates the workbook
for t in skills/leonardo-da-vinci/scripts/tests/test_*.py; do uv run "$t"; done
```

Validate the module with the BMad Module Builder's Validate Module (VM) path on `skills/`.

## License

TODO (owner to choose).
