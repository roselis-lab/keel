"""The weekly freshness check, run on recorded upstream answers: no network here.

The check exists so a pinned source that moved on turns into one issue per source, and
so nothing else does - a source that is current, or a publisher that could not be
reached, must not open anything."""
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures" / "coverage_freshness"

_spec = importlib.util.spec_from_file_location("coverage_freshness", ROOT / "scripts" / "coverage_freshness.py")
cf = importlib.util.module_from_spec(_spec)
sys.modules["coverage_freshness"] = cf
_spec.loader.exec_module(cf)

# URL fragment -> fixture file. Anything else is a network call the test did not expect.
ROUTES = {
    "atlas-data/releases/latest": "atlas_release.json",
    "atlas-data/v2026.11/dist/manifest.yaml": "atlas_manifest.yaml",
    "atlas-data/v2026.11/dist/v6/ATLAS-2026.11.yaml": "atlas_data.yaml",
    "genai.owasp.org/wp-json/wp/v2/resource": "genai_resources.json",
    "www-project-mcp-top-10/main/tab_top10.md": "mcp_tab.md",
    "saif-data/commits": "saif_commits.json",
    "eur-lex.europa.eu/legal-content/EN/ALL/": "eurlex.html",
}


def fake_fetch(url: str) -> str:
    for frag, name in ROUTES.items():
        if frag in url:
            return (FIX / name).read_text(encoding="utf-8")
    raise AssertionError(f"unexpected fetch {url}")


def write_source(root: Path, sid: str, title: str, version: str, refs: list[str], **extra) -> None:
    d = root / "coverage"
    d.mkdir(parents=True, exist_ok=True)
    doc = {"source": {"id": sid, "title": title, "kind": "best_practice", "version": version,
                      "url": extra.pop("url", "https://example.com/"), "checked": "2026-11-12",
                      "entry_count": len(refs)},
           "entries": [{"ref": r, "title": r, "state": "gap"} for r in refs]}
    (d / f"{sid}.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")


def by_id(results):
    return {r.source_id: r for r in results}


@pytest.fixture
def catalog(tmp_path):
    write_source(tmp_path, "mitre-atlas", "MITRE ATLAS", "2026.10", ["AML.T0000", "AML.T0001"])
    write_source(tmp_path, "owasp-agentic", "OWASP Agentic", "2026", [f"ASI{i:02}" for i in range(1, 11)])
    write_source(tmp_path, "owasp-llm", "OWASP LLM", "2025", [f"LLM{i:02}" for i in range(1, 11)])
    write_source(tmp_path, "owasp-mcp", "OWASP MCP Top 10", "v0.1", [f"MCP{i:02}" for i in range(1, 11)])
    write_source(tmp_path, "google-saif", "SAIF", "saif-data @ 2026-08-29", ["DP"])
    write_source(tmp_path, "eu-ai-act", "EU AI Act", "consolidated 2026-07-27", ["Art. 1"],
                 url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727")
    return tmp_path


def test_atlas_counts_new_and_withdrawn_techniques(catalog):
    r = by_id(cf.check_all(catalog, fake_fetch))["mitre-atlas"]
    assert r.outdated and r.latest == "2026.11"
    assert r.summary == "2026.10 → v2026.11: 2 techniques to map"
    body = cf.issue_body(r)
    assert "- AML.T0146 A Technique Added This Month" in body
    assert "- AML.T0001" in body                       # gone upstream, row still here
    assert "AML.T0000.000" not in body                 # sub-techniques are not rows


def test_atlas_calendar_version_is_newer_than_old_numbering():
    assert cf._calver("2026.10") > cf._calver("5.6.0")
    assert cf._calver("v2026.11") > cf._calver("2026.10")


def test_owasp_editions_by_year_and_crosswalks_ignored(catalog):
    res = by_id(cf.check_all(catalog, fake_fetch))
    assert res["owasp-llm"].outdated and res["owasp-llm"].latest == "2026"
    assert "owasp-genai-llm-top-10-2026" in cf.issue_body(res["owasp-llm"])
    # A 2027 crosswalk *about* the agentic list is not a new edition of it.
    assert not res["owasp-agentic"].outdated and res["owasp-agentic"].latest == "2026"


def test_mcp_version_from_list_page(catalog):
    r = by_id(cf.check_all(catalog, fake_fetch))["owasp-mcp"]
    assert r.outdated and r.latest == "v0.2"


def test_saif_and_eu_ai_act(catalog):
    res = by_id(cf.check_all(catalog, fake_fetch))
    assert res["google-saif"].outdated and res["google-saif"].latest == "saif-data @ 2026-09-30"
    assert not res["eu-ai-act"].outdated and res["eu-ai-act"].latest == "consolidated 20260727"


def test_unreachable_or_unknown_source_never_becomes_an_issue(tmp_path):
    write_source(tmp_path, "mitre-atlas", "MITRE ATLAS", "2026.10", ["AML.T0000"])
    write_source(tmp_path, "someone-else", "Some list", "1", ["X"])

    def down(url):
        raise OSError("network is down")

    res = by_id(cf.check_all(tmp_path, down))
    assert res["mitre-atlas"].error and not res["mitre-atlas"].outdated
    assert res["someone-else"].error == "no checker for this source"
    assert cf.plan_issues(list(res.values()), []) == []
    assert "could not check" in cf.report(list(res.values()))


def test_one_issue_per_source_created_then_updated_then_left(catalog):
    results = cf.check_all(catalog, fake_fetch)
    outdated = {r.source_id for r in results if r.outdated}
    assert outdated == {"mitre-atlas", "owasp-llm", "owasp-mcp", "google-saif"}

    first = cf.plan_issues(results, [])
    assert [a for a, _, _ in first] == ["create"] * 4

    # Open issues as GitHub would return them, one of them already current.
    atlas = next(r for r in results if r.source_id == "mitre-atlas")
    llm = next(r for r in results if r.source_id == "owasp-llm")
    open_issues = [
        {"number": 7, "title": cf.issue_title(atlas), "body": cf.issue_body(atlas)},
        {"number": 8, "title": "Coverage: OWASP LLM older text",
         "body": cf.MARKER.format(id="owasp-llm") + "\nstale"},
        {"number": 9, "title": "Unrelated", "body": "nothing to do with coverage"},
    ]
    plan = cf.plan_issues(results, open_issues)
    assert ("update", 8, {"title": cf.issue_title(llm), "body": cf.issue_body(llm)}) in plan
    assert all(n != 7 for _, n, _ in plan)              # identical: left alone
    assert sum(1 for a, _, _ in plan if a == "create") == 2


def test_real_catalog_has_a_checker_for_every_source():
    ids = {p.stem for p in (ROOT / "catalog" / "coverage").glob("*.yaml")}
    assert ids <= set(cf.CHECKERS), ids - set(cf.CHECKERS)
