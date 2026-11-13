"""`keel site`: the catalog and the finished reports as plain, read-only HTML files.

What a team does with Keel day to day is read: a security lead reads the reports, a risk
owner is shown one, a reviewer reads a catalog change in a pull request. None of that
needs a server that can write. So this builds a folder of static pages that a Git host
publishes (GitHub Pages, GitLab Pages), and access to it is whatever the Git host already
enforces. Changes still go through pull requests; the local `keel up` UI stays the
authoring tool.

Three rules hold the pages safe to publish:

* Every page is built from records that passed the same schema as the server, and every
  value is escaped. A report can quote hostile text (a prompt, a payload) and it must
  render as text.
* No script, no external fetch. The Content-Security-Policy on every page says so, and a
  click on a reference sends no referrer, so an internal page address does not leak.
* Reports are left out unless asked for, and drafts are left out unless asked for again.
  A Pages site can be public by accident; a finding should not be.
"""
from __future__ import annotations

import argparse
import datetime
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.schemas.report import Report
from keel.services import coverage_service
from keel.services.report_service import DATE_RE, SYSTEM_ID_RE
from keel.store import MITIGATION_ORDER, get_store
from keel.vocabulary import load_vocabularies

# A file inside the output folder that says "this folder was built by keel site". The
# build empties the folder first, so stale pages for deleted records do not linger, and
# it will only empty a folder that carries this mark.
MARKER = ".keel-site"

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)

LEVELS = {"low": 1, "medium": 2, "high": 3}

# A requirement's coverage_status, in the words of the person reading the hand-off.
IN_PLACE = {
    "already_covered": "Yes",
    "partial": "Partly",
    "needs_implementation": "No, to be built",
}

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1f21;--muted:#5d6166;--line:#dcdcd8;--card:#fff;
--accent:#1f5f8b;--high:#a3261b;--medium:#8a5a00;--low:#2f6b3a;--draft:#fff4d6}
@media (prefers-color-scheme:dark){:root{--bg:#16181a;--fg:#e6e6e3;--muted:#a0a4a8;
--line:#33373b;--card:#1d2023;--accent:#7cb7e0;--high:#ff8a7a;--medium:#e6b450;
--low:#8fd19e;--draft:#3a3220}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header.top{border-bottom:1px solid var(--line);background:var(--card)}
header.top nav{max-width:1080px;margin:0 auto;padding:12px 16px;display:flex;gap:20px;
flex-wrap:wrap;align-items:baseline}
header.top a{color:var(--fg);text-decoration:none}
header.top a.brand{font-weight:700}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;line-height:1.25;margin:0 0 8px}
h2{font-size:1.2rem;margin:32px 0 8px}
h3{font-size:1.05rem;margin:20px 0 6px}
a{color:var(--accent)}
p{margin:0 0 10px}
.muted{color:var(--muted)}
.lead{font-size:1.05rem}
code{font:0.9em ui-monospace,SFMono-Regular,Consolas,monospace}
table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:0.95rem}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--muted)}
td.num,th.num{text-align:right;white-space:nowrap}
.scroll{overflow-x:auto}
.box{background:var(--card);border:1px solid var(--line);border-radius:6px;
padding:12px 16px;margin:12px 0}
.box.key{border-left:4px solid var(--accent)}
.banner{background:var(--draft);border:1px solid var(--line);border-radius:6px;
padding:10px 14px;margin:0 0 16px}
.tag{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:0 6px;
font-size:0.85rem;margin:0 4px 4px 0;white-space:nowrap}
.high{color:var(--high);font-weight:600}.medium{color:var(--medium);font-weight:600}
.low{color:var(--low);font-weight:600}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:6px;
padding:10px 14px;min-width:140px}
.stat b{display:block;font-size:1.4rem}
dl{margin:0 0 10px}dt{font-weight:600;margin-top:8px}dd{margin:0 0 4px 0}
ul{margin:0 0 10px;padding-left:22px}
details{margin:12px 0}summary{cursor:pointer;font-weight:600}
footer{max-width:1080px;margin:0 auto;padding:16px;color:var(--muted);font-size:0.85rem}
"""


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


_CODE = re.compile(r"`([^`\n]+)`")


def prose(text: Any) -> str:
    """Catalog and report prose as paragraphs. Escaped first; backticks become code."""
    if text is None:
        return ""
    paras = [p.strip() for p in re.split(r"\n\s*\n", str(text)) if p.strip()]
    out = []
    for p in paras:
        body = _CODE.sub(r"<code>\1</code>", esc(p)).replace("\n", "<br>")
        out.append(f"<p>{body}</p>")
    return "".join(out)


def label(key: str) -> str:
    return key.replace("_", " ").capitalize()


def level(value: str | None) -> str:
    return f'<span class="{esc(value)}">{esc(value)}</span>' if value in LEVELS else esc(value)


def generic(value: Any) -> str:
    """Any nested value from a record: dicts as definition lists, lists as bullets.
    This is what keeps a page complete when a schema grows a field this file does not
    know about yet."""
    if value is None or value == [] or value == {}:
        return '<p class="muted">Not written.</p>'
    if isinstance(value, bool):
        return f"<p>{'yes' if value else 'no'}</p>"
    if isinstance(value, dict):
        rows = "".join(
            f"<dt>{esc(label(k))}</dt><dd>{generic(v)}</dd>"
            for k, v in value.items() if v not in (None, [], {})
        )
        return f"<dl>{rows}</dl>"
    if isinstance(value, list):
        if all(not isinstance(v, (dict, list)) for v in value):
            return "<ul>" + "".join(f"<li>{esc(v)}</li>" for v in value) + "</ul>"
        return "".join(f'<div class="box">{generic(v)}</div>' for v in value)
    return prose(value)


# --------------------------------------------------------------------------- #
# Page frame
# --------------------------------------------------------------------------- #
class Site:
    def __init__(self, out: Path, title: str, built: str):
        self.out = out
        self.title = title
        self.built = built
        self.pages: list[str] = []

    def link(self, depth: int, target: str) -> str:
        """A relative link, so the site works under any path prefix and from disk."""
        return "../" * depth + target

    def write(self, rel: str, heading: str, body: str) -> None:
        depth = rel.count("/")
        up = lambda t: self.link(depth, t)  # noqa: E731
        nav = (
            f'<a class="brand" href="{up("index.html")}">{esc(self.title)}</a>'
            f'<a href="{up("threats/index.html")}">Threats</a>'
            f'<a href="{up("mitigations/index.html")}">Controls</a>'
            f'<a href="{up("coverage/index.html")}">Coverage</a>'
            f'<a href="{up("reports/index.html")}">Reports</a>'
        )
        page = (
            "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
            '<meta name="referrer" content="no-referrer">'
            '<meta name="robots" content="noindex,nofollow">'
            f"<title>{esc(heading)} - {esc(self.title)}</title><style>{CSS}</style></head>"
            f'<body><header class="top"><nav>{nav}</nav></header><main>{body}</main>'
            f"<footer>Read-only copy built by <code>keel site</code> {esc(self.built)}. "
            "Changes to the catalog go through a pull request.</footer></body></html>\n"
        )
        path = self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page, encoding="utf-8")
        self.pages.append(rel)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_reports(reports_dir: Path | None, include_drafts: bool) -> list[Report]:
    """Every report that parses against the schema, newest first per system. A file
    that does not parse is skipped, the same rule the server follows."""
    if reports_dir is None or not reports_dir.is_dir():
        return []
    out: list[Report] = []
    for system_dir in sorted(p for p in reports_dir.iterdir() if p.is_dir()):
        if not SYSTEM_ID_RE.match(system_dir.name):
            continue
        for path in sorted(system_dir.glob("*.yaml")):
            if not DATE_RE.match(path.stem):
                continue
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                report = Report(**data) if isinstance(data, dict) else None
            except (OSError, yaml.YAMLError, ValidationError, TypeError):
                report = None
            if report is None:
                print(f"skipped {path}: not a valid report", file=sys.stderr)
                continue
            # The folder and file name are the address; the content has to agree, or a
            # link would point at a page built from a different record.
            if report.system_id != system_dir.name or report.date != path.stem:
                print(f"skipped {path}: system_id or date disagrees with the path",
                      file=sys.stderr)
                continue
            if report.status != "final" and not include_drafts:
                continue
            out.append(report)
    out.sort(key=lambda r: (r.system_id, r.date), reverse=True)
    return out


def _commit(catalog_dir: Path) -> str:
    for var in ("GITHUB_SHA", "CI_COMMIT_SHA"):
        if os.environ.get(var):
            return os.environ[var][:12]
    try:
        res = subprocess.run(
            ["git", "-C", str(catalog_dir), "rev-parse", "--short=12", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
class Builder:
    def __init__(self, site: Site, reports: list[Report]):
        store = get_store()
        self.site = site
        self.threats: dict[str, dict] = dict(sorted(store.threats.items()))
        self.mitigations: dict[str, dict] = dict(sorted(store.mitigations.items()))
        self.vocab = load_vocabularies(store.dir)
        self.coverage = coverage_service.matrix(store.dir)["sources"]
        self.named_by = coverage_service.by_entity(store.dir)
        self.reports = reports
        self.used_by: dict[str, list[tuple[str, str]]] = {}
        for tid, t in self.threats.items():
            for link in t.get("mitigations") or []:
                self.used_by.setdefault(link["id"], []).append((tid, link.get("strength", "")))

    # links ------------------------------------------------------------------ #
    def ref(self, depth: int, entity_id: str | None) -> str:
        """A link to a threat or control page when the id exists, plain text otherwise."""
        if not entity_id:
            return ""
        if entity_id in self.threats:
            return f'<a href="{self.site.link(depth, f"threats/{entity_id}/index.html")}">' \
                   f"{esc(entity_id)}</a>"
        if entity_id in self.mitigations:
            return f'<a href="{self.site.link(depth, f"mitigations/{entity_id}/index.html")}">' \
                   f"{esc(entity_id)}</a>"
        return f"<code>{esc(entity_id)}</code>"

    def vocab_name(self, kind: str, value: str) -> str:
        entry = self.vocab.get(kind, {}).get(value)
        name = entry.get("name") if isinstance(entry, dict) else None
        return esc(name or value)

    def named_by_html(self, entity_id: str) -> str:
        cites = self.named_by.get(entity_id) or []
        if not cites:
            return '<p class="muted">No tracked source names this entry. It is Keel\'s own.</p>'
        items = "".join(
            f'<li>{esc(c["source_title"])} {esc(c["version"])}: <b>{esc(c["ref"])}</b> '
            f'{esc(c["title"])}</li>' for c in cites
        )
        return f"<ul>{items}</ul>"

    # overview --------------------------------------------------------------- #
    def overview(self) -> None:
        links = sum(len(t.get("mitigations") or []) for t in self.threats.values())
        counts = {"covered": 0, "out_of_scope": 0, "gap": 0}
        for src in self.coverage:
            for k, v in src["counts"].items():
                counts[k] += v
        rows = sum(counts.values())
        latest: dict[str, Report] = {}
        for r in self.reports:
            latest.setdefault(r.system_id, r)
        stats = "".join(
            f'<div class="stat"><b>{n}</b>{esc(what)}</div>' for n, what in (
                (len(self.threats), "threats"),
                (len(self.mitigations), "controls"),
                (links, "threat-to-control links"),
                (rows, "coverage rows"),
                (len(latest), "assessed systems"),
            )
        )
        if latest:
            body_rows = "".join(
                f"<tr><td><a href=\"reports/{esc(r.system_id)}/{esc(r.date)}/index.html\">"
                f"{esc(r.system_name)}</a></td><td>{esc(r.date)}</td><td>{esc(r.status)}</td>"
                f'<td class="num">{len(r.findings)}</td>'
                f'<td class="num">{sum(1 for f in r.findings if f.risk.severity == "high")}</td></tr>'
                for r in latest.values()
            )
            reports_html = (
                '<div class="scroll"><table><tr><th>System</th><th>Latest assessment</th>'
                '<th>Status</th><th class="num">Findings</th><th class="num">High severity</th>'
                f"</tr>{body_rows}</table></div>"
            )
        else:
            reports_html = (
                '<p class="muted">No reports in this build. Reports are published only when '
                "the build is given a reports folder.</p>"
            )
        body = (
            f"<h1>{esc(self.site.title)}</h1>"
            '<p class="lead">The GenAI threat catalog this team assesses against, and the '
            "assessments made with it. This copy is read-only.</p>"
            f'<div class="stats">{stats}</div>'
            f"<h2>Latest assessment per system</h2>{reports_html}"
            "<h2>Where the catalog stands against public lists</h2>"
            f"<p>{counts['covered']} of {rows} entries from the tracked lists are covered, "
            f"{counts['out_of_scope']} are out of scope with the reason written down, and "
            f"{counts['gap']} are open gaps. "
            '<a href="coverage/index.html">The full table</a>.</p>'
        )
        self.site.write("index.html", "Overview", body)

    # threats ---------------------------------------------------------------- #
    def threat_list(self) -> None:
        rows = ""
        for tid, t in self.threats.items():
            links = t.get("mitigations") or []
            gating = sum(1 for m in links if m.get("strength") == "gating")
            rows += (
                f'<tr><td><a href="{esc(tid)}/index.html">{esc(tid)}</a></td>'
                f"<td>{esc(t.get('title'))}</td><td>{self.vocab_name('harm', t.get('harm'))}</td>"
                f'<td class="num">{len(t.get("weaknesses") or [])}</td>'
                f'<td class="num">{gating}</td><td class="num">{len(links) - gating}</td></tr>'
            )
        body = (
            "<h1>Threats</h1><p>One threat is one harm. Each one says when it does not "
            "apply to a system, so an assessment can rule it out with a reason.</p>"
            '<div class="scroll"><table><tr><th>Id</th><th>Threat</th><th>Harm</th>'
            '<th class="num">Weaknesses</th><th class="num">Blocking controls</th>'
            f'<th class="num">Softening controls</th></tr>{rows}</table></div>'
        )
        self.site.write("threats/index.html", "Threats", body)

    def threat_page(self, tid: str, t: dict) -> None:
        d = 2
        sources = "".join(
            f'<span class="tag">{self.vocab_name("source", s)}</span>' for s in t.get("source") or []
        )
        weak_rows = "".join(
            f"<tr><td>{self.vocab_name('components', w.get('component'))}</td>"
            f"<td>{', '.join(self.vocab_name('surface', s) for s in w.get('surface') or []) or '<span class=muted>none: the component acts on its own authority</span>'}</td>"
            f"<td>{esc(w.get('nature'))}</td><td>{prose(w.get('text'))}</td></tr>"
            for w in t.get("weaknesses") or []
        )
        mit_rows = "".join(
            f"<tr><td>{self.ref(d, m['id'])}<br><span class=\"muted\">"
            f"{esc((self.mitigations.get(m['id']) or {}).get('name'))}</span></td>"
            f"<td>{esc(m.get('strength'))}</td><td>{prose(m.get('rationale'))}"
            f"{('<p><b>Exception:</b> ' + esc(m['exception']) + '</p>') if m.get('exception') else ''}"
            "</td></tr>"
            for m in t.get("mitigations") or []
        )
        refs = "".join(
            f'<li><a href="{esc(r.get("url"))}" rel="noopener noreferrer">{esc(r.get("title"))}</a>'
            f"{prose(r.get('note'))}</li>"
            for r in t.get("references") or []
        )
        body = (
            f'<p class="muted"><code>{esc(tid)}</code></p><h1>{esc(t.get("title"))}</h1>'
            f"<p>Harm: <b>{self.vocab_name('harm', t.get('harm'))}</b></p>"
            f"<p>Driven by: {sources}</p>"
            '<div class="box key"><h3>When it does not apply</h3>'
            f"{prose(t.get('reachability'))}</div>"
            "<h2>Weaknesses: the paths to this harm</h2>"
            '<div class="scroll"><table><tr><th>Component</th><th>Reached over</th>'
            f"<th>Nature</th><th>Condition</th></tr>{weak_rows}</table></div>"
            "<h2>Controls</h2><p class=\"muted\">A blocking (gating) control stops the threat. "
            "A softening (soft) control only lowers the odds.</p>"
            '<div class="scroll"><table><tr><th>Control</th><th>Strength</th><th>Why it fits'
            f"</th></tr>{mit_rows}</table></div>"
            f"<h2>References</h2>{('<ul>' + refs + '</ul>') if refs else '<p class=muted>None.</p>'}"
            + (f"<h2>Against the tracked lists</h2>{prose(t.get('positioning'))}"
               if t.get("positioning") else "")
            + f"<h2>Named by</h2>{self.named_by_html(tid)}"
            f'<p class="muted">Source file: <code>catalog/threats/{esc(tid)}.yaml</code></p>'
        )
        self.site.write(f"threats/{tid}/index.html", tid, body)

    # mitigations ------------------------------------------------------------ #
    def mitigation_list(self) -> None:
        rows = "".join(
            f'<tr><td><a href="{esc(mid)}/index.html">{esc(mid)}</a></td>'
            f"<td>{esc(m.get('name'))}</td><td>{esc(m.get('mitigation_class'))}</td>"
            f'<td class="num">{len(self.used_by.get(mid, []))}</td>'
            f'<td class="num">{len(m.get("implementations") or [])}</td></tr>'
            for mid, m in self.mitigations.items()
        )
        body = (
            "<h1>Controls</h1><p>A control card says what the control does and how to check "
            "it. An implementation records how this organisation built it. A card with no "
            "implementation is a recommendation, not cover.</p>"
            '<div class="scroll"><table><tr><th>Id</th><th>Control</th><th>Class</th>'
            '<th class="num">Threats</th><th class="num">Implementations</th></tr>'
            f"{rows}</table></div>"
        )
        self.site.write("mitigations/index.html", "Controls", body)

    def mitigation_page(self, mid: str, m: dict) -> None:
        d = 2
        shown = {"id", "name", "mitigation_class", "purpose", "implementations"}
        fields = "".join(
            f"<h3>{esc(label(k))}</h3>{generic(m.get(k))}"
            for k in [*MITIGATION_ORDER, *sorted(set(m) - set(MITIGATION_ORDER))]
            if k not in shown and k in m and m.get(k) not in (None, [], {})
        )
        used = "".join(
            f"<li>{self.ref(d, tid)} ({esc(strength)}) {esc(self.threats[tid].get('title'))}</li>"
            for tid, strength in self.used_by.get(mid, [])
        )
        impls = m.get("implementations") or []
        impl_html = generic(impls) if impls else (
            '<p class="muted">No implementation recorded. Treat this control as a '
            "recommendation until one is.</p>"
        )
        body = (
            f'<p class="muted"><code>{esc(mid)}</code> {esc(m.get("mitigation_class"))}</p>'
            f"<h1>{esc(m.get('name'))}</h1>{prose(m.get('purpose'))}"
            f'<div class="box key"><h3>Implementations here</h3>{impl_html}</div>'
            f"<h2>Used by threats</h2>{('<ul>' + used + '</ul>') if used else '<p class=muted>No threat links this control.</p>'}"
            f"<h2>The card</h2>{fields or '<p class=muted>Only the name and purpose are written.</p>'}"
            f"<h2>Named by</h2>{self.named_by_html(mid)}"
            f'<p class="muted">Source file: <code>catalog/mitigations/{esc(mid)}.yaml</code></p>'
        )
        self.site.write(f"mitigations/{mid}/index.html", mid, body)

    # coverage --------------------------------------------------------------- #
    def coverage_page(self) -> None:
        d = 1
        parts = []
        for src in self.coverage:
            s, c = src["source"], src["counts"]
            rows = "".join(
                f"<tr><td>{esc(e['ref'])}</td><td>{esc(e['title'])}"
                f"{' <span class=muted>(' + esc(e['maturity']) + ')</span>' if e.get('maturity') else ''}"
                f"</td><td>{esc(e['state'])}</td>"
                f"<td>{' '.join(self.ref(d, i) for i in [*e.get('threats', []), *e.get('mitigations', [])])}"
                f"{prose(e.get('note'))}</td></tr>"
                for e in src["entries"]
            )
            parts.append(
                f"<h2>{esc(s['title'])} {esc(s['version'])}</h2>"
                f'<p class="muted">Read against the source on {esc(s["checked"])}. '
                f'<a href="{esc(s["url"])}" rel="noopener noreferrer">Source</a>. '
                f"{c['covered']} covered, {c['out_of_scope']} out of scope, {c['gap']} gap.</p>"
                '<div class="scroll"><table><tr><th>Entry</th><th>Name</th><th>State</th>'
                f"<th>Answered by, or why not</th></tr>{rows}</table></div>"
            )
        body = (
            "<h1>Coverage</h1><p>Every entry of each tracked list has a row, whether or not "
            "the catalog answers it. <b>Covered</b> names what answers it. <b>Out of scope</b> "
            "says why the catalog deliberately does not. <b>Gap</b> is an open item.</p>"
            + "".join(parts)
        )
        self.site.write("coverage/index.html", "Coverage", body)

    # reports ---------------------------------------------------------------- #
    def report_list(self) -> None:
        if not self.reports:
            body = (
                "<h1>Reports</h1><p class=\"muted\">This build has no reports. They are "
                "included only when <code>keel site</code> is given <code>--reports</code>, "
                "so that findings are never published by default.</p>"
            )
            self.site.write("reports/index.html", "Reports", body)
            return
        rows = "".join(
            f'<tr><td><a href="{esc(r.system_id)}/{esc(r.date)}/index.html">{esc(r.system_name)}</a></td>'
            f"<td>{esc(r.date)}</td><td>{esc(r.status)}</td><td>{esc(r.assessor)}</td>"
            f'<td class="num">{len(r.findings)}</td>'
            f'<td class="num">{sum(1 for f in r.findings if f.risk.severity == "high")}</td></tr>'
            for r in self.reports
        )
        body = (
            "<h1>Reports</h1><p>One assessment of one system on one date. A final report is "
            "signed off and does not change; a re-assessment is a new date.</p>"
            '<div class="scroll"><table><tr><th>System</th><th>Date</th><th>Status</th>'
            '<th>Assessor</th><th class="num">Findings</th><th class="num">High severity</th>'
            f"</tr>{rows}</table></div>"
        )
        self.site.write("reports/index.html", "Reports", body)

    def report_page(self, r: Report) -> None:
        d = 3
        data = r.model_dump(mode="json")
        findings = sorted(
            r.findings,
            key=lambda f: (LEVELS.get(f.risk.severity, 0), LEVELS.get(f.risk.likelihood, 0)),
            reverse=True,
        )
        summary = "".join(
            f'<tr><td><a href="#{esc(f.id)}">{esc(f.id)}</a></td>'
            f"<td>{self.vocab_name('harm', f.harm)}</td><td>{level(f.risk.severity)}</td>"
            f"<td>{level(f.risk.likelihood)}</td>"
            f"<td>{'catalog' if f.from_catalog else 'new, not in the catalog'}</td></tr>"
            for f in findings
        )
        known_finding = {
            "id", "from_catalog", "scenario", "source", "asset", "attack_surface",
            "vulnerability", "exploitation_complexity", "harm", "risk", "delta",
            "requirements", "ignored_mitigations",
        }
        blocks = []
        for f in findings:
            fd = f.model_dump(mode="json")
            reqs = "".join(
                "<tr><td>"
                + (self.ref(d, q["mitigation_id"]) if q.get("mitigation_id") else prose(q.get("description")))
                + f"</td><td>{esc(IN_PLACE.get(q.get('coverage_status'), q.get('coverage_status')))}"
                f"{prose(q.get('coverage_note'))}</td>"
                f"<td>{'yes' if q.get('included') else 'no'}</td></tr>"
                for q in fd.get("requirements") or []
            )
            ignored = "".join(
                f"<li>{self.ref(d, i['mitigation_id'])}: {esc(i['reason'])}</li>"
                for i in fd.get("ignored_mitigations") or []
            )
            extra = {k: v for k, v in fd.items() if k not in known_finding}
            blocks.append(
                f'<section class="box" id="{esc(f.id)}"><h3>{self.ref(d, f.id) if f.from_catalog else esc(f.id)}: '
                f"{level(f.risk.severity)} severity, {level(f.risk.likelihood)} likelihood</h3>"
                f"{prose(f.scenario)}"
                f"<dl><dt>Who or what drives it</dt><dd>{self.vocab_name('source', f.source.who)}: "
                f"{esc(f.source.motive)}. Access: {esc(f.source.access)}</dd>"
                f"<dt>Asset</dt><dd>{esc(f.asset)}</dd>"
                f"<dt>Reached over</dt><dd>{self.vocab_name('surface', f.attack_surface)}</dd>"
                f"<dt>Vulnerability</dt><dd>{prose(f.vulnerability)}</dd>"
                f"<dt>Effort to exploit</dt><dd>{level(f.exploitation_complexity)}</dd>"
                f"<dt>Why this grade</dt><dd>{prose(f.risk.reasoning)}</dd>"
                f"<dt>What the AI integration changed</dt><dd>{prose(f.delta)}</dd></dl>"
                + ("<h3>Requirements</h3><div class=\"scroll\"><table><tr><th>Control or ask</th>"
                   f"<th>In place here?</th><th>In the hand-off</th></tr>{reqs}</table></div>" if reqs else "")
                + (f"<h3>Linked controls that do not apply here</h3><ul>{ignored}</ul>" if ignored else "")
                + (generic(extra) if extra else "")
                + "</section>"
            )
        discarded = "".join(
            f"<tr><td>{self.ref(d, x.id)}</td><td>{prose(x.reason)}</td></tr>" for x in r.discarded
        )
        known_report = {
            "system_id", "system_name", "system_description", "date", "assessor", "status",
            "delta_summary", "findings", "discarded", "meta",
            # An extension's own data: Keel stores it and does not show it.
            "extensions",
        }
        extra = {k: v for k, v in data.items() if k not in known_report and v not in (None, [], {})}
        meta = data.get("meta") or {}
        took = _duration(meta.get("started_at"), meta.get("finished_at"))
        banner = (
            '<div class="banner"><b>Draft.</b> The assessor has not signed this off yet; '
            "grades and wording may still change.</div>" if r.status != "final" else ""
        )
        body = (
            f"{banner}<p class=\"muted\">{esc(r.date)} · {esc(r.status)} · assessed by "
            f"{esc(r.assessor)}{(' · took ' + esc(took)) if took else ''}</p>"
            f"<h1>{esc(r.system_name)}</h1>{prose(r.system_description)}"
            + (f'<div class="box key"><h3>What changed since the last assessment</h3>'
               f"{prose(r.delta_summary)}</div>" if r.delta_summary else "")
            + f"<h2>Findings ({len(findings)})</h2>"
            + ('<div class="scroll"><table><tr><th>Threat</th><th>Harm</th><th>Severity</th>'
               f"<th>Likelihood</th><th>Origin</th></tr>{summary}</table></div>" if findings
               else '<p class="muted">No threat survived the analysis.</p>')
            + "".join(blocks)
            + (f"<h2>Ruled out, with the reason</h2><div class=\"scroll\"><table><tr><th>Threat</th>"
               f"<th>Why it does not apply</th></tr>{discarded}</table></div>" if discarded else "")
            + (f"<h2>Other fields</h2>{generic(extra)}" if extra else "")
            + ("<details><summary>How this assessment ran</summary>"
               f"{generic({k: v for k, v in meta.items() if k not in ('started_at', 'finished_at')})}"
               "</details>" if any(meta.get(k) for k in meta if k not in ("started_at", "finished_at")) else "")
            + f'<p class="muted">Source file: <code>reports/{esc(r.system_id)}/{esc(r.date)}.yaml</code></p>'
        )
        self.site.write(f"reports/{r.system_id}/{r.date}/index.html", r.system_name, body)

    def build(self) -> None:
        self.overview()
        self.threat_list()
        for tid, t in self.threats.items():
            self.threat_page(tid, t)
        self.mitigation_list()
        for mid, m in self.mitigations.items():
            self.mitigation_page(mid, m)
        self.coverage_page()
        self.report_list()
        for r in self.reports:
            self.report_page(r)


def _duration(start: str | None, end: str | None) -> str:
    try:
        a = datetime.datetime.fromisoformat(str(start))
        b = datetime.datetime.fromisoformat(str(end))
        minutes = round((b - a).total_seconds() / 60)
    except (TypeError, ValueError):
        return ""
    if minutes <= 0:
        return ""
    return f"{minutes} min" if minutes < 60 else f"{minutes // 60} h {minutes % 60:02d} min"


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #
def _prepare(out: Path) -> None:
    """Empty the output folder, but only one this command made, or an empty one."""
    if out.exists():
        if not out.is_dir():
            raise SystemExit(f"{out} exists and is not a folder.")
        if any(out.iterdir()) and not (out / MARKER).is_file():
            raise SystemExit(
                f"{out} is not empty and was not built by `keel site`. "
                "Pick an empty folder, or delete this one yourself."
            )
        shutil.rmtree(out)
    out.mkdir(parents=True)


def build_site(
    out: Path,
    reports_dir: Path | None = None,
    include_drafts: bool = False,
    title: str = "Keel",
) -> dict[str, int]:
    """Build the site into `out`. Returns how many pages and reports went in."""
    out = Path(out)
    _prepare(out)
    store = get_store()
    commit = _commit(store.dir)
    built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if commit:
        built += f" from commit {commit}"
    site = Site(out, title, built)
    reports = load_reports(reports_dir, include_drafts)
    Builder(site, reports).build()
    (out / MARKER).write_text("built by keel site\n", encoding="utf-8")
    # GitHub Pages runs Jekyll over a folder unless told not to; these files are final.
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return {"pages": len(site.pages), "reports": len(reports)}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="keel site",
        description="Build a read-only HTML copy of the catalog (and, if asked, the "
        "reports) for GitHub Pages, GitLab Pages or any static host.",
    )
    p.add_argument("--out", default="public", help="output folder (default: public)")
    p.add_argument(
        "--reports", metavar="DIR", default=None,
        help="include the final reports from this folder; without it no report is published",
    )
    p.add_argument(
        "--include-drafts", action="store_true",
        help="also publish draft reports, marked as drafts",
    )
    p.add_argument("--title", default="Keel", help="site name shown on every page")
    return p


def main(argv: list[str]) -> None:
    args = parser().parse_args(argv)
    if args.include_drafts and not args.reports:
        raise SystemExit("--include-drafts needs --reports.")
    reports_dir = Path(args.reports) if args.reports else None
    if reports_dir is not None and not reports_dir.is_dir():
        raise SystemExit(f"--reports {reports_dir}: no such folder.")
    result = build_site(Path(args.out), reports_dir, args.include_drafts, args.title)
    print(
        f"Wrote {result['pages']} pages to {args.out} "
        f"({result['reports']} report(s) included).",
        file=sys.stderr,
    )
