"""Extensions: a report keeps an extension's section whether or not it is installed, and
an installed one is found by its entry point and used.

Every extension here is made up ("example"), registered by replacing the entry point
lookup, and every report is written by the test.
"""
import importlib
import sys
from types import SimpleNamespace

import pytest
import yaml
from fastapi import APIRouter
from fastapi.testclient import TestClient

import keel.config
from keel import diagram, extensions
from keel.errors import Invalid
from keel.mcp import tools as _tools  # noqa: F401 - importing registers Keel's own tools
from keel.mcp.registry import dispatch_tool
from keel.services import report_service

SECTION = {"kept": "as it is", "nested": {"parts": [{"id": "p1", "label": "Gateway"}]}}

REPORT = {
    "system_id": "checkout-agent",
    "system_name": "Checkout Agent",
    "system_description": "Handles checkout for the storefront.",
    "date": "2026-08-26",
    "assessor": "Jane Doe <jane@example.com>",
    "findings": [],
    "discarded": [],
    "surfaces": [{"id": "S1", "kind": "entry", "name": "checkout API", "where": "/api/checkout",
                  "note": "no model on this path"}],
}


class EntryPoint:
    """Stands in for importlib.metadata.EntryPoint: a name and a load()."""

    def __init__(self, name, obj=None, error=None):
        self.name, self._obj, self._error = name, obj, error

    def load(self):
        if self._error:
            raise self._error
        return self._obj


@pytest.fixture
def install(monkeypatch):
    """`install(*entry_points)` makes them the installed extensions; none by default."""

    def put(*eps):
        monkeypatch.setattr(
            extensions, "entry_points",
            lambda group: list(eps) if group == extensions.GROUP else [],
        )
        extensions.installed.cache_clear()

    put()
    yield put
    extensions.installed.cache_clear()


@pytest.fixture
def reports(tmp_path, monkeypatch):
    """`write(**fields) -> path`: a made-up report on disk, under its system and date."""
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path))

    def write(**over):
        doc = {**REPORT, **over}
        path = tmp_path / doc["system_id"] / f"{doc['date']}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc), encoding="utf-8")
        return path

    return write


def _on_disk(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Without the extension installed
# --------------------------------------------------------------------------- #
def test_a_report_with_a_section_opens_checks_and_saves_without_the_extension(reports, install):
    path = reports(extensions={"example": SECTION})
    base = "/api/reports/checkout-agent/2026-08-26"
    from keel.main import app

    c = TestClient(app)
    got = c.get(base)
    assert got.status_code == 200
    body = got.json()
    assert body["extensions"] == {"example": SECTION}

    assert c.post(f"{base}/validate", json=body).json()["ok"] is True

    body["system_description"] = "Handles checkout and refunds."
    assert c.put(base, json=body).status_code == 200
    assert _on_disk(path)["extensions"] == {"example": SECTION}


async def test_a_report_with_a_section_round_trips_through_mcp_without_the_extension(reports, install):
    path = reports(extensions={"example": SECTION})
    mcp_body = await dispatch_tool("get_report", {"system_id": "checkout-agent", "date": "2026-08-26"})
    assert mcp_body["extensions"] == {"example": SECTION}
    saved = await dispatch_tool("save_report", {"system_id": "checkout-agent", "date": "2026-08-26",
                                                "report": mcp_body})
    assert saved["success"] is True
    updated = await dispatch_tool("update_report", {
        "system_id": "checkout-agent", "date": "2026-08-26",
        "changes": {"delta_summary": "Refunds were added."},
    })
    assert updated["success"] is True
    on_disk = _on_disk(path)
    assert on_disk["extensions"] == {"example": SECTION}
    assert on_disk["delta_summary"] == "Refunds were added."


async def test_update_report_changes_a_section_key_by_key(reports, install):
    """Sending one key of a section keeps its other keys and other extensions' sections."""
    path = reports(extensions={"example": SECTION, "other": {"x": 1}})
    updated = await dispatch_tool("update_report", {
        "system_id": "checkout-agent", "date": "2026-08-26",
        "changes": {"extensions": {"example": {"nested": {"parts": []}, "kept": None, "new": 2}}},
    })
    assert updated["success"] is True
    assert _on_disk(path)["extensions"] == {"example": {"nested": {"parts": []}, "new": 2},
                                            "other": {"x": 1}}


def test_a_report_without_a_section_is_saved_without_one(reports, install):
    """Turning extensions on must not rewrite every report in the archive."""
    path = reports()
    report_service.save_report("checkout-agent", "2026-08-26", dict(REPORT))
    assert "extensions" not in _on_disk(path)


def test_the_site_does_not_show_a_section(catalog_dir, tmp_path, install):
    from keel import site
    from keel.store import Store, set_store
    from tests.test_site import REPORT as SITE_REPORT

    set_store(Store(catalog_dir(
        threats=[{"id": "T-ONE", "mitigations": [
            {"id": "CTRL-ONE", "strength": "gating", "rationale": "blocks it"}]}, {"id": "T-TWO"}],
        mitigations=[{"id": "CTRL-ONE"}],
    )))
    try:
        root = tmp_path / "reports"
        (root / "checkout-agent").mkdir(parents=True)
        doc = {**SITE_REPORT, "extensions": {"example": {"marker": "only-the-extension-reads-this"}}}
        (root / "checkout-agent" / "2026-08-26.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
        out = tmp_path / "public"
        assert site.build_site(out, root)["reports"] == 1
        page = (out / "reports/checkout-agent/2026-08-26/index.html").read_text(encoding="utf-8")
        assert "only-the-extension-reads-this" not in page
    finally:
        set_store(None)


# --------------------------------------------------------------------------- #
# A fake extension, installed
# --------------------------------------------------------------------------- #
def test_an_extension_that_does_not_load_is_skipped(install, caplog):
    good = SimpleNamespace(name="example")
    install(EntryPoint("broken", error=ImportError("missing dependency")),
            EntryPoint("nameless", SimpleNamespace()), EntryPoint("example", good))
    assert extensions.installed() == (good,)
    assert "broken" in caplog.text


def test_its_diagram_is_used_and_its_note_shown(reports, install, monkeypatch, tmp_path):
    seen = []

    def draw_diagram(report, section, threats, shape):
        seen.append((report.system_id, section, shape))
        return (f"<figure>{shape}</figure>", "Drawn by the example extension.") if section else None

    install(EntryPoint("example", SimpleNamespace(name="example", draw_diagram=draw_diagram)))
    reports(extensions={"example": SECTION})
    reports(system_id="plain-agent")
    monkeypatch.setenv("KEEL_ARCHIFY", str(tmp_path / "none"))
    from keel.main import app

    c = TestClient(app)
    body = c.get("/api/reports/checkout-agent/2026-08-26/diagram?shape=narrow").json()
    assert body == {"html": "<figure>narrow</figure>", "reason": None,
                    "note": "Drawn by the example extension."}
    assert seen == [("checkout-agent", SECTION, "narrow")]

    # The extension returns None for a report with no section: Keel draws its own.
    body = c.get("/api/reports/plain-agent/2026-08-26/diagram").json()
    assert body["html"] is None and "Archify" in body["reason"] and body["note"] is None
    assert seen[-1] == ("plain-agent", {}, "wide")


def test_its_diagram_may_say_why_it_cannot_draw(reports, install):
    def draw_diagram(report, section, threats, shape):
        raise diagram.Unavailable("The example drawing needs its own tool.")

    install(EntryPoint("example", SimpleNamespace(name="example", draw_diagram=draw_diagram)))
    reports(extensions={"example": SECTION})
    from keel.main import app

    body = TestClient(app).get("/api/reports/checkout-agent/2026-08-26/diagram").json()
    assert body == {"html": None, "reason": "The example drawing needs its own tool.", "note": None}


def test_its_check_errors_are_reported_for_its_own_section(reports, install):
    checked = []

    def check(report, section):
        checked.append(section)
        return ["a part has no label"] if section.get("bad") else []

    install(EntryPoint("example", SimpleNamespace(name="example", check=check)))
    bad = {**REPORT, "extensions": {"example": {"bad": True}}}
    reports(**bad)

    result = report_service.check_report("checkout-agent", "2026-08-26", bad)
    assert result["ok"] is False
    assert {"field": "", "msg": "extensions.example: a part has no label"} in result["errors"]
    with pytest.raises(Invalid) as e:
        report_service.save_report("checkout-agent", "2026-08-26", bad)
    assert "extensions.example: a part has no label" in [d["message"] for d in e.value.details]

    # No section, nothing for it to check.
    checked.clear()
    assert report_service.check_report("checkout-agent", "2026-08-26", dict(REPORT))["ok"] is True
    assert checked == []

    # Not installed: the same section is stored and not checked.
    install()
    assert report_service.save_report("checkout-agent", "2026-08-26", bad)["success"] is True


def test_its_router_is_mounted_before_the_page_catch_all(install, monkeypatch):
    router = APIRouter()

    @router.get("/api/example/ping")
    def ping():
        return {"pong": True}

    @router.get("/example/page")
    def page():
        return {"page": True}

    install(EntryPoint("example", SimpleNamespace(name="example", routers=[router])))
    import keel.main

    try:
        c = TestClient(importlib.reload(keel.main).app)
        assert c.get("/api/example/ping").json() == {"pong": True}
        assert c.get("/example/page").json() == {"page": True}
        assert c.get("/health").json()["status"] == "ok"
    finally:
        monkeypatch.undo()
        extensions.installed.cache_clear()
        importlib.reload(keel.main)


def test_its_command_runs_and_keel_keeps_its_own_names(install, monkeypatch):
    seen = []

    def hello(args):
        seen.append(args)
        return 3

    def validate(args):
        raise AssertionError("Keel's own `validate` must win")

    install(EntryPoint("example", SimpleNamespace(
        name="example", commands={"hello": hello, "validate": validate})))
    from keel.mcp import server

    monkeypatch.setattr(sys, "argv", ["keel", "hello", "--loud", "x"])
    with pytest.raises(SystemExit) as e:
        server.main()
    assert e.value.code == 3
    assert seen == [["--loud", "x"]]
    assert set(extensions.commands()) == {"hello"}


async def test_it_adds_mcp_tools_after_keels_own(install):
    from keel.mcp import registry

    def register_mcp(mcp):
        @mcp.register_tool(annotations={"readOnlyHint": True})
        async def example_echo(text: str) -> dict:
            """Says the text back."""
            return {"echo": text}

    install(EntryPoint("example", SimpleNamespace(name="example", register_mcp=register_mcp)))
    import keel.mcp.server

    try:
        importlib.reload(keel.mcp.server)
        assert "save_report" in registry.TOOL_REGISTRY
        assert await dispatch_tool("example_echo", {"text": "hi"}) == {"echo": "hi"}
    finally:
        registry.TOOL_REGISTRY.pop("example_echo", None)
