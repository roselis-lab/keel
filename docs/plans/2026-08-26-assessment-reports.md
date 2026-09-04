# Assessment Reports Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Read-only backend + UI for browsing assessment reports written to `reports/<system_id>/<date>.yaml`, per `docs/plans/2026-08-26-assessment-reports-design.md`.

**Architecture:** A new Pydantic `Report` schema (mirroring the YAML shape, reusing `Harm`/`Surface`/`Source` from `keel/schemas/threat.py`); a `report_service` that reads `reports/` fresh off disk per call (NOT loaded into the hot in-memory `Store` — reports are an archive, not editable catalog data); three new read-only routes; a fifth UI screen ("Reports") that renders a report natively and builds two copy-to-clipboard markdown variants client-side. No write path anywhere in this plan — reports are authored by the `assess-genai-with-library` skill directly via the Write tool (a separate, non-code follow-up, out of scope here).

**Tech Stack:** FastAPI + Pydantic (backend), vanilla JS (frontend, no build step), pytest (backend tests), manual Browser-pane verification (frontend).

**Out of scope (do not implement here):** the `assess-genai-with-library` skill changes (system-identification step, the report-writing final step) — those are prose edits to a `SKILL.md`, not code, and aren't unit-testable; track as a separate follow-up. Also out of scope: any `keel validate` integration for `reports/` (explicitly rejected in the design).

---

### Task 1: Report schema

**Files:**
- Create: `keel/schemas/report.py`
- Test: `tests/test_report_schema.py`

**Context:** Mirrors the YAML shape in the design doc. Reuses `Harm`, `Surface`, `Source` from `keel/schemas/threat.py` instead of inventing parallel vocabularies. Two conditional-requirement validators on `Requirement`, following the same `model_validator(mode="after")` pattern already used for `Implementation.coverage`/`covers` in `keel/schemas/mitigation.py` (read that file first for the exact style). `Discarded` deliberately does NOT share `Finding`'s chain fields (id + reason only) — the design doc calls this out explicitly as a fix to an earlier, over-heavy draft.

**Step 1: Write the failing tests**

```python
# tests/test_report_schema.py
import pytest
from pydantic import ValidationError

from keel.schemas.report import (
    DialogueEntry, Discarded, Finding, IgnoredMitigation, Report, Requirement,
)


def _requirement(**over):
    base = dict(mitigation_id="CTRL-URL-ALLOWLIST", coverage_status="needs_implementation")
    base.update(over)
    return Requirement(**base)


def test_requirement_with_mitigation_id_needs_no_description():
    r = _requirement()
    assert r.description is None


def test_requirement_without_mitigation_id_requires_description():
    with pytest.raises(ValidationError):
        _requirement(mitigation_id=None)


def test_requirement_without_mitigation_id_and_description_is_valid():
    r = _requirement(mitigation_id=None, description="Restrict outbound requests to an allowlist.")
    assert r.description == "Restrict outbound requests to an allowlist."


def test_requirement_rejects_description_when_mitigation_id_set():
    with pytest.raises(ValidationError):
        _requirement(description="redundant — mitigation_id is already set")


def test_requirement_already_covered_requires_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="already_covered")


def test_requirement_partial_requires_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="partial")


def test_requirement_already_covered_with_note_is_valid():
    r = _requirement(coverage_status="already_covered", coverage_note="Closed by a shared Vault instance.")
    assert r.coverage_note == "Closed by a shared Vault instance."


def test_requirement_needs_implementation_rejects_stray_coverage_note():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="needs_implementation", coverage_note="shouldn't be here")


def test_requirement_rejects_bad_coverage_status_enum():
    with pytest.raises(ValidationError):
        _requirement(coverage_status="mostly_fine")


def test_discarded_has_no_chain_fields():
    d = Discarded(id="T-XSS", reason="output is plain JSON, no render path")
    assert d.model_dump() == {"id": "T-XSS", "reason": "output is plain JSON, no render path"}
    with pytest.raises(ValidationError):
        Discarded(id="T-XSS", reason="...", asset="should not be accepted")


def _finding(**over):
    base = dict(
        id="T-SSRF", from_catalog=True, scenario="an attacker reaches an internal service via SSRF",
        source={"who": "external-attacker", "motive": "recon", "access": "public API"},
        asset="internal metadata endpoint", attack_surface="agent-environment",
        vulnerability="tool builds a URL from unvalidated model output",
        exploitation_complexity="medium", harm="data-exposed",
        risk={"likelihood": "medium", "severity": "high", "reasoning": "reachable, no compensating control"},
        delta="new attack surface introduced by the outbound-fetch tool",
    )
    base.update(over)
    return Finding(**base)


def test_finding_parses_with_catalog_enums():
    f = _finding()
    assert f.harm == "data-exposed"
    assert f.attack_surface == "agent-environment"


def test_finding_rejects_bad_harm_enum():
    with pytest.raises(ValidationError):
        _finding(harm="not-a-real-harm")


def test_finding_rejects_bad_exploitation_complexity():
    with pytest.raises(ValidationError):
        _finding(exploitation_complexity="extreme")


def test_finding_carries_requirements_and_ignored_mitigations():
    f = _finding(
        requirements=[{"mitigation_id": "CTRL-URL-ALLOWLIST", "coverage_status": "needs_implementation"}],
        ignored_mitigations=[{"mitigation_id": "CTRL-SOME-OTHER", "reason": "no outbound egress on this system"}],
    )
    assert isinstance(f.requirements[0], Requirement)
    assert isinstance(f.ignored_mitigations[0], IgnoredMitigation)


def test_report_parses_minimal():
    r = Report(
        system_id="checkout-agent", system_name="Checkout Agent",
        system_description="Handles checkout for the storefront.",
        date="2026-08-26", assessor="Jane Doe <jane@example.com>",
        findings=[_finding().model_dump()],
        discarded=[{"id": "T-XSS", "reason": "no render path"}],
        dialogue=[{"question": "q", "answer": "a", "impact": "i"}],
    )
    assert r.system_id == "checkout-agent"
    assert len(r.findings) == 1


def test_report_rejects_unknown_top_level_field():
    with pytest.raises(ValidationError):
        Report(
            system_id="x", system_name="X", system_description="d", date="2026-08-26",
            assessor="a", not_a_real_field="oops",
        )
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_report_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'keel.schemas.report'`.

**Step 3: Write the implementation**

```python
# keel/schemas/report.py
"""Report schema: a persisted assess-genai-with-library run. Read-only from the app's
side — a report is written once by the skill (via the Write tool) and never edited
through this schema; it exists here purely to parse and validate on read.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keel.schemas.threat import Harm, Source, Surface

ExploitationComplexity = Literal["low", "medium", "high"]
Likelihood = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high", "critical"]
CoverageStatus = Literal["already_covered", "needs_implementation", "partial"]


class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    who: Source
    motive: str
    access: str


class RiskInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    likelihood: Likelihood
    severity: Severity
    reasoning: str


class Requirement(BaseModel):
    """One risk-reduction ask. Thin on purpose: a cataloged mitigation's `purpose` and
    its threat-link `rationale` already explain what/why — this only records the
    assessment-specific judgment (is it already covered here?) and, for anything not
    yet in the catalog, the actual ask."""

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str | None = None
    coverage_status: CoverageStatus
    coverage_note: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> "Requirement":
        if self.mitigation_id is None and not (self.description or "").strip():
            raise ValueError("description is required when mitigation_id is null")
        if self.mitigation_id is not None and self.description:
            raise ValueError("description only applies when mitigation_id is null (a catalog card already names it)")
        needs_note = self.coverage_status in ("already_covered", "partial")
        if needs_note and not (self.coverage_note or "").strip():
            raise ValueError("coverage_note is required when coverage_status is 'already_covered' or 'partial'")
        if not needs_note and self.coverage_note:
            raise ValueError("coverage_note only applies to 'already_covered' or 'partial'")
        return self


class IgnoredMitigation(BaseModel):
    """A mitigation linked to this threat in the catalog, but not used for this system."""

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str
    reason: str


class Discarded(BaseModel):
    """A threat candidate ruled out during analysis. Deliberately NOT the full Finding
    chain — a discard is an id + why, nothing more (see Finding for survived threats)."""

    model_config = ConfigDict(extra="forbid")
    id: str
    reason: str


class DialogueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
    answer: str
    impact: str


class Finding(BaseModel):
    """A threat that survived analysis, with its full chain."""

    model_config = ConfigDict(extra="forbid")
    id: str
    from_catalog: bool
    scenario: str
    source: SourceInfo
    asset: str
    attack_surface: Surface
    vulnerability: str
    exploitation_complexity: ExploitationComplexity
    harm: Harm
    risk: RiskInfo
    delta: str
    requirements: list[Requirement] = Field(default_factory=list)
    ignored_mitigations: list[IgnoredMitigation] = Field(default_factory=list)


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system_id: str
    system_name: str
    system_description: str
    date: str
    assessor: str
    delta_summary: str | None = None
    findings: list[Finding] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    dialogue: list[DialogueEntry] = Field(default_factory=list)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_report_schema.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add keel/schemas/report.py tests/test_report_schema.py
git commit -m "feat(reports): Report schema with conditional Requirement validators"
```

---

### Task 2: Reports directory setting

**Files:**
- Modify: `keel/config.py`
- Test: covered by Task 3's directory-override test (no standalone test needed for a plain settings field).

**Context:** Mirrors the existing `catalog_dir` override exactly (see `keel/config.py`), so tests can point reports at a temp directory the same way `tests/test_catalog_dir_override.py` does for the catalog.

**Step 1: Add the setting**

In `keel/config.py`, after the `catalog_dir` field:

```python
    # Optional override for the reports directory (env var: REPORTS_DIR). Empty = the
    # repo's own reports/, sibling to catalog/.
    reports_dir: str = ""
```

**Step 2: No isolated test — verified via Task 3's `test_get_reports_dir_honors_override` test.**

**Step 3: Commit**

```bash
git add keel/config.py
git commit -m "feat(config): add reports_dir override, mirroring catalog_dir"
```

---

### Task 3: Report service (read-only, off-disk, not in the hot Store)

**Files:**
- Create: `keel/services/report_service.py`
- Test: `tests/test_report_service.py`

**Context:** Reports are an archive, not hot editable data — unlike `keel/store.py`'s `Store`, which loads `catalog/` into memory once and serves reads from there, this service re-reads `reports/` from disk on every call. There is no in-memory cache to invalidate, no `set_store()`-style test seam; tests instead monkeypatch `keel.config.settings.reports_dir`, exactly like `tests/test_catalog_dir_override.py` does for `catalog_dir`.

A malformed or unparseable report file must never take down a whole list request — skip it and keep going (this is an archive of many independent files, not a single validated catalog).

**Step 1: Write the failing tests**

```python
# tests/test_report_service.py
import yaml

import keel.config
from keel.services import report_service

VALID_REPORT = {
    "system_id": "checkout-agent", "system_name": "Checkout Agent",
    "system_description": "Handles checkout for the storefront.",
    "date": "2026-08-26", "assessor": "Jane Doe <jane@example.com>",
    "findings": [], "discarded": [], "dialogue": [],
}


def _write_report(reports_dir, system_id, date, data=None):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(VALID_REPORT, system_id=system_id, date=date)
    if data:
        payload.update(data)
    (d / f"{date}.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_get_reports_dir_honors_override(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service._reports_dir() == tmp_path


def test_list_reports_empty_dir_returns_empty_list(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    assert report_service.list_reports() == []


def test_list_reports_groups_by_system_with_latest_date(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26", {"delta_summary": "added a new tool"})
    _write_report(tmp_path, "support-bot", "2026-07-01")

    items = report_service.list_reports()
    by_id = {i["system_id"]: i for i in items}
    assert set(by_id) == {"checkout-agent", "support-bot"}
    assert by_id["checkout-agent"]["latest_date"] == "2026-08-26"
    assert by_id["checkout-agent"]["report_count"] == 2
    assert by_id["checkout-agent"]["has_delta"] is True
    assert by_id["support-bot"]["report_count"] == 1
    assert by_id["support-bot"]["has_delta"] is False


def test_list_reports_skips_a_malformed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    bad_dir = tmp_path / "broken-system"
    bad_dir.mkdir()
    (bad_dir / "2026-08-01.yaml").write_text("not: [valid, yaml, :::", encoding="utf-8")

    items = report_service.list_reports()
    assert [i["system_id"] for i in items] == ["checkout-agent"]


def test_get_report_series_sorted_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    dates = [r["date"] for r in report_service.get_report_series("checkout-agent")]
    assert dates == ["2026-08-26", "2026-05-10"]


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
    bad_dir = tmp_path / "broken-system"
    bad_dir.mkdir()
    (bad_dir / "2026-08-01.yaml").write_text("not: [valid, yaml, :::", encoding="utf-8")
    result = report_service.get_report("broken-system", "2026-08-01")
    assert result["success"] is False
    assert "error" in result
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_report_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'keel.services.report_service'`.

**Step 3: Write the implementation**

```python
# keel/services/report_service.py
"""Read-only access to reports/ — an archive of assess-genai-with-library runs, one
YAML file per assessment. Unlike keel/store.py's Store, nothing here is cached in
memory: reports are read fresh off disk on every call, since they're an immutable
archive rather than hot editable catalog data. A malformed file is skipped in list
views and reported as a clear error from get_report, never a 500.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.schemas.report import Report

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def _reports_dir() -> Path:
    from keel.config import settings

    return Path(settings.reports_dir) if settings.reports_dir else DEFAULT_REPORTS_DIR


def _load_report_file(path: Path) -> Report | None:
    """Parse one report YAML file. None on any failure (bad YAML, schema mismatch)."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        return Report(**data)
    except ValidationError:
        return None


def list_reports() -> list[dict[str, Any]]:
    """One entry per system folder: {system_id, system_name, latest_date, report_count,
    has_delta}. A system with zero parseable report files is omitted entirely."""
    root = _reports_dir()
    if not root.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for system_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        reports = []
        for path in sorted(system_dir.glob("*.yaml")):
            report = _load_report_file(path)
            if report is not None:
                reports.append(report)
        if not reports:
            continue
        reports.sort(key=lambda r: r.date, reverse=True)
        latest = reports[0]
        out.append({
            "system_id": system_dir.name,
            "system_name": latest.system_name,
            "latest_date": latest.date,
            "report_count": len(reports),
            "has_delta": any(r.delta_summary for r in reports),
        })
    return out


def get_report_series(system_id: str) -> list[dict[str, Any]]:
    """[{date, system_name}, ...] for one system, newest first. [] if the system
    folder is missing or has no parseable report files."""
    system_dir = _reports_dir() / system_id
    if not system_dir.is_dir():
        return []
    reports = []
    for path in sorted(system_dir.glob("*.yaml")):
        report = _load_report_file(path)
        if report is not None:
            reports.append(report)
    reports.sort(key=lambda r: r.date, reverse=True)
    return [{"date": r.date, "system_name": r.system_name} for r in reports]


def get_report(system_id: str, date: str) -> dict[str, Any]:
    """{"success": True, "report": {...}} or {"success": False, "error": "..."}."""
    path = _reports_dir() / system_id / f"{date}.yaml"
    if not path.is_file():
        return {"success": False, "error": f"No report for {system_id!r} on {date!r}"}
    report = _load_report_file(path)
    if report is None:
        return {"success": False, "error": f"Report {system_id}/{date}.yaml could not be parsed"}
    return {"success": True, "report": report.model_dump()}
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_report_service.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add keel/services/report_service.py tests/test_report_service.py
git commit -m "feat(reports): read-only report_service — list/series/get, off-disk"
```

---

### Task 4: Routes

**Files:**
- Modify: `keel/routes/library.py`
- Test: `tests/test_report_routes.py`

**Context:** Read-only, added to `library.py` alongside the other non-CRUD sections already there (Health/overview, Style guide, Git history, Config) rather than a new file — this file already mixes concerns by section comment, not by one-file-per-entity. Uses `monkeypatch` on `keel.config.settings.reports_dir` the same way Task 3's tests do, with a real `FastAPI TestClient` (see `tests/test_crud_routes.py` / `tests/test_history.py` for the house style).

**Step 1: Write the failing tests**

```python
# tests/test_report_routes.py
import yaml
from fastapi.testclient import TestClient

import keel.config
from keel.main import app

VALID_REPORT = {
    "system_id": "checkout-agent", "system_name": "Checkout Agent",
    "system_description": "Handles checkout for the storefront.",
    "date": "2026-08-26", "assessor": "Jane Doe <jane@example.com>",
    "findings": [], "discarded": [], "dialogue": [],
}


def _write_report(reports_dir, system_id, date):
    d = reports_dir / system_id
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(VALID_REPORT, system_id=system_id, date=date)
    (d / f"{date}.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_route_list_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    client = TestClient(app)
    r = client.get("/reports")
    assert r.status_code == 200
    body = r.json()
    assert body["reports"][0]["system_id"] == "checkout-agent"


def test_route_report_series(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-05-10")
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    client = TestClient(app)
    r = client.get("/reports/checkout-agent")
    assert r.status_code == 200
    dates = [x["date"] for x in r.json()["series"]]
    assert dates == ["2026-08-26", "2026-05-10"]


def test_route_report_series_unknown_system_returns_empty_not_404(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    client = TestClient(app)
    r = client.get("/reports/no-such-system")
    assert r.status_code == 200
    assert r.json()["series"] == []


def test_route_get_report_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    _write_report(tmp_path, "checkout-agent", "2026-08-26")
    client = TestClient(app)
    r = client.get("/reports/checkout-agent/2026-08-26")
    assert r.status_code == 200
    assert r.json()["system_name"] == "Checkout Agent"


def test_route_get_report_missing_is_404(tmp_path, monkeypatch):
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    client = TestClient(app)
    r = client.get("/reports/no-such-system/2026-08-26")
    assert r.status_code == 404
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_report_routes.py -v`
Expected: FAIL with 404s (routes don't exist yet).

**Step 3: Write the implementation**

In `keel/routes/library.py`: add the import near the top, alongside the other service imports —

```python
from keel.services import (
    health_service,
    mitigation_service,
    report_service,
    style_guide_service,
    threat_service,
)
```

Then add a new section, after the "Git history (read-only)" section and before "Config":

```python
# --------------------------------------------------------------------------- #
# Reports (read-only — written directly to disk by assess-genai-with-library)
# --------------------------------------------------------------------------- #
@router.get("/reports")
async def list_reports():
    """One entry per system with any parseable report."""
    return {"reports": report_service.list_reports()}


@router.get("/reports/{system_id}")
async def report_series(system_id: str):
    """A system's report dates, newest first. Empty list (not 404) for an unknown
    or empty system — there's nothing invalid about a system with no reports yet."""
    return {"series": report_service.get_report_series(system_id)}


@router.get("/reports/{system_id}/{date}")
async def get_report(system_id: str, date: str):
    result = report_service.get_report(system_id, date)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result["report"]
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_report_routes.py -v`
Expected: all PASS.

**Step 5: Run the full backend suite**

Run: `python -m pytest -q`
Expected: all PASS. This closes out the entire backend portion of this plan.

**Step 6: Commit**

```bash
git add keel/routes/library.py tests/test_report_routes.py
git commit -m "feat(reports): GET /reports, /reports/{system_id}, /reports/{system_id}/{date}"
```

---

### Task 5: Frontend — Reports screen scaffolding (nav + rail list)

**Files:**
- Modify: `keel/static/index.html`

**Context:** Read `keel/static/index.html`'s Overview screen implementation first (`loadOverview`, `overviewHtml`, `renderOverviewRail`, and how `switchScreen`/`renderRail`/`renderMain` dispatch on `state.screen`) — Reports needs that same "load once, render read-only, no draft/save" shape, not the Threats/Mitigations three-pane editor. No automated test for this task (pure UI wiring); verified together with Tasks 6–7 in Task 8's manual pass.

**Step 1: Add the nav button**

Find the screen nav buttons (`<button data-screen="overview">Overview</button>` etc., near the top of the body) and add a fifth:

```html
<button data-screen="reports">Reports</button>
```

**Step 2: Add `reports` to `switchScreen`'s screen-specific branches**

In `switchScreen(name)`, extend the `titles` map, the `noSearch`/facets/`newBtn` visibility checks (Reports has no search, no facets, no "+ New" button — same as Overview), and add a `reports` case to the final dispatch:

```javascript
const titles = { overview: "Keel · Overview", threats: "Keel · Threats", mitigations: "Keel · Mitigations", style: "Keel · Style guide", reports: "Keel · Reports" };
...
const noSearch = name === "overview" || name === "reports";
...
const hasFacets = name === "threats" || name === "mitigations" || name === "style";   // unchanged — reports gets none
...
newBtn.style.display = (name === "style" || name === "overview" || name === "reports") ? "none" : "";
...
renderRail(); renderMain(); renderRight();
if (name === "overview") loadOverview();
if (name === "reports") loadReports();
```

**Step 3: Add `reports` to `renderRail`/`renderMain`/`renderRight` dispatch**

```javascript
function renderRail() {
  if (state.screen === "overview") return renderOverviewRail();
  if (state.screen === "reports") return renderReportsRail();
  if (state.screen === "style") return renderStyleRail();
  if (state.screen === "mitigations") return renderMitRail();
  return renderList();
}
function renderMain() {
  if (state.screen === "overview") return renderOverviewMain();
  if (state.screen === "reports") return renderReportsMain();
  if (state.screen === "style") return renderStyleDetail();
  if (state.screen === "mitigations") return renderMitDetail();
  return renderDetail();
}
```

(Leave `renderRight` alone if Overview's branch already collapses the third column via `applyPreviewVisibility()` for screens with no preview — Reports should do the same; add a `reports` case mirroring whatever `overview` does there.)

**Step 4: Add report state fields**

Near `mitFacets`/`warnings`/`recentActivity` in the `state` object:

```javascript
reportsList: [],        // GET /reports — [{system_id, system_name, latest_date, report_count, has_delta}]
reportSeries: {},        // system_id -> GET /reports/{system_id}'s series, cached per system as opened
reportSelected: null,    // {system_id, date} of the open report
currentReport: null,     // GET /reports/{system_id}/{date} body
```

**Step 5: Load + rail + empty main**

```javascript
async function loadReports() {
  state.reportsList = (await j("/reports")).reports;
  if (state.screen === "reports") { renderReportsRail(); renderReportsMain(); }
}

function renderReportsRail() {
  const el = document.getElementById("list");
  el.innerHTML = state.reportsList.length ? state.reportsList.map(s => `
    <div class="row" data-system="${esc(s.system_id)}">
      <span class="rid">${esc(s.system_id)}</span>
      <span class="rtitle">${esc(s.system_name)} · ${s.report_count} report${s.report_count === 1 ? "" : "s"}${s.has_delta ? " · Δ" : ""}</span>
    </div>`).join("") : '<div class="empty" style="margin-top:40px">No reports yet.</div>';
  document.getElementById("count").textContent = state.reportsList.length + "";
  el.querySelectorAll(".row").forEach(row => row.onclick = () => openReportSystem(row.dataset.system));
}

function renderReportsMain() {
  const m = document.getElementById("main");
  m.innerHTML = state.currentReport
    ? reportDetailHtml(state.currentReport)
    : '<div class="empty">Select a system from the list.</div>';
  if (state.currentReport) wireReportDetail();
}
```

**Step 6: Commit**

```bash
git add keel/static/index.html
git commit -m "feat(reports-ui): Reports screen scaffolding — nav, rail list, dispatch"
```

---

### Task 6: Frontend — report detail (self-check rendering)

**Files:**
- Modify: `keel/static/index.html`

**Context:** `openReportSystem` opens a system's series and picks the latest date (or lets the user switch between dates if there's more than one — a small dropdown or list of date chips above the detail is enough, no need for a separate screen). `reportDetailHtml` renders the SELF-CHECK view natively: findings grouped by `risk.severity` (`critical`/`high` = "Important", `medium`/`low` = "Less important"), `discarded` shown collapsed/de-emphasized, `dialogue` as a short Q&A list — reuse `.card`/`.badge`/`readsec`-style patterns already in this file rather than inventing new CSS.

**Step 1: System open + date switching**

```javascript
async function openReportSystem(systemId, date) {
  if (!state.reportSeries[systemId]) {
    state.reportSeries[systemId] = (await j(`/reports/${encodeURIComponent(systemId)}`)).series;
  }
  const series = state.reportSeries[systemId];
  const pick = date || (series[0] && series[0].date);
  if (!pick) { state.currentReport = null; renderReportsMain(); return; }
  state.currentReport = await j(`/reports/${encodeURIComponent(systemId)}/${encodeURIComponent(pick)}`);
  state.reportSelected = { system_id: systemId, date: pick };
  renderReportsMain();
}
```

**Step 2: Detail rendering**

```javascript
const SEVERITY_IMPORTANT = new Set(["critical", "high"]);

function reportDetailHtml(rep) {
  const series = state.reportSeries[state.reportSelected.system_id] || [];
  const dateChips = series.map(s => `<span class="badge ${s.date === state.reportSelected.date ? "soft" : ""}" data-date="${esc(s.date)}" style="cursor:pointer">${esc(s.date)}</span>`).join(" ");

  const important = rep.findings.filter(f => SEVERITY_IMPORTANT.has(f.risk.severity));
  const lessImportant = rep.findings.filter(f => !SEVERITY_IMPORTANT.has(f.risk.severity));

  const findingCard = f => `<div class="card">
      <div class="chead"><span class="ctitle">${esc(f.id)}</span><span class="badge cov ${f.risk.severity === "critical" || f.risk.severity === "high" ? "c-lo" : "c-mid"}">${esc(f.risk.severity)}</span></div>
      <div class="cdesc">${esc(f.scenario)}</div>
      ${f.requirements.map(r => `<div class="cdesc">→ ${esc(r.mitigation_id || r.description)}${r.coverage_status !== "needs_implementation" ? ` <span class="badge soft">${esc(r.coverage_status)}</span>` : ""}</div>`).join("")}
    </div>`;

  const discardedHtml = rep.discarded.length
    ? `<details><summary>Discarded (${rep.discarded.length})</summary>${rep.discarded.map(d => `<div class="cdesc">${esc(d.id)} — ${esc(d.reason)}</div>`).join("")}</details>`
    : "";

  const dialogueHtml = rep.dialogue.length
    ? rep.dialogue.map(d => `<div class="card"><div class="cdesc"><b>Q:</b> ${esc(d.question)}</div><div class="cdesc"><b>A:</b> ${esc(d.answer)}</div><div class="rationale">${esc(d.impact)}</div></div>`).join("")
    : '<p class="placeholder">No recorded exchanges.</p>';

  return `<div class="detail">
    <div class="dhead">
      <div class="dtitle"><h2>${esc(rep.system_name)}</h2><div class="did">${esc(rep.date)} · ${esc(rep.assessor)}</div></div>
    </div>
    <div class="ov-chips">${dateChips}</div>
    ${rep.delta_summary ? `<section><h3 class="slabel">What changed</h3><p>${esc(rep.delta_summary)}</p></section>` : ""}
    <section><h3 class="slabel">Important</h3>${important.map(findingCard).join("") || '<p class="placeholder">None.</p>'}</section>
    <section><h3 class="slabel">Less important</h3>${lessImportant.map(findingCard).join("") || '<p class="placeholder">None.</p>'}</section>
    <section><h3 class="slabel">Discarded</h3>${discardedHtml}</section>
    <section><h3 class="slabel">Dialogue</h3>${dialogueHtml}</section>
    <section>
      <button class="btn ghost" id="copyRequirements">Copy requirements</button>
      <button class="btn ghost" id="copyRequirementsExplained">Copy requirements + explanations</button>
    </section>
  </div>`;
}

function wireReportDetail() {
  document.querySelectorAll(".ov-chips [data-date]").forEach(chip =>
    chip.onclick = () => openReportSystem(state.reportSelected.system_id, chip.dataset.date));
  // copy buttons wired in Task 7
}
```

**Step 3: Commit**

```bash
git add keel/static/index.html
git commit -m "feat(reports-ui): render report detail — findings by severity, discarded, dialogue"
```

---

### Task 7: Frontend — copy-to-clipboard views with copy-time inclusion

**Files:**
- Modify: `keel/static/index.html`

**Context:** Two markdown variants, built client-side from `state.currentReport` plus a live mitigation lookup (mirror the existing `mitById`/`setMitData` pattern — fetch `/mitigations?brief=false&include=name` filtered to the ids actually referenced, or reuse `state.mitById` if it's already populated app-wide; check how `state.mitById` gets populated on boot before deciding whether a fresh fetch is needed here). For `owner`, resolve from the mitigation's `implementations`: if there is exactly one implementation, use its `owner`; if more than one, prefer the first with `coverage === "shared"`, else the first entry; if none or `owner` is blank, omit the line. Inclusion checkboxes are copy-time UI state only — nothing is written back to the report.

**Step 1: Inclusion checkboxes on each requirement line**

Modify the `findingCard` requirement line from Task 6 to add a checkbox, defaulted per the design (`already_covered` unchecked, everything else checked; `discarded` never shown here at all since this only iterates `rep.findings`):

```javascript
${f.requirements.map((r, ri) => `<div class="cdesc">
  <label><input type="checkbox" class="req-include" data-fid="${esc(f.id)}" data-ri="${ri}" ${r.coverage_status === "already_covered" ? "" : "checked"}>
  ${esc(r.mitigation_id || r.description)}${r.coverage_status !== "needs_implementation" ? ` <span class="badge soft">${esc(r.coverage_status)}</span>` : ""}</label>
</div>`).join("")}
```

**Step 2: Mitigation lookup for the copy views**

```javascript
async function resolveMitigationsForReport(rep) {
  const ids = [...new Set(rep.findings.flatMap(f => f.requirements.map(r => r.mitigation_id).filter(Boolean)))];
  if (!ids.length) return {};
  const all = (await j("/mitigations?brief=false&include=name&include=implementations")).mitigations;
  const byId = Object.fromEntries(all.map(m => [m.id, m]));
  const out = {};
  for (const id of ids) {
    const m = byId[id];
    if (!m) continue;
    const impls = m.implementations || [];
    const owner = impls.length === 1 ? impls[0].owner
      : (impls.find(i => i.coverage === "shared") || impls[0] || {}).owner;
    out[id] = { name: m.name, owner: owner || null };
  }
  return out;
}
```

**Step 3: Build + copy the two markdown variants**

```javascript
function buildRequirementsMarkdown(rep, mitInfo, includeExplanations) {
  const lines = [`# Requirements — ${rep.system_name} (${rep.date})`, ""];
  for (const f of rep.findings) {
    f.requirements.forEach((r, ri) => {
      const cb = document.querySelector(`.req-include[data-fid="${CSS.escape(f.id)}"][data-ri="${ri}"]`);
      if (cb && !cb.checked) return;
      const info = r.mitigation_id ? mitInfo[r.mitigation_id] : null;
      const label = info ? info.name : r.description;
      const ownerNote = info && info.owner ? ` (owner: ${info.owner})` : "";
      lines.push(`- ${label}${ownerNote}`);
      if (includeExplanations) lines.push(`  ${f.scenario}`);
    });
  }
  return lines.join("\n");
}

function wireReportDetail() {
  document.querySelectorAll(".ov-chips [data-date]").forEach(chip =>
    chip.onclick = () => openReportSystem(state.reportSelected.system_id, chip.dataset.date));

  const copyBtn = (id, withExplanations) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.onclick = async () => {
      const mitInfo = await resolveMitigationsForReport(state.currentReport);
      const md = buildRequirementsMarkdown(state.currentReport, mitInfo, withExplanations);
      await navigator.clipboard.writeText(md);
      toast("Copied to clipboard");
    };
  };
  copyBtn("copyRequirements", false);
  copyBtn("copyRequirementsExplained", true);
}
```

(This replaces the placeholder `wireReportDetail` stub from Task 6 — same function name, fuller body.)

**Step 4: Commit**

```bash
git add keel/static/index.html
git commit -m "feat(reports-ui): copy-to-clipboard requirements views with copy-time inclusion"
```

---

### Task 8: Fixture data + manual verification

**Files:** none created in the repo (fixture lives in a temp directory pointed at via `REPORTS_DIR`, never committed — this is a demo aid, not real assessment data, and there's no skill yet to produce real reports).

**Step 1: Prepare a temp reports fixture**

```bash
mkdir -p /tmp/keel-reports-demo/checkout-agent
```

Write two files by hand — `/tmp/keel-reports-demo/checkout-agent/2026-05-10.yaml` (a minimal first assessment, no `delta_summary`) and `/tmp/keel-reports-demo/checkout-agent/2026-08-26.yaml` (a re-assessment, `delta_summary` present, at least one finding with `requirements[].mitigation_id` set to a REAL id from the shipped catalog, e.g. `CTRL-URL-ALLOWLIST`, one with `mitigation_id: null` + a `description`, one `already_covered` requirement with a `coverage_note`, one `discarded` entry, one `dialogue` entry). Use the `Report` schema from Task 1 as the source of truth for the shape — if in doubt, construct it in a Python shell via `Report(...).model_dump()` and dump that to YAML rather than hand-guessing field names.

**Step 2: Point the dev server at the fixture**

Add `REPORTS_DIR=/tmp/keel-reports-demo` to how `keel-web` is launched (either export it before `preview_start`, or add an `"env"` entry to the `.claude/launch.json` config added earlier this session — check whichever the Browser pane's `preview_start` tool actually supports before assuming).

**Step 3: Browser verification checklist**

- Reports tab appears in the nav; clicking it lists `checkout-agent` with `report_count: 2` and a `Δ` marker.
- Opening it shows the 2026-08-26 report by default; the two date chips let you switch to 2026-05-10 and back.
- Findings split correctly into Important/Less important by `risk.severity`; Discarded is collapsed; Dialogue shows the Q/A/impact.
- "Copy requirements" produces a markdown list with the ad hoc requirement's `description`, the catalog one's resolved `name` (not its raw id), and an owner note wherever `Implementation.owner` is set on that mitigation's card — verify by reading `navigator.clipboard` contents back via `javascript_tool` (`await navigator.clipboard.readText()`), the same way clipboard writes were verified earlier this session.
- "Copy requirements + explanations" produces the same list with each finding's `scenario` appended.
- Unchecking a requirement's inclusion checkbox and copying again shows it excluded; reloading the page resets the checkboxes to their defaults (proving nothing persisted).
- The `already_covered` requirement starts unchecked by default.

**Step 4: Clean up**

```bash
rm -rf /tmp/keel-reports-demo
```

Revert whatever env/launch-config change Step 2 made — the fixture and its wiring must not be committed.

**Step 5: Final full-suite run**

Run: `python -m pytest -q`
Expected: all PASS (backend tasks 1–4 already covered this; this just re-confirms nothing broke while doing the frontend tasks, which touch no Python).

---

## Follow-up (not in this plan)

Once this is merged, the actual assessment-writing side needs its own pass: two prose changes to `.claude/skills/assess-genai-with-library/SKILL.md` — a system-identification step (compare against `reports/*/` frontmatter, propose a match, load the prior report on confirmation and assess by delta) and a final report-writing step (assemble a `Report`-shaped YAML via git-identity for `assessor`, write it plus the full self-check `.md` rendering via the Write tool). Neither is unit-testable; verify by running a real or fixture assessment through the skill once written and inspecting the resulting file against `keel/schemas/report.py`.
