---
name: cost-estimate
description: Price the project from its BMad artifacts into an Excel workbook, one sheet per environment, a rate card and an overall summary; or update an existing estimate
code: CE
added: 2026-09-28
type: prompt
---

# Cost estimate

The outcome is a workbook {user_name} can put in front of whoever holds the budget: `<name>.xlsx` in the cost estimates folder (org config `cost_estimates_folder`, default `{project-root}/docs/cost_estimates/`), built by `scripts/build_estimate.py` from a model, `<name>.estimate.json`, that sits beside it. Every line cites where it came from, every price says which meter and when, and everything not yet decided is listed as a gap instead of guessed.

The workbook has an **Overall** sheet (inputs: days of delivery, working days per month, hours per month, months of run, contingency, exchange rate; the delivery team as role × employees × days × allocation = mandays, priced from the rate card; and the cost summary gathering every sheet into delivery, run and grand totals), one sheet per **environment**, the **Rate Card**, **Other Costs** and **Sources & Gaps**. Every total is a formula, so {user_name} can change a blue cell in Excel and the workbook recalculates. `uv run scripts/build_estimate.py --help` documents the model format in full.

## New or update

List the models already in the cost estimates folder. If {user_name} names one, or the project has one, this is an update: start with **Update** below. Several estimates can live side by side (`<project>-mvp`, `<project>-ha`), so a different scenario is a new model, usually copied from an existing one.

## What to read

The artifacts decide *what* is built; they never decide what it costs. Look before you ask: find these yourself and show {user_name} what you found and which of them you'll use.

- **Architecture spine** (`_bmad-output/planning-artifacts/architecture/<name>/ARCHITECTURE-SPINE.md`): components and the Azure service each runs on, data stores, networking, environments, regions, availability and disaster recovery.
- **Spec / PRD**: users, volumes, retention, availability targets: what sizes things.
- **Epics and stories, sprint status**: how much work there is, which kinds of work (front end, back end, infrastructure, data, testing), and how much is already done.
- **Anything else {user_name} gives you**: a file in the project, a vendor quote, figures typed in chat, a different set of environments for a what-if. A figure given in chat is cited as `owner: <who>, <date>`.

Read only inside the project.

## Build the bill of materials

For each environment (from the spine; if it names none, propose Dev, Test and Prod and ask), list each component as one line per priced meter: component, Azure service, SKU or tier, unit, quantity, usage per month and the citation. A service billed on several meters (compute and storage, say) gets a line per meter. Always-on hourly items use `"usage": "hours"`; anything that runs part-time (a dev cluster stopped at night) gets its hours as a number, cited to whoever decided it.

Then **challenge before pricing**: put the gaps and contradictions to {user_name}, most expensive first, each with roughly what it costs either way. Typical ones: the spine names a service but not its size, Prod's high availability or DR isn't stated, the environments differ from what the stories assume, or there are no data volumes. One round, in Scrooge's voice; each answer becomes an `owner:` cite or an agreed `assumption:`, and anything still open goes in `gaps`.

## Price it

For each line run `uv run scripts/azure_prices.py --service "<serviceName>" --region <region> --sku <armSkuName> --currency <currency>` (pricing region and currency from BOND.md, USD by default; `--help` has the other filters). When several meters come back, pick the one that matches the line and say which you chose when it isn't obvious. Tier 0 unless the volume clearly reaches a higher tier. Linux unless the artifacts say Windows. Copy the item's `source` into `price_source` and its `retailPrice` into `unit_price`. When the API has no currency the owner reports in, price in USD and set `cloud_currency`, `fx_rate` and `fx_source` from a rate {user_name} gives. No match in the API, or a service outside Azure (SaaS licences, a vendor): ask {user_name} for the figure, or list it as a gap.

List prices are what Microsoft charges a stranger. Apply a discount or reservation only when {user_name} gives it with its source, and say so in the line's note.

## The team

The team is priced from the rate card (capability RT, `rate-card.json` in the sanctum). If it's missing, or a role the team needs isn't on it, get the day rates from {user_name} first; never invent one.

Propose the team from the work: the roles the stories call for, the number of employees in each, and the days of delivery. Base your proposal on the story count, the stories still open in the sprint status, and a pace {user_name} confirms. Show the reasoning in one or two lines and let {user_name} set the numbers. `days: null` means the whole delivery (the Overall input), a number means a shorter stint (a security specialist for ten days), and `allocation` covers part-time roles. Cite the epics file for roles the stories imply and `owner:` for the numbers {user_name} set.

Ask once about **other costs** (licences, penetration test, training, support contracts). Include only the ones {user_name} gives a figure for.

## Build and report

Write the model to `<cost estimates folder>/<name>.estimate.json`, run `uv run scripts/build_estimate.py {project-root} <name>.estimate.json --check`, fix what it flags (a cite that doesn't resolve, a role not on the rate card, an unpriced line), then build without `--check`.

Report from the script's `figures`, figure first: the grand total, split into delivery and run, with the contingency. Then each environment's monthly cost, the team's mandays and cost, the gaps, and the workbook's path. Tell {user_name} that the blue cells are theirs to change in Excel, and that the model is the source: a rebuild replaces the workbook. For a dashboard, every data range is a named Excel table and `<name>.facts.csv` holds the cost lines as plain values (see `references/project-close-out.md`, For the dashboard). Finish the way every Scrooge report finishes, with where the money leaks: the most expensive lines, any over-sized or always-on item that needn't be, and what a reservation would save if Prod runs a year or more. Price each saving, and never touch what makes the system sound.

Add or update the estimate's line in `estimates.md` in the sanctum.

## Update

1. `uv run scripts/build_estimate.py {project-root} <name>.estimate.json --drift` names the cited files, and the rate card, that changed since the build. Re-read those ADs and sections and propose the line changes they cause, as a before-and-after with the monthly difference.
2. Prices move: if the model's `price_date` is more than a month old, or {user_name} asks, re-run the price lookups and report what changed.
3. If the build refuses because the workbook was changed after the last build, {user_name} edited it in Excel. Read the workbook's blue input cells (openpyxl), show the differences from the model, and carry the ones {user_name} wants to keep into the model before rebuilding. Use `--force` only when {user_name} says to discard the hand edits.
4. Rebuild, report the old and new grand totals and the lines that moved them, and update `estimates.md`.
