"""`keel reports migrate`: fields the schema does not know move into an extension's section,
nothing is lost, and a second run changes nothing.

Every report and diagram here is made up by the test; the extension is "example".
"""
import sys

import pytest
import yaml

import keel.config
from keel import migrate
from keel.schemas.report import Report
from tests.test_atlassian import finding, report

DATE = "2026-11-07"
OLD_DIAGRAM = {"parts": [{"id": "gw", "label": "Gateway"}], "flows": []}
FOLDER_DIAGRAM = {"parts": [{"id": "db", "label": "Orders"}], "flows": []}
HANDOFF = {"ticket": "OPS-12", "team": "payments"}


def _old_report(system_id):
    """A report written while these fields were part of the schema: one on the report, one
    on a finding, two on a requirement."""
    f = finding("T-A", weight=["counted twice in the old layout"])
    # A copy: the helper's requirement is shared with other tests.
    f["requirements"] = [{**f["requirements"][0], "handoff": HANDOFF,
                          "old_command": ["make", "check-refunds"]}]
    return report(system_id=system_id, date=DATE, findings=[f], system_diagram=OLD_DIAGRAM)


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """A reports folder and a diagrams folder, both made up."""
    root, diagrams = tmp_path / "reports", tmp_path / "diagrams"
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(root))

    def put(folder, system_id, doc):
        path = folder / system_id / f"{DATE}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    files = {
        "old": put(root, "old-agent", _old_report("old-agent")),
        "plain": put(root, "plain-agent", report(system_id="plain-agent", date=DATE)),
        "untouched": put(root, "quiet-agent", report(system_id="quiet-agent", date=DATE)),
    }
    put(diagrams, "plain-agent", FOLDER_DIAGRAM)
    put(diagrams, "old-agent", FOLDER_DIAGRAM)    # the report has one already: kept
    put(diagrams, "ghost-agent", FOLDER_DIAGRAM)  # no report for it
    return root, diagrams, files


def _run(diagrams=None, **kw):
    lines = []
    code = migrate.migrate("example", diagrams, say=lines.append, **kw)
    return code, lines


def _read(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_unknown_fields_at_all_three_levels_move_into_the_section(archive):
    root, diagrams, files = archive
    before_untouched = files["untouched"].read_bytes()

    code, lines = _run(diagrams)
    assert code == 0, lines

    old = _read(files["old"])
    assert "system_diagram" not in old
    assert "weight" not in old["findings"][0]
    assert not {"handoff", "old_command"} & set(old["findings"][0]["requirements"][0])
    assert old["extensions"] == {"example": {
        "system_diagram": OLD_DIAGRAM,
        "findings": {"T-A": {"weight": ["counted twice in the old layout"]}},
        "requirements": {"T-A/0": {"handoff": HANDOFF, "old_command": ["make", "check-refunds"]}},
    }}
    assert old["status"] == "final"   # moving data is not an edit of the assessment
    Report(**old)

    assert _read(files["plain"])["extensions"] == {"example": {"system_diagram": FOLDER_DIAGRAM}}
    assert files["untouched"].read_bytes() == before_untouched

    assert lines[-1] == "2 reports changed, 0 not migrated"
    assert "skipped diagram ghost-agent/2026-11-07: no such report" in lines


def test_a_second_run_changes_nothing(archive):
    root, diagrams, files = archive
    assert _run(diagrams)[0] == 0
    after_first = {k: p.read_bytes() for k, p in files.items()}

    code, lines = _run(diagrams)
    assert code == 0
    assert {k: p.read_bytes() for k, p in files.items()} == after_first
    assert lines[-1] == "0 reports changed, 0 not migrated"


def test_a_dry_run_writes_nothing(archive):
    root, diagrams, files = archive
    before = {k: p.read_bytes() for k, p in files.items()}
    code, lines = _run(diagrams, dry_run=True)
    assert code == 0
    assert {k: p.read_bytes() for k, p in files.items()} == before
    assert lines[-1] == "2 reports would change, 0 not migrated"


def test_a_field_already_in_the_section_with_another_value_stops_that_report(archive):
    root, _, files = archive
    doc = _old_report("clash-agent")
    doc["extensions"] = {"example": {"system_diagram": FOLDER_DIAGRAM}}
    path = root / "clash-agent" / f"{DATE}.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    before = path.read_bytes()

    code, lines = _run()
    assert code == 1
    assert path.read_bytes() == before
    assert any(line.startswith("not migrated clash-agent/2026-11-07: system_diagram") for line in lines)
    assert lines[-1] == "1 report changed, 1 not migrated"   # the others still went through


def test_a_report_that_would_come_out_invalid_is_not_written_and_is_named(archive):
    root, _, _ = archive
    doc = _old_report("broken-agent")
    doc["evidence"][0]["stray"] = "a field on evidence is not one the command moves"
    path = root / "broken-agent" / f"{DATE}.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    before = path.read_bytes()

    code, lines = _run()
    assert code == 1
    assert path.read_bytes() == before
    assert any(line.startswith("not migrated broken-agent/2026-11-07:") for line in lines)


def test_keel_reports_migrate_runs_from_the_command_line(archive, monkeypatch, capsys):
    root, diagrams, files = archive
    from keel.mcp import server

    monkeypatch.setattr(sys, "argv", ["keel", "reports", "migrate", "--extension", "example",
                                      "--diagrams", str(diagrams)])
    with pytest.raises(SystemExit) as e:
        server.main()
    assert e.value.code == 0
    assert "2 reports changed, 0 not migrated" in capsys.readouterr().out
    assert "example" in _read(files["old"])["extensions"]
