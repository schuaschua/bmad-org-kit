"""Tests for build_estimate.py against a throwaway project (synthetic spine, rate card and model).

Run: uv run --with pytest --with openpyxl pytest -q skills/agent-scrooge/scripts/tests
Add --with formulas to also recalculate the workbook's formulas and compare them with the script's figures.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "build_estimate.py"
spec = importlib.util.spec_from_file_location("build_estimate", SCRIPT)
build_estimate = importlib.util.module_from_spec(spec)
sys.modules["build_estimate"] = build_estimate
spec.loader.exec_module(build_estimate)

openpyxl = pytest.importorskip("openpyxl")

SPINE = "_bmad-output/planning-artifacts/architecture/demo/ARCHITECTURE-SPINE.md"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "_bmad" / "memory" / "agent-scrooge").mkdir(parents=True)
    (tmp_path / "_bmad" / "config.toml").write_text(
        '[modules.org]\ncost_estimates_folder = "{project-root}/docs/cost_estimates"\n')
    spine = tmp_path / SPINE
    spine.parent.mkdir(parents=True)
    spine.write_text("# Spine\n## AD-1 Hosting\nAKS, environments Dev and Prod.\n")
    (tmp_path / "_bmad" / "memory" / "agent-scrooge" / "rate-card.json").write_text(json.dumps(
        {"currency": "USD", "updated": "2026-09-28", "source": "test",
         "roles": [{"role": "Developer", "day_rate": 500}, {"role": "Tech Lead", "day_rate": 800}]}))
    return tmp_path


def model(**over) -> dict:
    m = {
        "name": "demo", "currency": "USD", "pricing_region": "uaenorth", "price_date": "2026-09-28",
        "assumptions": {"delivery_days": 63, "contingency_pct": 10},
        "environments": [
            {"name": "Dev", "run_months": 6, "items": [
                {"component": "AKS nodes", "service": "Virtual Machines", "sku": "Standard_D4s_v5",
                 "unit": "1 Hour", "unit_price": 0.235, "quantity": 2, "cite": f"{SPINE} AD-1", "price_source": "API"}]},
            {"name": "Prod", "delivery_months": 1, "items": [
                {"component": "AKS nodes", "service": "Virtual Machines", "sku": "Standard_D4s_v5",
                 "unit": "1 Hour", "unit_price": 0.235, "quantity": 3, "cite": f"{SPINE} AD-1", "price_source": "API"},
                {"component": "Storage", "service": "Storage", "unit": "1 GB/Month", "unit_price": 0.02,
                 "quantity": 500, "usage": 1, "cite": "assumption: 500 GB of documents", "price_source": "API"}]}],
        "team": [{"role": "Developer", "employees": 3, "cite": f"{SPINE} AD-1"},
                 {"role": "Tech Lead", "employees": 1, "allocation": 0.5, "cite": "owner: Tech Lead, 2026-09-28"}],
        "other_costs": [{"item": "Pen test", "cost": 5000, "cite": "assumption: typical"}],
        "gaps": ["DR region not stated"],
    }
    m.update(over)
    return m


def write_model(project: Path, m: dict) -> Path:
    path = project / "docs" / "cost_estimates" / "demo.estimate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m))
    return path


def run(project: Path, *args: str, capsys) -> tuple[int, dict]:
    code = build_estimate.main([str(project), *args])
    return code, json.loads(capsys.readouterr().out)


def test_figures(project, capsys):
    write_model(project, model())
    code, out = run(project, "demo.estimate.json", "--check", capsys=capsys)
    assert code == 0, out
    f = out["figures"]
    assert f["delivery_months"] == 3.0
    assert f["environments"][0] == {"name": "Dev", "monthly": 343.1, "delivery": 1029.3, "run": 2058.6}
    assert f["environments"][1]["monthly"] == 524.65  # 0.235 x 3 x 730 + 0.02 x 500
    assert f["team"] == {"employees": 4, "mandays": 220.5, "cost": 119700.0}
    assert f["grand_total"]["total"] == 148069.19


def test_workbook_sheets_and_formulas(project, capsys):
    path = write_model(project, model())
    code, out = run(project, "demo.estimate.json", capsys=capsys)
    assert code == 0, out
    wb = openpyxl.load_workbook(out["workbook"])
    assert wb.sheetnames == ["Overall", "Rate Card", "Other Costs", "Dev", "Prod", "Sources & Gaps"]
    ov = wb["Overall"]
    cells = {c.value: c for row in ov.iter_rows() for c in row if isinstance(c.value, str)}
    assert "=DeliveryDays/WorkingDaysPerMonth" in cells
    assert any(v.startswith("=VLOOKUP(A") for v in cells)
    assert "Grand total" in cells
    assert {"DeliveryDays", "HoursPerMonth", "Contingency", "FxRate"} <= set(wb.defined_names)
    assert wb["Dev"]["H5"].value == "=HoursPerMonth" and wb["Dev"]["I5"].value == "=F5*G5*H5*FxRate"
    assert wb["Prod"]["H6"].value == 1
    gaps = [c.value for c in wb["Sources & Gaps"]["B"] if c.value]
    assert "DR region not stated" in gaps
    assert any("assumption: 500 GB" in g for g in gaps)
    stamp = json.loads(path.read_text())["stamp"]
    assert SPINE in stamp["files"] and "workbook_mtime" in stamp


def test_formulas_recalculate_to_the_same_figures(project, capsys):
    formulas = pytest.importorskip("formulas")
    write_model(project, model())
    _, out = run(project, "demo.estimate.json", capsys=capsys)
    sol = formulas.ExcelModel().loads(out["workbook"]).finish().calculate()
    values = {str(k).split("]")[-1].upper(): v.value[0][0] for k, v in sol.items() if hasattr(v, "value")}
    grand = [v for k, v in values.items() if k.startswith("OVERALL'!G") and isinstance(v, float)]
    assert max(grand) == pytest.approx(out["figures"]["grand_total"]["total"], abs=0.01)


@pytest.mark.parametrize("change, message", [
    (lambda m: m["environments"][0]["items"][0].update(cite=f"{SPINE} AD-9"), "'AD-9' does not appear"),
    (lambda m: m["environments"][0]["items"][0].update(cite="docs/missing.md"), "does not exist"),
    (lambda m: m["environments"][0]["items"][0].update(cite="../outside.md"), "outside the project"),
    (lambda m: m["environments"][0]["items"][0].update(unit_price=None), "unpriced item belongs in gaps"),
    (lambda m: m["environments"][0]["items"][0].pop("price_source"), "price_source missing"),
    (lambda m: m["team"].append({"role": "Architect", "employees": 1, "cite": "owner: x"}), "not on the rate card"),
    (lambda m: m["team"][0].update(allocation=1.5), "allocation"),
    (lambda m: m["environments"].append({"name": "Overall", "items": []}), "clashes"),
    (lambda m: m.update(currency="AED"), "rate card is in USD"),
    (lambda m: m.update(cloud_currency="EUR"), "fx_rate"),
])
def test_refuses_invalid_models(project, capsys, change, message):
    m = model()
    change(m)
    write_model(project, m)
    code, out = run(project, "demo.estimate.json", capsys=capsys)
    assert code == 1
    assert any(message in e for e in out["errors"]), out["errors"]


def test_fx_converts_cloud_prices(project, capsys):
    write_model(project, model(cloud_currency="EUR", fx_rate=2, fx_source="test rate"))
    _, out = run(project, "demo.estimate.json", "--check", capsys=capsys)
    assert out["figures"]["environments"][0]["monthly"] == 686.2


def test_drift_and_hand_edits(project, capsys):
    write_model(project, model())
    code, out = run(project, "demo.estimate.json", capsys=capsys)
    workbook = Path(out["workbook"])
    assert run(project, "demo.estimate.json", "--drift", capsys=capsys)[1]["status"] == "current"
    (project / SPINE).write_text("# Spine\n## AD-1 Hosting\nAKS, Dev, Test and Prod.\n")
    code, out = run(project, "demo.estimate.json", "--drift", capsys=capsys)
    assert code == 1 and out["changed"] == [SPINE]
    # a rebuild over an unchanged workbook is fine; over a hand-edited one it is refused
    assert run(project, "demo.estimate.json", capsys=capsys)[0] == 0
    later = workbook.stat().st_mtime + 60
    os.utime(workbook, (later, later))
    code, out = run(project, "demo.estimate.json", capsys=capsys)
    assert code == 2 and "changed after the last build" in out["message"]
    assert run(project, "demo.estimate.json", "--force", capsys=capsys)[0] == 0


USAGE = """kind,work_item,story_no,title,model,first_call,last_call,calls,input_tokens,cache_write_5m_tokens,cache_write_1h_tokens,cache_read_tokens,output_tokens,cost_units
planning,architecture,,,claude-opus-5-5,2026-09-01T09:00:00Z,2026-09-02T10:00:00Z,10,1000000,0,1000000,10000000,100000,0
story,PROJ-1,1.1,Login,claude-haiku-4-5-20251001,2026-09-07T09:00:00Z,2026-09-08T10:00:00Z,5,2000000,0,0,0,0,0
story,PROJ-1,1.1,Login,<synthetic>,2026-09-07T09:00:00Z,2026-09-07T09:00:00Z,1,0,0,0,0,0,0
"""
PRICES = {"source": "https://platform.claude.com/docs/en/about-claude/pricing", "fetched": "2026-09-28", "currency": "USD",
          "models": {"claude-opus-5-5": {"name": "Claude Opus 5.5", "input": 4, "cache_write_5m": 5, "cache_write_1h": 8,
                                         "cache_read": 0.2, "output": 20},
                     "claude-haiku-4-5": {"name": "Claude Haiku 4.5", "input": 1, "cache_write_5m": 1.25,
                                          "cache_write_1h": 2, "cache_read": 0.1, "output": 5}}}
TIMELINE = """category,name,detail,status,started,completed,days,source
project,demo,13 working days,complete,2026-08-28,2026-09-15,19,summary
epic,epic-1,2 stories,done,2026-09-07,2026-09-15,9,git
"""
# opus: 4 + 8 + 10M x 0.2 = 2 + 0.1M x 20 = 2 -> 16; haiku: 2M x 1 = 2 -> 18 USD
CLAUDE_USD = 18.0


def close_out_files(project: Path) -> None:
    ledger = project / "docs" / "token_usage"
    ledger.mkdir(parents=True, exist_ok=True)
    (ledger / "claude_usage.csv").write_text(USAGE)
    (ledger / "project_timeline.csv").write_text(TIMELINE)
    (project / "_bmad" / "memory" / "agent-scrooge" / "claude-prices.json").write_text(json.dumps(PRICES))


def test_close_out_sheets_tables_and_facts(project, capsys):
    close_out_files(project)
    write_model(project, model(close_out={}))
    code, out = run(project, "demo.estimate.json", capsys=capsys)
    assert code == 0, out
    claude = out["figures"]["claude"]
    assert (claude["calls"], claude["usd"], claude["unpriced_models"]) == (16, CLAUDE_USD, [])
    assert out["figures"]["grand_total"]["total"] == round((134608.35 + CLAUDE_USD) * 1.1, 2)
    wb = openpyxl.load_workbook(out["workbook"])
    assert wb.sheetnames[-5:] == ["Claude Prices", "Claude Usage Detail", "Claude Usage", "Project Timeline", "Sources & Gaps"]
    tables = {t for ws in wb for t in ws.tables}
    assert {"tblInputs", "tblTeam", "tblCostSummary", "tblEnvDev", "tblEnvProd", "tblRateCard", "tblOtherCosts",
            "tblClaudeUsage", "tblClaudeUsageDetail", "tblClaudePrices", "tblTimeline"} <= tables
    assert wb["Claude Usage Detail"]["F6"].value == "claude-haiku-4-5"
    assert '"="&$A5' in wb["Claude Usage"]["H5"].value
    facts = Path(out["facts"]).read_text().splitlines()
    assert facts[0] == "estimate,currency,category,item,monthly,delivery,run,total"
    assert any(line.startswith("demo,USD,claude,Claude API usage,,18.0") for line in facts)


def test_close_out_formulas_match(project, capsys):
    formulas = pytest.importorskip("formulas")
    close_out_files(project)
    write_model(project, model(close_out={}))
    _, out = run(project, "demo.estimate.json", capsys=capsys)
    sol = formulas.ExcelModel().loads(out["workbook"]).finish().calculate()
    values = {str(k).split("]")[-1].upper(): v.value[0][0] for k, v in sol.items() if hasattr(v, "value")}
    usage_total = [v for k, v in values.items() if k.startswith("CLAUDE USAGE'!H") and isinstance(v, float)]
    assert max(usage_total) == pytest.approx(CLAUDE_USD)  # the <synthetic> row must not sum every model
    grand = [v for k, v in values.items() if k.startswith("OVERALL'!G") and isinstance(v, float)]
    assert max(grand) == pytest.approx(out["figures"]["grand_total"]["total"], abs=0.01)


def test_close_out_memo_currency_and_unpriced(project, capsys):
    close_out_files(project)
    (project / "docs/token_usage/claude_usage.csv").write_text(
        USAGE + "story,PROJ-1,1.1,Login,claude-mystery-9,2026-09-07T09:00:00Z,2026-09-07T09:00:00Z,1,5,0,0,0,0,0\n")
    write_model(project, model(close_out={"in_totals": False}))
    _, out = run(project, "demo.estimate.json", capsys=capsys)
    assert out["figures"]["claude"]["unpriced_models"] == ["claude-mystery-9"]
    assert out["figures"]["grand_total"]["total"] == 148069.19  # a memo, not in the totals
    labels = [c.value for c in openpyxl.load_workbook(out["workbook"])["Overall"]["A"] if c.value]
    assert any(str(v).startswith("Memo: Claude API usage") for v in labels)

    card = project / "_bmad" / "memory" / "agent-scrooge" / "rate-card.json"
    card.write_text(card.read_text().replace('"USD"', '"AED"'))
    write_model(project, model(currency="AED", cloud_currency="USD", fx_rate=3.6725, fx_source="t", close_out={}))
    code, out = run(project, "demo.estimate.json", "--check", capsys=capsys)
    assert code == 1 and any("close_out.fx_rate" in e for e in out["errors"])


def test_shipped_example_still_builds(capsys):
    example = Path(__file__).resolve().parents[2] / "assets" / "examples" / "falcon-portal"
    code = build_estimate.main([str(example), "falcon-portal.estimate.json", "--check"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out
    assert out["figures"]["currency"] == "USD"
    assert out["figures"]["grand_total"]["total"] == 462615.59
    assert out["figures"]["claude"]["calls"] == 2614
