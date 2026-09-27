# Bond

## Basics
- **Name:** {user_name}
- **Call them:** {user_name}
- **Language:** {communication_language}

## Money
- **Reporting currency:** USD (the kit's default). {Change it only if the owner asks during First Breath.} Every estimate and the rate card use it.
- **Azure pricing region:** {The region the spine deploys to (armRegionName, for example uaenorth); asked when the spine doesn't say.}
- **Cloud price basis:** Azure retail list prices (pay-as-you-go) unless {user_name} gives a discount or reservation to apply, with its source.

## Workspace
- **Token ledger:** the org config's `token_usage_folder` (default `docs/token_usage/`, gitignored).
- **Cost estimates:** the org config's `cost_estimates_folder` (default `docs/cost_estimates/`): `<name>.estimate.json` (the model) and `<name>.xlsx` (the workbook). {Confirm during First Breath whether the folder should be gitignored: the workbooks carry the rate card.}
- **Jira project key:** {jira_project_key}

## BMad Artifacts
Ground truth for what gets built, read-only to me. {Confirm or correct during First Breath.}
- Spec / PRD: `_bmad-output/specs/` and `_bmad-output/planning-artifacts/`
- Architecture spine: `_bmad-output/planning-artifacts/architecture/<name>/ARCHITECTURE-SPINE.md`
- Epics and stories, sprint status: `_bmad-output/planning-artifacts/`, `_bmad-output/implementation-artifacts/`

## Things They've Asked Me to Remember
{Explicit requests.}

## Things to Avoid
{What annoys them, what doesn't work for them.}
