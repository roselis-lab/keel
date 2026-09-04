"""Read-only Git history endpoints.

Everything here runs against the throwaway repo built by the `git_catalog` fixture,
so the tests assert on the history behaviour rather than on this repository's own
commit log. They skip cleanly where `git` is missing.
"""
import pytest
from fastapi.testclient import TestClient

from keel import githistory
from keel.main import app

from .conftest import GIT_MISSING

pytestmark = pytest.mark.skipif(GIT_MISSING, reason="git is not installed")


def test_history_of_tracked_threat(git_catalog):
    result = githistory.history("threats", "T-FIXTURE")
    assert result["available"] is True
    assert result["file"].endswith("T-FIXTURE.yaml")
    assert len(result["commits"]) == 2
    assert result["commits"][0]["message"] == "fix(catalog): a clearer title"
    for c in result["commits"]:
        assert c["sha"]
        assert c["author"] == "Test Author"
        assert c["date"]
        assert c["message"]


def test_history_of_missing_id_is_unavailable(git_catalog):
    result = githistory.history("threats", "T-DOES-NOT-EXIST")
    assert result["available"] is False
    assert result["commits"] == []


def test_history_rejects_bad_entity_and_traversal(git_catalog):
    assert githistory.history("etc", "passwd")["available"] is False
    assert githistory.history("threats", "../../secrets")["available"] is False


def test_history_unavailable_outside_a_git_repo(catalog_dir):
    """A throwaway CATALOG_DIR is the normal case for a fork that is not yet a repo.
    It must report unavailable, not raise."""
    from keel.store import Store, set_store

    set_store(Store(catalog_dir(threats=[{"id": "T-ONE"}])))
    try:
        assert githistory.history("threats", "T-ONE") == {"available": False, "commits": []}
        assert githistory.recent_activity()["available"] is False
    finally:
        set_store(None)


def test_diff_of_a_real_commit(git_catalog):
    hist = githistory.history("threats", "T-FIXTURE")
    sha = hist["commits"][0]["sha"]
    d = githistory.diff("threats", "T-FIXTURE", sha)
    assert d is not None
    assert d["sha"]
    assert isinstance(d["diff"], str)
    # The scoped diff should mention the file path or carry unified-diff markers.
    assert "T-FIXTURE.yaml" in d["diff"] or "@@" in d["diff"] or "diff --git" in d["diff"]
    # Scoped to this entry: the mitigation committed alongside it must not appear.
    assert "CTRL-FIXTURE.yaml" not in d["diff"]


def test_diff_rejects_bad_sha(git_catalog):
    assert githistory.diff("threats", "T-FIXTURE", "zzzz") is None
    assert githistory.diff("threats", "T-FIXTURE", "; rm -rf /") is None
    assert githistory.diff("etc", "passwd", "abcd") is None


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
def test_route_history_ok(git_catalog):
    r = TestClient(app).get("/api/history/threats/T-FIXTURE")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert len(body["commits"]) == 2


def test_route_history_missing_is_available_false(git_catalog):
    r = TestClient(app).get("/api/history/threats/T-DOES-NOT-EXIST")
    assert r.status_code == 200
    assert r.json() == {"available": False, "commits": []}


def test_route_history_bad_entity_and_traversal_404(git_catalog):
    client = TestClient(app)
    assert client.get("/api/history/etc/passwd").status_code == 404
    # A traversal id never matches the id pattern → 404.
    assert client.get("/api/history/threats/..%2F..%2Fsecrets").status_code == 404


def test_route_diff_ok_and_bad_sha_404(git_catalog):
    client = TestClient(app)
    sha = client.get("/api/history/threats/T-FIXTURE").json()["commits"][0]["sha"]
    ok = client.get(f"/api/history/threats/T-FIXTURE/{sha}")
    assert ok.status_code == 200
    assert isinstance(ok.json()["diff"], str)

    assert client.get("/api/history/threats/T-FIXTURE/zzzz").status_code == 404


# --------------------------------------------------------------------------- #
# Recent activity (whole-catalog feed)
# --------------------------------------------------------------------------- #
def test_recent_activity_lists_commits_with_entities(git_catalog):
    result = githistory.recent_activity(limit=5)
    assert result["available"] is True
    assert len(result["commits"]) == 2
    for c in result["commits"]:
        assert c["sha"] and c["author"] and c["date"] and c["message"]
        assert c["entities"], c  # every returned commit touched at least one tracked entity
        for e in c["entities"]:
            assert e["entity_type"] in ("threats", "mitigations")
            assert e["entity_id"]

    # The first commit added both files; the second touched only the threat.
    newest, oldest = result["commits"]
    assert [e["entity_id"] for e in newest["entities"]] == ["T-FIXTURE"]
    assert sorted(e["entity_id"] for e in oldest["entities"]) == ["CTRL-FIXTURE", "T-FIXTURE"]


def test_recent_activity_respects_limit(git_catalog):
    assert len(githistory.recent_activity(limit=1)["commits"]) == 1


def test_route_recent_activity_ok(git_catalog):
    r = TestClient(app).get("/api/history/recent?limit=3")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert len(body["commits"]) == 2
