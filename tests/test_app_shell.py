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
def test_every_sub_entity_field_has_an_editor_control():
    """`note` became required on a Reference and the editor never grew a field for it, so
    entering edit dropped the notes and the save was refused: a threat carrying references
    could not be edited in the app at all. The schema is the list; the markup tags each
    control with `data-field`, so the two can be compared instead of trusted."""
    from keel.schemas.threat import Reference, Weakness

    html = client.get("/").text
    for model in (Weakness, Reference):
        for name in model.model_fields:
            assert f'data-field="{name}"' in html, f"{model.__name__}.{name} has no editor"
