"""Read-only Git history endpoints.

These run against the REAL repo (the catalog YAML files have real commit history
here) and write nothing. They SKIP cleanly where `git` is missing or the working
tree is not a git repo, so the suite still runs in a throwaway `CATALOG_DIR` copy.
"""
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from keel import githistory
from keel.main import app
from keel.store import get_store, set_store


def _git_repo_available() -> bool:
    if shutil.which("git") is None:
        return False
    set_store(None)
    try:
        proc = subprocess.run(
            ["git", "-C", str(get_store().dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            timeout=10,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


pytestmark = pytest.mark.skipif(
    not _git_repo_available(),
    reason="git unavailable or catalog is not inside a git repo",
)


def test_history_of_tracked_threat():
    set_store(None)
    result = githistory.history("threats", "T-CMD-INJECT")
    assert result["available"] is True
    assert result["file"].endswith("T-CMD-INJECT.yaml")
    assert len(result["commits"]) >= 1  # shallow clones may show only 1
    for c in result["commits"]:
        assert c["sha"]
        assert c["author"]
        assert c["date"]
        assert c["message"]


def test_history_of_missing_id_is_unavailable():
    set_store(None)
    result = githistory.history("threats", "T-DOES-NOT-EXIST")
    assert result["available"] is False
    assert result["commits"] == []


def test_history_rejects_bad_entity_and_traversal():
    set_store(None)
    assert githistory.history("etc", "passwd")["available"] is False
    assert githistory.history("threats", "../../secrets")["available"] is False


def test_diff_of_a_real_commit():
    set_store(None)
    hist = githistory.history("threats", "T-CMD-INJECT")
    sha = hist["commits"][0]["sha"]
    d = githistory.diff("threats", "T-CMD-INJECT", sha)
    assert d is not None
    assert d["sha"]
    assert isinstance(d["diff"], str)
    # The scoped diff should mention the file path or carry unified-diff markers.
    assert "T-CMD-INJECT.yaml" in d["diff"] or "@@" in d["diff"] or "diff --git" in d["diff"]


def test_diff_rejects_bad_sha():
    set_store(None)
    assert githistory.diff("threats", "T-CMD-INJECT", "zzzz") is None
    assert githistory.diff("threats", "T-CMD-INJECT", "; rm -rf /") is None
    assert githistory.diff("etc", "passwd", "abcd") is None


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
def test_route_history_ok():
    set_store(None)
    client = TestClient(app)
    r = client.get("/history/threats/T-CMD-INJECT")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert len(body["commits"]) >= 1


def test_route_history_missing_is_available_false():
    set_store(None)
    client = TestClient(app)
    r = client.get("/history/threats/T-DOES-NOT-EXIST")
    assert r.status_code == 200
    assert r.json() == {"available": False, "commits": []}


def test_route_history_bad_entity_and_traversal_404():
    set_store(None)
    client = TestClient(app)
    assert client.get("/history/etc/passwd").status_code == 404
    # A traversal id never matches the id pattern → 404.
    assert client.get("/history/threats/..%2F..%2Fsecrets").status_code == 404


def test_route_diff_ok_and_bad_sha_404():
    set_store(None)
    client = TestClient(app)
    hist = client.get("/history/threats/T-CMD-INJECT").json()
    sha = hist["commits"][0]["sha"]
    ok = client.get(f"/history/threats/T-CMD-INJECT/{sha}")
    assert ok.status_code == 200
    assert isinstance(ok.json()["diff"], str)

    assert client.get("/history/threats/T-CMD-INJECT/zzzz").status_code == 404
