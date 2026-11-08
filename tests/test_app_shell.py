"""The UI is served at real paths, and the API keeps its own namespace.

Views used to live behind a `#` because the API owned `/threats` and `/mitigations` at
the root. The API moved under `/api`, which freed those paths for the app — but a
catch-all that answers everything will also answer `/api/typo` with 200 and a page of
HTML, so the exclusion is the part worth testing.
"""
from fastapi.testclient import TestClient

from keel.main import app

client = TestClient(app)


def test_root_serves_the_app():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<title>Keel" in r.text
    assert 'id="root"' in r.text
    # A deploy must not leave a browser holding an index that names old assets.
    assert r.headers["cache-control"] == "no-cache"


def test_the_built_assets_the_index_names_are_served():
    """The app is committed as a build. An index that names a file the build did not
    write is a blank page, so every script and stylesheet it names has to load."""
    import re

    html = client.get("/").text
    names = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    assert names, "the index names no assets"
    for name in names:
        assert client.get(name).status_code == 200, name


def test_a_missing_asset_is_404_not_the_app():
    r = client.get("/assets/nothing-here.js")
    assert r.status_code == 404
    assert "text/html" not in r.headers.get("content-type", "")


def test_the_old_editor_is_still_served_at_bare_edit():
    r = client.get("/edit")
    assert r.status_code == 200
    assert "data-field=" in r.text
    assert 'id="root"' not in r.text


def test_old_editor_links_to_threats_and_controls_land_in_the_app_editor():
    """Threats and controls are edited in the app. A bookmark or an old link into the
    single-file editor for either must not open the old screen."""
    cases = {
        "/edit/threats": "/threats",
        "/edit/threats/T-CMD-INJECT": "/threats/T-CMD-INJECT/edit",
        "/edit/mitigations": "/controls",
        "/edit/mitigations/CTRL-ANY": "/controls/CTRL-ANY/edit",
        "/edit/controls/CTRL-ANY": "/controls/CTRL-ANY/edit",
        "/edit/threats/..%2F..%2Fetc": "/threats",
        "/edit/reports": "/reports",
        "/edit/reports/halo/2026-09-08": "/reports/halo/2026-09-08/edit",
        "/edit/reports/halo/not-a-date": "/reports",
        "/edit/style": "/style-guide",
        "/edit/style-guide": "/style-guide",
        "/edit/style/threat/title": "/style-guide/threat/title",
        "/edit/style/threat/": "/style-guide/threat",
    }
    for path, to in cases.items():
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 308, path
        assert r.headers["location"] == to, path


def test_no_link_in_the_app_leads_to_the_old_editor():
    """The owner pressed a library button in the new app and landed on the old screen.
    Reports and the style guide are edited in the app now, so no path in its source may
    start with `/edit` (the app's own editors end in `/edit` instead)."""
    import re
    from pathlib import Path

    src = Path(__file__).parents[1] / "web/src"
    hits = []
    for f in src.rglob("*.ts*"):
        for m in re.finditer(r'["`\'](/edit\b[^"`\']*)', f.read_text(encoding="utf-8")):
            hits.append((f.name, m.group(1)))
    assert not hits, hits


def test_the_app_has_editor_routes():
    for path in ("/threats/new", "/threats/T-CMD-INJECT/edit", "/controls/new", "/controls/CTRL-ANY/edit",
                 "/reports/new", "/reports/sys/2026-01-01/edit", "/style-guide", "/style-guide/threat",
                 "/style-guide/threat/title"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert 'id="root"' in r.text, path


def test_a_view_path_serves_the_app_so_a_deep_link_opens_cold():
    for path in ("/overview", "/threats", "/threats/T-ANYTHING", "/reports/sys/2026-01-01"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "text/html" in r.headers["content-type"], path


def test_unknown_api_path_is_404_not_the_app():
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert "text/html" not in r.headers.get("content-type", "")


def test_api_root_is_404():
    assert client.get("/api").status_code == 404


def test_api_still_answers_json():
    r = client.get("/api/threats")
    assert r.status_code == 200
    assert r.json()["count"] == len(r.json()["threats"])


def test_app_liveness_stays_at_the_root():
    assert client.get("/health").json()["status"] == "ok"


# --------------------------------------------------------------------------- #
# The editor has to keep up with the schema
# --------------------------------------------------------------------------- #
def test_every_schema_field_has_a_control_in_the_app_editor():
    """`note` became required on a Reference and the old editor never grew a field for it,
    so a threat carrying references could not be saved at all. The schema is the list.
    Every field in the app editor is bound by a `path` naming it ("title",
    `${p}.surface`, "telemetry.evidence"), so the source can be checked against the
    schema instead of trusted."""
    import re
    from pathlib import Path

    from keel.schemas import mitigation as m
    from keel.schemas import threat as t

    src = (Path(__file__).parents[1] / "web/src/pages/Editor.tsx").read_text(encoding="utf-8")
    paths = set(re.findall(r'path=(?:"([^"]+)"|\{`([^`]+)`\})', src))
    names = {seg for pair in paths for p in pair if p for seg in re.split(r"[.]", p)}
    # Chosen with a picker rather than typed, so there is no field to bind.
    picked = {("MitigationLink", "id")}
    models = (t.Threat, t.Weakness, t.Reference, t.MitigationLink, m.MitigationCreate,
              m.LocusDecision, m.FailureDecision, m.Telemetry, m.TelemetryEvent,
              m.ValidationCheck, m.FaqItem, m.Implementation)
    for model in models:
        for name in model.model_fields:
            if (model.__name__, name) in picked:
                continue
            bound = name in names or f'set("{name}"' in src
            assert bound, f"{model.__name__}.{name} has no control in the app editor"


def test_the_report_editor_binds_every_field_the_old_editor_did():
    """Report editing moved out of the single-file editor. What it let an assessor change
    is the floor: losing a field in the move would send them back to editing YAML."""
    import re
    from pathlib import Path

    src = (Path(__file__).parents[1] / "web/src/pages/ReportEditor.tsx").read_text(encoding="utf-8")
    bound = set(re.findall(r'path=(?:"([^"]+)"|\{`\$\{\w+\}\.([^`]+)`\})', src))
    bound = {a or b for a, b in bound}
    bound |= set(re.findall(r'set\(`\$\{\w+\}\.([a-z_.]+)`', src))
    old_editor = {
        "system_name", "system_id", "system_description", "delta_summary",
        "scenario", "asset", "vulnerability", "delta", "harm", "attack_surface",
        "exploitation_complexity", "risk.severity", "risk.likelihood", "risk.reasoning",
        "source.who", "source.motive", "source.access",
        "included", "invariant", "enforce_at", "done_check",
    }
    assert not old_editor - bound, sorted(old_editor - bound)


# --------------------------------------------------------------------------- #
# Validators the app's editors call as you type
# --------------------------------------------------------------------------- #
def test_control_validate_names_the_field_and_saves_nothing():
    import copy

    from keel.store import get_store

    ok, card = next(iter(get_store().mitigations.items()))
    card = copy.deepcopy(card)
    assert client.post("/api/mitigations/validate", json=card).json()["errors"] == []
    # An emptied input reaches the server as null, the way the editor sends it.
    r = client.post("/api/mitigations/validate", json={**card, "name": None})
    assert r.status_code == 200
    body = r.json()
    assert not body["ok"]
    assert any(e["field"] == "name" for e in body["errors"]), body
    assert client.get(f"/api/mitigations/{ok}").json()["name"] == card["name"]


def test_report_validate_names_the_field_and_saves_nothing():
    doc = {"system_id": "probe", "date": "2026-01-01", "system_name": "Probe",
           "system_description": "Answers questions.", "assessor": "test"}
    url = "/api/reports/probe/2026-01-01/validate"
    assert client.post(url, json=doc).json() == {"ok": True, "errors": [], "advice": []}
    body = client.post(url, json={**doc, "findings": [{"risk": {"severity": "huge"}}]}).json()
    assert not body["ok"]
    assert any(e["field"] == "findings.0.risk.severity" for e in body["errors"]), body
    # The address names the report; a body naming another one is refused, not saved.
    moved = client.post("/api/reports/other/2026-01-01/validate", json=doc).json()
    assert not moved["ok"] and moved["errors"][0]["field"] == ""
    assert client.get("/api/reports/probe/2026-01-01").status_code == 404
