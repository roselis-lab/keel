"""The example report for the evidence links on the report page stays a valid report.

tests/fixtures/evidence-links is a reports folder: `REPORTS_DIR=tests/fixtures/evidence-links keel up`
opens it, and /reports/demo-evidence/2026-11-13 shows each kind of mark the page turns
into a link (web/src/components/Evidence.tsx; the marks are tested in web/test). If the
schema moves on and the example no longer loads, this says so before someone opens it.
"""
import re
from pathlib import Path

import keel.config
from keel.services import report_service

FIXTURE = Path(__file__).parent / "fixtures" / "evidence-links"


def test_the_example_report_loads_and_carries_every_kind_of_mark(monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(FIXTURE))
    r = report_service.get_report("demo-evidence", "2026-11-13")["report"]
    held = {e["id"] for e in r["evidence"]}
    prose = " ".join(
        [f["scenario"] + " " + f["vulnerability"] + " " + f["risk"]["reasoning"] for f in r["findings"]]
        + [d["reason"] for d in r["discarded"]]
    )
    marks = {int(n) for n in re.findall(r"(?<![\w\]])\[(\d+)\]", prose)}
    assert marks & held, "a mark on evidence the report holds"
    assert marks - held, "a mark on evidence the report does not hold"
    assert re.search(r"\]\(#ev-\d+\)", prose) and re.search(r"(?<!\()#ev-\d+", prose), "both #ev-n forms"
    assert re.search(r"\[\d+, \d+\]", prose), "a list of marks"
