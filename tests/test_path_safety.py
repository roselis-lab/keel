"""An id is also a file name, so it is an untrusted path segment.

`catalog_dir / f"{entity_id}.yaml"` happily accepts `../../elsewhere`, and every id
arrives from outside - an MCP argument, a URL segment, a line of YAML. This was open:
three files escaped the catalog before the guard existed.

Two layers, on purpose. The schema rejects a bad id with a sentence an author can act
on. The store refuses to leave its own directory no matter what it is handed, so a bug
in the first layer cannot become an arbitrary write. A check the caller has to remember
is a check the next code path forgets.
"""
import pytest

from keel.mcp import tools as _tools  # noqa: F401
from keel.mcp.registry import dispatch_tool
from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import Threat
from keel.store import Store, set_store

# Everything an adversarial sweep of every path-taking entry point turned up, plus the
# names that got through the first fix: they never escaped the catalog, but Windows
# resolves them as devices and a git checkout containing one fails outright.
ESCAPES = [
    # Traversal, in the forms that usually work.
    "../../pwned", "T/../../pwned", "../outside", "./../pwned", "....//....//pwned",
    "/etc/passwd", "C:/pwned", r"\\server\share", r"..\..\pwned",
    "..", ".", ".hidden", "", " ", "with space",
    # These never escaped the catalog. They are refused because Windows resolves them as
    # devices whatever the extension, and a `git clone` of a repo containing one fails on
    # that platform - the catalog is a repository people clone.
    "T-A.", "T-A ", "CON", "NUL", "COM1", "LPT9", "nul.yaml",
    "T-A:stream",           # NTFS alternate data stream
    "T-A" + chr(0) + ".yaml",  # null byte
    "．．/pwned",    # fullwidth dots, which some normalisers fold to ASCII
    "T" * 300,              # longer than NAME_MAX once ".yaml" is appended
]


@pytest.fixture
def store(catalog_dir):
    s = Store(catalog_dir(threats=[{"id": "T-A"}], mitigations=[{"id": "CTRL-A"}]))
    set_store(s)
    yield s
    set_store(None)


# --------------------------------------------------------------------------- #
# The store cannot leave its directory, whatever it is asked
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("stem", ESCAPES)
@pytest.mark.parametrize("subdir", ["threats", "mitigations", "style_guide", "coverage"])
def test_the_store_refuses_any_name_that_is_a_path(store, subdir, stem):
    with pytest.raises(ValueError):
        store._path(subdir, stem)


def test_a_normal_id_resolves_inside_its_directory(store):
    path = store._path("threats", "T-DATA-LEAK")
    assert path.parent == (store.dir / "threats").resolve()
    assert path.name == "T-DATA-LEAK.yaml"


def test_the_guard_covers_deletes_too(store, tmp_path):
    """A delete is the same primitive pointed the other way."""
    with pytest.raises(ValueError):
        store.delete_threat_file("../../anything")


def test_nothing_is_written_outside_the_catalog(store, tmp_path):
    """The end-to-end claim, checked by looking at the filesystem rather than the code."""
    outside = list(tmp_path.rglob("*.yaml"))
    store.threats["../../escapee"] = {"id": "../../escapee", "title": "x"}
    with pytest.raises(ValueError):
        store.write_threat("../../escapee")
    assert list(tmp_path.rglob("*.yaml")) == outside


# --------------------------------------------------------------------------- #
# The schema says so first, in words
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", ["../../pwned", "T/../x", "/abs", ".dot", "a b"])
def test_the_schema_rejects_an_id_that_could_be_a_path(bad):
    for model, extra in (
        (Threat, {"title": "t", "harm": "downtime", "reachability": "r",
                  "weaknesses": [{"component": "tool", "text": "w"}]}),
        (MitigationCreate, {"name": "n", "mitigation_class": "process"}),
    ):
        with pytest.raises(Exception):
            model(id=bad, **extra)


@pytest.mark.asyncio
async def test_a_traversal_id_is_refused_at_the_tool_with_a_readable_message(store):
    result = await dispatch_tool("create_threat", {"threat_id": "../../pwned", "fields": {
        "title": "x", "harm": "downtime",
        "weaknesses": [{"component": "tool", "text": "x"}], "reachability": "y"}})
    assert result["code"] == "invalid"
    assert result["field"] == "id"
    assert "T-A" not in str(result)          # nothing leaked about what is there


@pytest.mark.asyncio
async def test_coverage_cannot_be_pointed_at_a_file_elsewhere(store, tmp_path):
    """It used to be closed only by luck: the file outside happened not to parse as a
    coverage document."""
    (tmp_path.parent / "elsewhere.yaml").write_text("source: {}\n", encoding="utf-8")
    result = await dispatch_tool("set_coverage_entry", {
        "source_id": "../../elsewhere", "ref": "X", "state": "gap"})
    assert result["success"] is False
    assert result["code"] in ("forbidden", "not_found")


# --------------------------------------------------------------------------- #
# The pattern is the readable layer; the boundary is structural
# --------------------------------------------------------------------------- #
def test_the_guard_holds_with_the_pattern_disabled(store, monkeypatch):
    """The point of the design, stated as a test. A pattern is one edit away from being
    wrong and cannot see a symlink or a name the platform rewrites on the way to disk,
    so it must not be what actually holds."""
    import keel.store as st

    monkeypatch.setattr(st, "is_safe_stem", lambda stem: None)
    for bad in ("../../pwned", "T/../../pwned", "/etc/passwd", r"..\..\pwned"):
        with pytest.raises((ValueError, OSError)):
            store._path("threats", bad)


def test_the_report_guard_holds_with_its_patterns_disabled(tmp_path, monkeypatch):
    """Reports were the last place where a regex was the whole boundary."""
    import keel.config
    from keel.services import report_service as rs

    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))
    always = type("Always", (), {"match": lambda self, _: True})()
    monkeypatch.setattr(rs, "SYSTEM_ID_RE", always)
    monkeypatch.setattr(rs, "DATE_RE", always)

    for system_id, date in (("../../etc", "passwd"),
                            ("sys", "../../../secrets"),
                            ("sys/../..", "2026-01-01")):
        assert rs._report_path(system_id, date) is None, (system_id, date)
    assert rs._report_path("sys", "2026-01-01") is not None


@pytest.mark.skipif(
    not hasattr(__import__("os"), "symlink"), reason="platform has no symlinks")
def test_a_symlink_out_of_the_catalog_is_refused(store, tmp_path):
    """A pattern cannot see this at all: the name is ordinary and the escape is in the
    filesystem. `resolve()` follows the link, so the parent comparison catches it.

    Skipped where the process cannot create symlinks (unprivileged Windows), which is
    why it is written to skip rather than to pass quietly."""
    import os

    secret = tmp_path.parent / "SECRET.yaml"
    secret.write_text("secret: true\n", encoding="utf-8")
    link = store.dir / "threats" / "T-LINK.yaml"
    try:
        os.symlink(secret, link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"cannot create a symlink here: {exc}")

    with pytest.raises(ValueError):
        store._path("threats", "T-LINK")
    assert secret.read_text(encoding="utf-8") == "secret: true\n"
