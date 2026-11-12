"""Organisation facts: kept between assessments, read by each, written only by people.

The tests point `settings.org_dir` at a throwaway folder and state the files they assert
on. The shipped example is checked too, because it is the format's documentation.
"""
import subprocess
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

import keel.config
from keel import recheck as rc
from keel.mcp.tools.reports import list_reports
from keel.schemas.org import OrgFile
from keel.schemas.report import Report
from keel.services import org_service

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "org" / "llm-gateway.yaml"


def _fact(**over):
    fact = {"id": "strips-pii", "statement": "The gateway removes e-mail addresses.",
            "confirmed_by": "Dana", "confirmed_on": "2026-09-14",
            "documents": ["https://wiki.example/gateway"]}
    return {**fact, **over}


def _file(*facts, **over):
    return {"title": "Gateway", "kind": "platform", "about": "The model proxy.",
            "facts": list(facts) or [_fact()], **over}


@pytest.fixture
def org_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "org_dir", str(tmp_path))

    def write(name, data):
        text = data if isinstance(data, str) else yaml.safe_dump(data)
        (tmp_path / f"{name}.yaml").write_text(text, encoding="utf-8")
    return write


def test_the_shipped_example_is_a_valid_file():
    org = org_service.load_file(EXAMPLE)
    assert {f.id for f in org.facts} == {"provider-allowlist", "restricted-stays-internal"}
    assert org.evidence[0].kind == "read"


def test_a_fact_must_rest_on_a_document_or_code():
    with pytest.raises(ValidationError, match="rests on"):
        OrgFile(**_file(_fact(documents=[])))


def test_a_fact_needs_who_confirmed_it_and_when():
    for missing in ("confirmed_by", "confirmed_on"):
        fact = _fact()
        del fact[missing]
        with pytest.raises(ValidationError):
            OrgFile(**_file(fact))


def test_code_evidence_has_the_report_shape():
    bad = _fact(documents=[], evidence=[{"id": 1, "kind": "read", "quote": "x", "path": "a.py"}])
    with pytest.raises(ValidationError, match="commit"):
        OrgFile(**_file(bad))


def test_ids_do_not_repeat_in_a_file():
    with pytest.raises(ValidationError, match="fact ids repeat"):
        OrgFile(**_file(_fact(), _fact()))


def test_no_folder_means_no_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "org_dir", str(tmp_path / "nope"))
    assert org_service.list_facts()["facts"] == []


def test_facts_are_listed_with_the_ref_a_report_cites(org_dir):
    org_dir("gateway", _file(_fact(systems=["support-bot"])))
    facts = org_service.list_facts()["facts"]
    assert facts == [{
        "ref": "org:gateway#strips-pii", "about": "Gateway (platform)",
        "statement": "The gateway removes e-mail addresses.", "confirmed_by": "Dana",
        "confirmed_on": "2026-09-14", "documents": ["https://wiki.example/gateway"],
        "code_evidence": 0, "systems": ["support-bot"],
    }]


def test_a_broken_file_is_named_and_the_rest_still_listed(org_dir):
    org_dir("gateway", _file())
    org_dir("policy", "title: [unclosed")
    org_dir("Bad_Name", _file())
    out = org_service.list_facts()
    assert [f["ref"] for f in out["facts"]] == ["org:gateway#strips-pii"]
    assert {b["file"] for b in out["broken"]} == {"policy.yaml", "Bad_Name.yaml"}


async def test_list_reports_carries_the_facts(org_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path / "reports"))
    org_dir("gateway", _file())
    out = await list_reports()
    assert out["reports"] == []
    assert out["org_facts"]["facts"][0]["ref"] == "org:gateway#strips-pii"


def _report(reason):
    return Report(system_id="halo", system_name="Halo", system_description="d", date="2026-11-12",
                  assessor="a", discarded=[{"id": "T-1", "reason": reason}])


def test_a_cited_fact_that_exists_draws_no_advice(org_dir):
    org_dir("gateway", _file())
    assert org_service.unknown_refs(_report("Ruled out by org:gateway#strips-pii.")) == []


def test_a_cited_fact_nobody_stored_is_said(org_dir):
    org_dir("gateway", _file())
    advice = org_service.unknown_refs(_report("org:gateway#strips-all and org:policy#x"))
    assert len(advice) == 2
    assert "org:gateway#strips-all" in advice[0] and "org:policy#x" in advice[1]


def test_recheck_reads_an_org_file_like_a_report(tmp_path, capsys):
    repo = tmp_path / "gw"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    (repo / "allow.py").write_text("ALLOW = {'a'}\n", encoding="utf-8")
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "x"], check=True)
    ev = {"id": 1, "kind": "read", "commit": "4043f65", "path": "allow.py", "lines": "1",
          "quote": "ALLOW = {'a'}"}
    path = tmp_path / "gateway.yaml"
    path.write_text(yaml.safe_dump(_file(_fact(documents=[], evidence=[ev]))), encoding="utf-8")
    rc.main([str(path), "--repo", str(repo)])
    assert "[1] in place" in capsys.readouterr().out
