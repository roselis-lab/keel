"""Repairing a file the loader refused.

The dashboard reports records that failed to load; anything reported as broken has to be
fixable where it is reported, and a record that would not parse has no form to render.
So the app serves the file's text and takes it back — through a deliberately narrow door.
"""
from fastapi.testclient import TestClient

from keel.main import app
from keel.store import Store, set_store

BAD = """id: T-BAD
title: Bad
harm: not-a-harm
weaknesses:
  - component: tool
    text: no scoping
reachability: nothing worth taking
"""
GOOD = BAD.replace("not-a-harm", "data-exposed")


def _client(catalog_dir):
    d = catalog_dir(threats=[{"id": "T-OK"}])
    (d / "threats" / "T-BAD.yaml").write_text(BAD, encoding="utf-8")
    set_store(Store(d))
    return TestClient(app), d


def test_read_returns_the_text_and_what_is_wrong_with_it(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        # Reading a broken file succeeds and reports what is wrong with it: the whole
        # point is to hand back something you can fix.
        body = client.get("/api/catalog/file", params={"path": "threats/T-BAD.yaml"}).json()
        assert body["text"] == BAD
        assert body["errors"][0]["field"] == "harm"
    finally:
        set_store(None)


def test_saving_a_fix_writes_it_and_the_record_loads(catalog_dir):
    client, d = _client(catalog_dir)
    try:
        r = client.put("/api/catalog/file", json={"path": "threats/T-BAD.yaml", "text": GOOD})
        assert r.status_code == 200
        assert r.json() == {"success": True, "path": "threats/T-BAD.yaml", "errors": [], "problems": []}
        assert (d / "threats" / "T-BAD.yaml").read_text(encoding="utf-8") == GOOD
        # The store reloaded, so the entry is now served.
        assert client.get("/api/threats/T-BAD").status_code == 200
    finally:
        set_store(None)


def test_a_save_that_would_not_load_is_refused_and_nothing_is_written(catalog_dir):
    """This door must not be able to create the state it exists to repair."""
    client, d = _client(catalog_dir)
    try:
        r = client.put(
            "/api/catalog/file",
            json={"path": "threats/T-BAD.yaml", "text": BAD.replace("not-a-harm", "still-wrong")},
        )
        assert r.status_code == 422
        assert r.json()["details"][0]["field"] == "harm"
        assert (d / "threats" / "T-BAD.yaml").read_text(encoding="utf-8") == BAD
    finally:
        set_store(None)


def test_unparseable_yaml_is_refused(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        r = client.put(
            "/api/catalog/file", json={"path": "threats/T-BAD.yaml", "text": "id: [unclosed\n"}
        )
        assert r.status_code == 422
        assert "not readable as YAML" in r.json()["details"][0]["message"]
    finally:
        set_store(None)


def test_id_must_still_match_the_filename(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        r = client.put(
            "/api/catalog/file",
            json={"path": "threats/T-BAD.yaml", "text": GOOD.replace("id: T-BAD", "id: T-OTHER")},
        )
        assert r.status_code == 422
        assert r.json()["details"][0]["field"] == "id"
    finally:
        set_store(None)


def test_the_door_is_narrow(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        for path in (
            "../secrets.yaml",
            "threats/../../secrets.yaml",
            "etc/passwd.yaml",
            "threats/notes.txt",
            "threats/T-BAD.yaml/x",
            "T-BAD.yaml",
        ):
            r = client.get("/api/catalog/file", params={"path": path})
            assert r.status_code == 400, (path, r.status_code)
    finally:
        set_store(None)


def test_missing_file_is_404(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        r = client.get("/api/catalog/file", params={"path": "threats/T-NOPE.yaml"})
        assert r.status_code == 404
    finally:
        set_store(None)


def test_bad_body_is_422(catalog_dir):
    client, _ = _client(catalog_dir)
    try:
        assert client.put("/api/catalog/file", json={"path": "threats/T-BAD.yaml"}).status_code == 422
    finally:
        set_store(None)
