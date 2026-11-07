"""A finished report as a Confluence page and Jira tickets, pushed from the assessor's machine.

One ticket per thing to build, not per finding, found again by its label so a second
publish updates instead of filing twice. The page is generated and says so. Report text
arrives as text: a report can quote a hostile prompt, and neither Confluence nor Jira
may read it as markup. Nothing is sent without a target, a token, or with --dry-run.
"""
import json
import re
import xml.dom.minidom
from urllib.parse import parse_qs, urlparse

import pytest
import yaml

from keel.atlassian import cli, picture, render
from keel.atlassian.client import Api, AtlassianError, Confluence, Jira
from keel.atlassian.picture import chain_png
from keel.schemas.report import Report
from keel.store import Store, set_store
from keel.vocabulary import load_vocabularies

HOSTILE = "<script>alert(1)</script> [click|https://evil.example] {html}<b>x</b>{html} !x.png!"

ASK = {
    "mitigation_id": None, "coverage_status": "needs_implementation",
    "description": "Cap refunds the bot can issue without a person.",
    "invariant": "No refund above 50 EUR leaves without a person's approval.",
    "enforce_at": "the refund service, before the gateway call",
    "done_check": "a test asks for a 60 EUR refund and expects a pending approval",
}


def finding(fid, **over):
    f = {
        "id": fid, "from_catalog": True,
        "scenario": "A customer asks for a refund and the model sets the amount itself [1].",
        "source": {"who": "external-attacker", "motive": "money", "access": "the public chat"},
        "asset": "refund budget", "attack_surface": "user-input",
        "vulnerability": "the refund tool takes the amount from the model",
        "exploitation_complexity": "low", "harm": "wrong-decision",
        "risk": {"likelihood": "high", "severity": "high", "reasoning": "Anyone can open the chat."},
        "delta": "new", "evidence": [1], "requirements": [ASK],
    }
    f.update(over)
    return f


def report(**over):
    r = {
        "system_id": "demo", "system_name": "Refund bot", "system_description": "A chat.",
        "date": "2026-11-07", "assessor": "Tester <t@example.com>", "status": "final",
        "findings": [finding("T-A")],
        "discarded": [{"id": "T-B", "by": "review", "reason": "The shell tool is not registered [1]."}],
        "open_questions": [{
            "id": "Q1", "question": "Who edits the help centre?", "asks_for": "access",
            "looked_in": "the repo", "needed_for": "poisoning", "how_to_check": "export permissions",
        }],
        "surfaces": [{"id": "S1", "kind": "entry", "name": "chat", "where": "/chat", "outcome": ["T-A"]}],
        "evidence": [{"id": 1, "kind": "read", "commit": "a" * 40, "path": "tools/refund.py",
                      "lines": "40-52", "quote": "return gateway.refund(order_id, amount)"}],
    }
    r.update(over)
    return r


@pytest.fixture
def store(catalog_dir):
    d = catalog_dir(
        threats=[{"id": "T-A"}, {"id": "T-B"}, {"id": "T-C"}],
        mitigations=[
            {"id": "CTRL-X", "name": "Approval before money moves",
             "validation": [{"criterion": "A refund above the cap waits for a person"}]},
        ],
    )
    s = Store(d)
    set_store(s)
    yield s
    set_store(None)


def write(tmp_path, data) -> object:
    p = tmp_path / "reports" / "demo" / "2026-11-07.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return p


def well_formed(storage: str) -> None:
    xml.dom.minidom.parseString(
        ('<r xmlns:ac="urn:ac" xmlns:ri="urn:ri">' + storage + "</r>").encode()
    )


# --------------------------------------------------------------------------- #
# What to build
# --------------------------------------------------------------------------- #
def test_findings_closed_by_one_control_share_one_ticket(store):
    ctrl = {"mitigation_id": "CTRL-X", "coverage_status": "needs_implementation"}
    r = Report(**report(findings=[
        finding("T-A", requirements=[ctrl]),
        finding("T-C", root_cause="other", requirements=[ctrl]),
    ]))
    ts = render.tickets(r, store.mitigations)
    assert len(ts) == 1
    assert [f.id for f in ts[0].findings] == ["T-A", "T-C"]


def test_covered_and_left_out_requirements_make_no_ticket(store):
    r = Report(**report(findings=[finding("T-A", requirements=[
        {"mitigation_id": "CTRL-X", "coverage_status": "already_covered", "coverage_note": "in place"},
        {**ASK, "included": False},
    ])]))
    assert render.tickets(r, store.mitigations) == []


def test_a_ticket_label_is_stable_across_reassessments(store):
    a = render.tickets(Report(**report()), store.mitigations)[0].label
    b = render.tickets(Report(**report(date="2026-12-01")), store.mitigations)[0].label
    assert a == b and re.fullmatch(r"keel-[0-9a-f]{12}", a)


def test_a_catalog_control_takes_its_acceptance_from_the_card(store):
    req = render.Requirement(mitigation_id="CTRL-X", coverage_status="needs_implementation")
    fix = render.fix_of(req, store.mitigations)
    assert fix.summary == "Approval before money moves"
    assert fix.must_hold.startswith("Stops the action")
    assert fix.where.startswith("infrastructure")
    assert fix.done_when == ["A refund above the cap waits for a person"]


def test_the_requirement_wins_over_the_card_when_it_says_more(store):
    req = render.Requirement(**{**{k: v for k, v in ASK.items() if k != "description"},
                                "mitigation_id": "CTRL-X"})
    fix = render.fix_of(req, store.mitigations)
    assert fix.must_hold == ASK["invariant"]
    assert fix.done_when == [ASK["done_check"]]


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #
def page(store, **over):
    r = Report(**report(**over))
    return render.storage(r, render.tickets(r, store.mitigations), store.mitigations, {}, "reports/demo/2026-11-07.yaml")


def test_the_page_is_well_formed_and_says_it_is_generated(store):
    s = page(store)
    well_formed(s)
    assert "Generated by Keel from <code>reports/demo/2026-11-07.yaml</code>" in s
    assert "overwritten on the next publish" in s


def test_the_page_keeps_everything_and_folds_the_reasoning(store):
    s = page(store)
    for text in ("What to build", "The risks", "Ruled out", "refuted in review",
                 "Still open", "export permissions", "How we know, for reviewers",
                 "Every surface walked (1)", "return gateway.refund(order_id, amount)"):
        assert text in s
    assert 'ri:filename="keel-chain-T-A.png"' in s
    assert "[1]" not in s.split("Evidence")[0]  # markers are for the evidence list only


def test_hostile_report_text_is_text_on_the_page(store):
    s = page(store, findings=[finding("T-A", scenario=HOSTILE, vulnerability=HOSTILE)])
    well_formed(s)
    assert "<script>" not in s and "<b>x</b>" not in s
    assert "&lt;script&gt;" in s


def test_harm_and_likelihood_stay_apart_and_today_is_shown(store):
    s = page(store, findings=[finding(
        "T-A", deployment="not_deployed",
        risk_today={"likelihood": "low", "severity": "high", "reasoning": "Not published yet."},
    )])
    assert "high harm · unlikely today" in s
    assert "high harm · likely at launch" in s


def test_a_draft_says_so(store):
    assert "<strong>Draft.</strong>" in page(store, status="draft")


def test_a_legacy_threat_is_marked_not_dropped(store):
    s = page(store, findings=[finding("T-A", origin="legacy")])
    assert "legacy: existed before the AI" in s and "T-A" in s


def test_a_non_https_evidence_link_is_not_a_link(store):
    s = page(store, evidence=[{"id": 1, "kind": "test", "command": "pytest",
                               "url": "javascript:alert(1)", "quote": "q"}])
    assert 'href="javascript' not in s


# --------------------------------------------------------------------------- #
# The ticket
# --------------------------------------------------------------------------- #
def test_hostile_text_cannot_become_wiki_markup(store):
    r = Report(**report(findings=[finding("T-A", scenario=HOSTILE)]))
    t = render.tickets(r, store.mitigations)[0]
    text = render.ticket_wiki(r, t, None, with_pictures=False)
    body = text.split("h3. Why\n", 1)[1].split("\n", 1)[0]
    for raw in ("[click|", "{html}", "!x.png!"):
        assert raw not in body
    assert r"\[click\|https://evil.example\]" in body


def test_the_ticket_links_the_page_only_over_https(store):
    r = Report(**report())
    t = render.tickets(r, store.mitigations)[0]
    assert "|https://wiki.example/p/1]" in render.ticket_wiki(r, t, "https://wiki.example/p/1", True)
    assert "javascript" not in render.ticket_wiki(r, t, "javascript:alert(1)", True)


def test_the_ticket_says_why_what_where_and_done(store):
    r = Report(**report())
    text = render.ticket_wiki(r, render.tickets(r, store.mitigations)[0], None, True)
    for part in ("h3. Why", "!keel-chain-T-A.png|width=760!", "h3. What must hold",
                 "*Where:*", "h3. Done when", "never changes this ticket's status"):
        assert part in text


def test_the_picture_is_a_png(store):
    r = Report(**report())
    data = chain_png(r, r.findings[0], load_vocabularies(store.dir), "No refund above 50 EUR")
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 2000


def _draws(font, char: str) -> bytes:
    return bytes(font.getmask(char))


def test_the_picture_font_draws_cyrillic():
    # A Russian report must not come out as empty boxes in Confluence and Jira.
    if picture.font_file() is None:
        pytest.skip("no system font with Cyrillic on this machine; set KEEL_PICTURE_FONT")
    font = picture._font(12)
    missing = _draws(font, "￿")
    for char in "ЖщЮя—":
        assert _draws(font, char) != missing, f"{char!r} is drawn as the missing-glyph box"


def test_a_pinned_font_wins(monkeypatch, tmp_path):
    pinned = tmp_path / "house.ttf"
    pinned.write_bytes(b"")
    monkeypatch.setenv("KEEL_PICTURE_FONT", str(pinned))
    picture.font_file.cache_clear()
    try:
        assert picture.font_file() == str(pinned)
    finally:
        monkeypatch.delenv("KEEL_PICTURE_FONT")
        picture.font_file.cache_clear()


# --------------------------------------------------------------------------- #
# Publishing
# --------------------------------------------------------------------------- #
class FakeAtlassian:
    """Just enough of Confluence and Jira to watch what a publish sends."""

    def __init__(self, cloud=True):
        self.calls: list[tuple[str, str]] = []
        self.pages: dict[str, dict] = {}
        self.issues: dict[str, dict] = {}
        self.cloud = cloud
        self.auth: set[str] = set()

    def __call__(self, method, url, headers, body):
        u = urlparse(url)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        path = u.path
        self.calls.append((method, path))
        self.auth.add(headers["Authorization"].split()[0])
        if "attachment" in path or "attachments" in path:
            assert headers.get("X-Atlassian-Token") in ("nocheck", "no-check") or method in ("GET", "DELETE")
        if path == "/wiki/rest/api/content" and method == "GET":
            hits = [p for p in self.pages.values() if p["title"] == q["title"]]
            return 200, json.dumps({"results": hits}).encode()
        if path == "/wiki/rest/api/content" and method == "POST":
            data = json.loads(body)
            pid = str(100 + len(self.pages))
            self.pages[pid] = {"id": pid, "title": data["title"], "version": {"number": 1},
                               "body": data["body"]["storage"]["value"],
                               "_links": {"webui": f"/spaces/SEC/pages/{pid}"}}
            return 200, json.dumps(self.pages[pid]).encode()
        m = re.fullmatch(r"/wiki/rest/api/content/(\d+)", path)
        if m and method == "PUT":
            data = json.loads(body)
            p = self.pages[m.group(1)]
            assert data["version"]["number"] == p["version"]["number"] + 1
            p.update(version=data["version"], body=data["body"]["storage"]["value"])
            return 200, json.dumps(p).encode()
        if re.fullmatch(r"/wiki/rest/api/content/\d+/child/attachment", path) and method == "GET":
            return 200, b'{"results": []}'
        if "/child/attachment" in path and method == "POST":
            return 200, b'{"results": [{"id": "att1"}]}'
        if path in ("/rest/api/2/search/jql", "/rest/api/2/search") and method == "GET":
            if path.endswith("/jql") and not self.cloud:
                return 404, b"not found"
            label = re.search(r'labels = "([^"]+)"', q["jql"]).group(1)
            hits = [{"key": k} for k, i in self.issues.items() if label in i["labels"]]
            return 200, json.dumps({"issues": hits}).encode()
        if path == "/rest/api/2/issue" and method == "POST":
            fields = json.loads(body)["fields"]
            key = f"SEC-{1 + len(self.issues)}"
            self.issues[key] = {**fields, "attachment": []}
            return 201, json.dumps({"key": key}).encode()
        m = re.fullmatch(r"/rest/api/2/issue/(SEC-\d+)", path)
        if m and method == "PUT":
            self.issues[m.group(1)].update(json.loads(body)["fields"])
            return 204, b""
        if m and method == "GET":
            return 200, json.dumps({"fields": {"attachment": self.issues[m.group(1)]["attachment"]}}).encode()
        m = re.fullmatch(r"/rest/api/2/issue/(SEC-\d+)/attachments", path)
        if m and method == "POST":
            name = re.search(rb'filename="([^"]+)"', body).group(1).decode()
            self.issues[m.group(1)]["attachment"].append({"id": name, "filename": name})
            return 200, b"[]"
        if path.startswith("/rest/api/2/attachment/") and method == "DELETE":
            for i in self.issues.values():
                i["attachment"] = [a for a in i["attachment"] if a["id"] != path.rsplit("/", 1)[1]]
            return 204, b""
        raise AssertionError(f"unexpected {method} {path}")


def run(path, fake, **over):
    kw = dict(space="SEC", parent=None, project="SEC", issue_type="Task", security_level=None,
              dry_run=False, allow_draft=False, say=lambda m: None)
    kw.update(over)
    return cli.publish(
        path, confluence=Confluence(Api("https://acme.atlassian.net/wiki", "t", "a@b.c", fake)),
        jira=Jira(Api("https://acme.atlassian.net", "t", "a@b.c", fake)), **kw,
    )


def test_first_publish_files_the_ticket_and_links_it_from_the_page(store, tmp_path):
    fake = FakeAtlassian()
    path = write(tmp_path, report())
    side = run(path, fake, security_level="Security team")
    (issue,) = fake.issues.values()
    assert issue["labels"][0] == "keel" and issue["security"] == {"name": "Security team"}
    assert "!keel-chain-T-A.png|width=760!" in issue["description"]
    assert "acme.atlassian.net/wiki/spaces/SEC/pages/100" in issue["description"]
    (pg,) = fake.pages.values()
    assert "https://acme.atlassian.net/browse/SEC-1" in pg["body"]
    saved = json.loads(cli.sidecar_path(path).read_text(encoding="utf-8"))
    assert saved == side and saved["confluence"]["page_id"] == "100"


def test_a_second_publish_updates_in_place(store, tmp_path):
    fake = FakeAtlassian()
    path = write(tmp_path, report())
    run(path, fake)
    fake.calls.clear()
    run(path, fake)
    assert ("POST", "/rest/api/2/issue") not in fake.calls
    assert ("POST", "/wiki/rest/api/content") not in fake.calls
    assert len(fake.issues) == 1 and len(fake.pages) == 1
    assert [a["filename"] for a in fake.issues["SEC-1"]["attachment"]] == ["keel-chain-T-A.png"]


def test_data_center_search_falls_back_and_uses_a_bearer_token(store, tmp_path):
    fake = FakeAtlassian(cloud=False)
    path = write(tmp_path, report())
    cli.publish(
        path, space=None, parent=None, project="SEC", issue_type="Task", security_level=None,
        dry_run=False, allow_draft=False, say=lambda m: None,
        jira=Jira(Api("https://jira.corp.example", "pat", None, fake)),
    )
    assert ("GET", "/rest/api/2/search") in fake.calls
    assert fake.auth == {"Bearer"}


def test_a_dry_run_sends_nothing(store, tmp_path):
    fake = FakeAtlassian()
    said = []
    run(write(tmp_path, report()), fake, dry_run=True, say=said.append)
    assert fake.calls == []
    assert any("visible to everyone who can see project SEC" in s for s in said)


def test_a_draft_is_not_published_unless_asked(store, tmp_path):
    with pytest.raises(SystemExit, match="draft"):
        run(write(tmp_path, report(status="draft")), FakeAtlassian())


def test_no_target_and_no_token_send_nothing(store, tmp_path, monkeypatch):
    path = write(tmp_path, report())
    with pytest.raises(SystemExit, match="at least one target"):
        cli.publish(path, space=None, parent=None, project=None, issue_type="Task",
                    security_level=None, dry_run=False, allow_draft=False)
    for var in ("KEEL_JIRA_URL", "KEEL_JIRA_TOKEN", "KEEL_ATLASSIAN_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SystemExit, match="never taken from the command line"):
        cli.publish(path, space=None, parent=None, project="SEC", issue_type="Task",
                    security_level=None, dry_run=False, allow_draft=False)


def test_plain_http_is_refused_before_the_token_travels():
    with pytest.raises(AtlassianError, match="only https"):
        Api("http://jira.corp.example", "t")


def test_export_writes_files_and_sends_nothing(store, tmp_path):
    out = tmp_path / "out"
    r = cli.export(write(tmp_path, report()), out, allow_draft=False)
    assert r == {"tickets": 1, "pictures": 1}
    well_formed((out / "confluence-page.xhtml").read_text(encoding="utf-8"))
    (ticket,) = (out / "jira").iterdir()
    assert ticket.read_text(encoding="utf-8").startswith("Summary: Cap refunds")
    assert (out / "keel-chain-T-A.png").read_bytes()[:4] == b"\x89PNG"


def test_the_report_page_gets_the_same_picture(store, tmp_path, monkeypatch):
    import keel.config
    from fastapi.testclient import TestClient

    from keel.main import app

    write(tmp_path, report())
    monkeypatch.setattr(keel.config.settings, "reports_dir", str(tmp_path / "reports"))
    c = TestClient(app)
    r = c.get("/api/reports/demo/2026-11-07/chain/T-A.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content[:4] == b"\x89PNG"
    assert c.get("/api/reports/demo/2026-11-07/chain/T-NOPE.png").status_code == 404


def test_publishing_is_not_an_mcp_tool():
    from keel.mcp.registry import get_tool_list

    names = {t["name"] for t in get_tool_list()}
    assert not any("publish" in n or "jira" in n or "confluence" in n for n in names)
