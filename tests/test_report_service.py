"""Access to reports/.

Unlike the catalog, reports are NOT loaded into the in-memory Store — they're an
archive, read fresh off disk per call. So these tests point `settings.reports_dir` at
a temp directory (the same seam `test_catalog_dir_override.py` uses for the catalog)
rather than installing a store.

The write path guards one rule above all: a final report is a dated record and is
never rewritten. Everything about `save_report` / `finalize_report` / `reopen_report`
below is there to keep that true.
"""
import yaml

import keel.config
from keel.services import report_service

VALID_REPORT = {
    "system_id": "checkout-agent",
    "system_name": "Checkout Agent",
    "system_description": "Handles checkout for the storefront.",
    "date": "2026-08-26",
    "assessor": "Jane Doe <jane@example.com>",
    "findings": [],
    "discarded": [],
}


def _write_report(reports_dir, system_id, date, extra=None):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(VALID_REPORT, system_id=system_id, date=date)
    if extra:
        payload.update(extra)
    (d / f"{date}.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def _write_broken(reports_dir, system_id, date):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{date}.yaml").write_text("not: [valid, yaml, :::", encoding="utf-8")


def test_reports_dir_honors_override(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service._reports_dir() == tmp_path


def test_list_reports_missing_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path / "nope"))
    assert report_service.list_reports() == []


def test_list_reports_empty_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.list_reports() == []


def test_list_reports_groups_by_system_with_latest_date(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"delta_summary": "added a new tool"})
    _write_report(tmp_path, "support-bot", "2026-07-01")

    by_id = {i["system_id"]: i for i in report_service.list_reports()}
    assert set(by_id) == {"checkout-agent", "support-bot"}
    assert by_id["checkout-agent"]["latest_date"] == "2026-08-26"
    assert by_id["checkout-agent"]["report_count"] == 2
    assert by_id["checkout-agent"]["has_delta"] is True
    assert by_id["support-bot"]["report_count"] == 1
    assert by_id["support-bot"]["has_delta"] is False


def test_list_reports_keywords_carry_the_ids_a_search_would_look_for(tmp_path, monkeypatch):
    """Filtering a handful of system NAMES is not worth a search box; finding which
    systems still owe a given control is."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"findings": [
        _finding(id="T-TOOL-ABUSE", requirements=[_req("CTRL-HACT-CRITICAL")]),
    ], "discarded": [{"id": "T-SSRF", "reason": "no url-taking tool"}]})

    kw = report_service.list_reports()[0]["keywords"]

    assert "ctrl-hact-critical" in kw
    assert "t-tool-abuse" in kw
    assert "t-ssrf" in kw               # a ruled-out candidate is still worth finding
    assert "handles checkout" in kw     # and the description


def test_list_reports_reports_the_latest_status(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10", {"status": "final"})
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    assert report_service.list_reports()[0]["status"] == "draft"


def test_list_reports_skips_a_malformed_file(tmp_path, monkeypatch):
    """One bad file must not take down the whole listing — this is an archive of many
    independent files, not a single validated catalog."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    _write_broken(tmp_path, "broken-system", "2026-08-01")

    assert [i["system_id"] for i in report_service.list_reports()] == ["checkout-agent"]


def test_list_reports_skips_a_schema_violating_file(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    d = tmp_path / "wrong-shape"
    d.mkdir()
    (d / "2026-08-01.yaml").write_text(yaml.safe_dump({"system_id": "x"}), encoding="utf-8")

    assert [i["system_id"] for i in report_service.list_reports()] == ["checkout-agent"]


def test_get_report_series_sorted_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    assert [r["date"] for r in report_service.get_report_series("checkout-agent")] == [
        "2026-08-26", "2026-05-10",
    ]


def test_get_report_series_unknown_system_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.get_report_series("no-such-system") == []


def test_get_report_returns_parsed_report(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    result = report_service.get_report("checkout-agent", "2026-08-26")
    assert result["success"] is True
    assert result["report"]["system_name"] == "Checkout Agent"


def test_get_report_missing_file_returns_error_not_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    result = report_service.get_report("no-such-system", "2026-08-26")
    assert result["success"] is False
    assert "error" in result


def test_get_report_malformed_file_returns_error_not_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_broken(tmp_path, "broken-system", "2026-08-01")
    result = report_service.get_report("broken-system", "2026-08-01")
    assert result["success"] is False
    assert "error" in result


# --------------------------------------------------------------------------- #
# Write path: draft -> final
# --------------------------------------------------------------------------- #
def test_a_report_without_a_status_reads_as_a_draft(tmp_path, monkeypatch):
    """Every report already on disk predates the status field; none of them is frozen."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    assert report_service.get_report("checkout-agent", "2026-08-26")["report"]["status"] == "draft"


def test_save_report_replaces_a_draft(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    body = dict(VALID_REPORT, system_description="Now also issues refunds.")

    result = report_service.save_report("checkout-agent", "2026-08-26", body)

    assert result["success"] is True
    reread = report_service.get_report("checkout-agent", "2026-08-26")["report"]
    assert reread["system_description"] == "Now also issues refunds."


def test_save_report_refuses_a_final_report(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})

    result = report_service.save_report(
        "checkout-agent", "2026-08-26", dict(VALID_REPORT, system_name="Rewritten")
    )

    assert result["success"] is False
    assert "final" in result["error"]
    assert report_service.get_report("checkout-agent", "2026-08-26")["report"][
        "system_name"
    ] == "Checkout Agent"


def test_save_report_refuses_a_body_that_moves_the_report(tmp_path, monkeypatch):
    """The path is the identity — a save of one report must not land on another."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    moved = report_service.save_report(
        "checkout-agent", "2026-08-26", dict(VALID_REPORT, date="2026-01-01")
    )
    renamed = report_service.save_report(
        "checkout-agent", "2026-08-26", dict(VALID_REPORT, system_id="other-system")
    )

    assert moved["success"] is False
    assert renamed["success"] is False


def test_save_report_cannot_finalize_through_the_body(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    result = report_service.save_report(
        "checkout-agent", "2026-08-26", dict(VALID_REPORT, status="final")
    )

    assert result["success"] is False
    assert "finalize" in result["error"]


def test_save_report_rejects_an_invalid_body(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    result = report_service.save_report("checkout-agent", "2026-08-26", {"system_id": "x"})

    assert result["success"] is False
    assert result["errors"]


def test_save_report_will_not_create_a_missing_report(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.save_report("ghost", "2026-08-26", VALID_REPORT)["success"] is False


def test_finalize_freezes_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    assert report_service.finalize_report("checkout-agent", "2026-08-26")["report"]["status"] == "final"
    again = report_service.finalize_report("checkout-agent", "2026-08-26")
    assert again["success"] is True
    assert again["report"]["status"] == "final"


def test_correct_unlocks_a_final_report_without_moving_its_date(tmp_path, monkeypatch):
    """Fixing a mistake in the record is not a re-assessment — nothing was looked at
    again, so moving the date would misstate when the work was done."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})

    result = report_service.correct_report("checkout-agent", "2026-08-26")

    assert result["report"]["status"] == "draft"
    assert result["report"]["date"] == "2026-08-26"
    assert [r["date"] for r in report_service.get_report_series("checkout-agent")] == ["2026-08-26"]
    # and now it saves
    assert report_service.save_report(
        "checkout-agent", "2026-08-26", dict(VALID_REPORT, system_name="Fixed")
    )["success"] is True


def test_correct_on_an_already_editable_draft_is_a_no_op(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    assert report_service.correct_report("checkout-agent", "2026-08-26")["report"]["status"] == "draft"


def test_create_report_makes_an_empty_draft(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))

    result = report_service.create_report(
        "support-bot", "Support Bot", "Answers help-centre questions.",
        "Jane Doe <jane@example.com>", "2026-09-01",
    )

    assert result["report"]["status"] == "draft"
    assert result["report"]["findings"] == []
    assert report_service.get_report("support-bot", "2026-09-01")["success"] is True


def test_create_report_never_lands_on_an_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    result = report_service.create_report(
        "checkout-agent", "Something Else", "d", "a", "2026-08-26",
    )

    assert result["success"] is False
    assert report_service.get_report("checkout-agent", "2026-08-26")["report"][
        "system_name"
    ] == "Checkout Agent"


def test_create_report_rejects_an_unusable_system_id(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.create_report("Not A Slug", "n", "d", "a", "2026-09-01")["success"] is False
    assert report_service.create_report("ok-slug", "n", "d", "a", "01-09-2026")["success"] is False


def test_reopen_copies_a_final_report_into_a_new_draft(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})

    result = report_service.reopen_report("checkout-agent", "2026-08-26", today="2026-09-01")

    assert result["report"]["date"] == "2026-09-01"
    assert result["report"]["status"] == "draft"
    # the record it revises is untouched
    original = report_service.get_report("checkout-agent", "2026-08-26")["report"]
    assert original["status"] == "final"
    assert [r["date"] for r in report_service.get_report_series("checkout-agent")] == [
        "2026-09-01", "2026-08-26",
    ]


def test_reopen_refuses_to_clobber_todays_draft(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})
    _write_report(tmp_path, "checkout-agent", "2026-09-01", {"system_name": "Work in progress"})

    result = report_service.reopen_report("checkout-agent", "2026-08-26", today="2026-09-01")

    assert result["success"] is False
    assert report_service.get_report("checkout-agent", "2026-09-01")["report"][
        "system_name"
    ] == "Work in progress"


def test_reopen_defaults_to_today(tmp_path, monkeypatch):
    import datetime

    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})

    result = report_service.reopen_report("checkout-agent", "2026-08-26")

    assert result["report"]["date"] == datetime.date.today().isoformat()


# --------------------------------------------------------------------------- #
# Cross-system insights
# --------------------------------------------------------------------------- #
def _finding(**over):
    base = dict(
        id="T-TOOL-ABUSE", from_catalog=True, scenario="s",
        source={"who": "external-attacker", "motive": "m", "access": "a"},
        asset="a", attack_surface="user-agent", vulnerability="v",
        exploitation_complexity="low", harm="wrong-decision",
        risk={"likelihood": "high", "severity": "high", "reasoning": "r"},
        delta="new", requirements=[], ignored_mitigations=[],
    )
    base.update(over)
    return base


def _req(mitigation_id="CTRL-HACT-CRITICAL", **over):
    base = dict(mitigation_id=mitigation_id, coverage_status="needs_implementation")
    base.update(over)
    return base


def test_insights_on_an_empty_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    out = report_service.insights()
    assert out["systems"] == 0 and out["assessments"] == 0
    assert out["most_requested"] == [] and out["latest_date"] is None


def test_insights_counts_a_control_once_per_system(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    reqs = [_req(), _req()]                      # asked twice within ONE report
    _write_report(tmp_path, "checkout-agent", "2026-08-26",
                  {"findings": [_finding(requirements=reqs)]})
    _write_report(tmp_path, "support-bot", "2026-08-26",
                  {"findings": [_finding(requirements=[_req()])]})

    top = report_service.insights()["most_requested"][0]

    assert top["mitigation_id"] == "CTRL-HACT-CRITICAL"
    assert top["systems"] == ["checkout-agent", "support-bot"]


def test_insights_reads_only_each_systems_latest_report(tmp_path, monkeypatch):
    """An older assessment's asks may already be done; counting them keeps reporting
    work that is finished."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10",
                  {"findings": [_finding(requirements=[_req("CTRL-OLD-ASK")])]})
    _write_report(tmp_path, "checkout-agent", "2026-08-26",
                  {"findings": [_finding(requirements=[_req("CTRL-NEW-ASK")])]})

    out = report_service.insights()

    assert [m["mitigation_id"] for m in out["most_requested"]] == ["CTRL-NEW-ASK"]
    assert out["systems"] == 1
    assert out["assessments"] == 2      # the archive is still counted in full


def test_insights_skips_requirements_that_do_not_ship(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"findings": [_finding(requirements=[
        _req("CTRL-COVERED", coverage_status="already_covered", coverage_note="the gateway does it"),
        _req("CTRL-DROPPED", included=False),
        _req("CTRL-WANTED"),
    ])]})

    assert [m["mitigation_id"] for m in report_service.insights()["most_requested"]] == ["CTRL-WANTED"]


def test_insights_collects_what_the_catalog_does_not_carry(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"findings": [
        _finding(id="T-NOVEL", from_catalog=False, requirements=[
            _req(mitigation_id=None, description="Check the warehouse return record."),
        ]),
    ]})

    kinds = {o["kind"]: o for o in report_service.insights()["off_catalog"]}

    assert kinds["threat"]["label"] == "T-NOVEL"
    assert kinds["control"]["label"] == "Check the warehouse return record."


def test_insights_separates_confirmed_from_ruled_out(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"findings": [_finding()]})
    _write_report(tmp_path, "support-bot", "2026-08-26", {
        "findings": [],
        "discarded": [{"id": "T-TOOL-ABUSE", "reason": "no tool moves money here"}],
    })

    row = {a["id"]: a for a in report_service.insights()["threat_activity"]}["T-TOOL-ABUSE"]

    assert row["confirmed"] == ["checkout-agent"]
    assert row["ruled_out"] == ["support-bot"]


def test_insights_severity_mix_and_per_system_load(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"findings": [
        _finding(requirements=[_req("CTRL-A"), _req("CTRL-B")]),
        _finding(id="T-DATA-LEAK", risk={"likelihood": "low", "severity": "medium", "reasoning": "r"}),
    ]})
    _write_report(tmp_path, "support-bot", "2026-08-26", {"findings": [
        _finding(id="T-DOS", risk={"likelihood": "low", "severity": "low", "reasoning": "r"}),
    ]})

    out = report_service.insights()

    assert out["severity_mix"] == {"high": 1, "medium": 1, "low": 1}
    # worst first, so the chart is already sorted for a top-down read
    assert [s["system_id"] for s in out["per_system"]] == ["checkout-agent", "support-bot"]
    assert out["per_system"][0]["severity"] == {"high": 1, "medium": 1, "low": 0}
    assert out["per_system"][0]["open_requirements"] == 2
    assert out["per_system"][0]["findings"] == 2
    assert out["per_system"][1]["severity"] == {"high": 0, "medium": 0, "low": 1}
    assert out["per_system"][1]["open_requirements"] == 0


def test_insights_ranks_the_system_with_the_most_high_findings_first(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    low = {"likelihood": "low", "severity": "low", "reasoning": "r"}
    # more findings overall, but none of them high
    _write_report(tmp_path, "aaa-noisy", "2026-08-26", {"findings": [
        _finding(risk=low), _finding(id="T-DOS", risk=low), _finding(id="T-SSRF", risk=low),
    ]})
    _write_report(tmp_path, "zzz-serious", "2026-08-26", {"findings": [_finding()]})

    assert [s["system_id"] for s in report_service.insights()["per_system"]] == [
        "zzz-serious", "aaa-noisy",
    ]


def test_insights_lists_unfinalized_drafts(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"status": "final"})
    _write_report(tmp_path, "support-bot", "2026-08-26")

    out = report_service.insights()

    assert [d["system_id"] for d in out["drafts"]] == ["support-bot"]
    assert out["latest_date"] == "2026-08-26"


def test_ids_that_would_escape_the_archive_are_refused(tmp_path, monkeypatch):
    """system_id is a folder name and date is a file name, both straight off the URL."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")

    assert report_service.get_report("../../etc", "passwd")["success"] is False
    assert report_service.get_report("checkout-agent", "../../../secrets")["success"] is False
    assert report_service.get_report_series("../..") == []
    assert report_service.save_report("../evil", "2026-08-26", VALID_REPORT)["success"] is False
