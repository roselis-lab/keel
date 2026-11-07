"""A report as a Confluence page (storage format) and Jira tickets (wiki markup).

The page is written for the people who read it, in that order:

1. one line on what was found, and a table of what to build: most developers stop here;
2. each risk with its picture, what happens and why it matters in two sentences, and the fix;
3. the reasoning, the review and the evidence, folded under "How we know";
4. what was ruled out and why, and the questions still open.

Nothing in the report is dropped: what a developer does not need is folded, not cut.

A ticket is one thing to build, not one finding. Findings that one fix closes share a
ticket, so a re-assessment that finds the same gap again updates that ticket instead of
filing another. The key is the system plus the catalog control, or, for an ask with no
card, the finding's root cause. Every value from the report is escaped: a report can
quote hostile text, a prompt or a payload, and it must arrive as text.
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field
from typing import Any

from keel.schemas.report import Finding, Report, Requirement, RiskInfo

LIKELY = {"high": "likely", "medium": "possible", "low": "unlikely"}
COLOUR = {"high": "Red", "medium": "Yellow", "low": "Green"}
LEVEL = {"high": 3, "medium": 2, "low": 1}


# --------------------------------------------------------------------------- #
# What to build
# --------------------------------------------------------------------------- #
@dataclass
class Fix:
    """What must hold, where, and how to tell it is done, from the requirement or,
    for a catalog control, from its card."""
    summary: str
    must_hold: str
    where: str
    done_when: list[str]


@dataclass
class Ticket:
    key: str
    label: str
    fix: Fix
    items: list[tuple[Finding, Requirement]] = field(default_factory=list)

    @property
    def findings(self) -> list[Finding]:
        seen: dict[str, Finding] = {}
        for f, _ in self.items:
            seen.setdefault(f.id, f)
        return list(seen.values())


def to_build(req: Requirement) -> bool:
    return req.included is not False and req.coverage_status != "already_covered"


def fix_of(req: Requirement, cards: dict[str, dict[str, Any]]) -> Fix:
    card = cards.get(req.mitigation_id or "", {}) if req.mitigation_id else {}
    locus = card.get("locus") or {}
    where = req.enforce_at or (
        f"{locus.get('value')}: {locus.get('note')}" if locus.get("value") else "not stated"
    )
    done = [req.done_check] if req.done_check else [
        v.get("criterion", "") for v in (card.get("validation") or []) if v.get("criterion")
    ]
    summary = (
        card.get("name") or req.description or req.invariant or req.mitigation_id or "Fix"
    )
    must = req.invariant or card.get("purpose") or req.description or summary
    return Fix(summary=summary, must_hold=must, where=where, done_when=done or ["not stated"])


def ticket_key(system_id: str, finding: Finding, req: Requirement, ask_no: int) -> str:
    if req.mitigation_id:
        return f"{system_id}/{req.mitigation_id}"
    return f"{system_id}/{finding.root_cause or finding.id}/ask-{ask_no}"


def label_for(key: str) -> str:
    """A Jira label is one token with no spaces; a hash keeps it short and stable."""
    return "keel-" + hashlib.sha256(key.encode()).hexdigest()[:12]


def tickets(report: Report, cards: dict[str, dict[str, Any]]) -> list[Ticket]:
    out: dict[str, Ticket] = {}
    for f in sorted_findings(report):
        ask_no = 0
        for req in f.requirements:
            if not req.mitigation_id:
                ask_no += 1
            if not to_build(req):
                continue
            key = ticket_key(report.system_id, f, req, ask_no)
            t = out.get(key)
            if t is None:
                t = out[key] = Ticket(key=key, label=label_for(key), fix=fix_of(req, cards))
            t.items.append((f, req))
    return list(out.values())


def sorted_findings(report: Report) -> list[Finding]:
    def rank(f: Finding) -> tuple[int, int]:
        now = f.risk_today or f.risk
        return (-LEVEL[f.risk.severity], -LEVEL[now.likelihood])
    return sorted(report.findings, key=rank)


def fix_on_picture(f: Finding, cards: dict[str, dict[str, Any]]) -> str | None:
    for req in f.requirements:
        if to_build(req):
            return fix_of(req, cards).must_hold
    return None


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
_REFS = re.compile(r"\s*\[\d+\](\[\d+\])*")


def plain(text: str | None) -> str:
    """Prose without the evidence markers [1][2]: the page lists evidence on its own."""
    return _REFS.sub("", text or "").strip()


def title_of(f: Finding) -> str:
    """The first clause of the scenario: it is written as what happens, which is what a
    reader needs as a heading. Long ones are cut at a word."""
    first = re.split(r"(?<=[.;:])\s", plain(f.scenario), maxsplit=1)[0].rstrip(".;:")
    if len(first) > 110:
        first = first[:110].rsplit(" ", 1)[0] + "..."
    return first or f.id


def risk_label(r: RiskInfo, when: str = "") -> str:
    # Harm and likelihood stay apart, as in the report: folding them would hide a high harm.
    tail = f" {when}" if when else ""
    return f"{r.severity} harm · {LIKELY[r.likelihood]}{tail}"


def picture_name(f: Finding) -> str:
    return f"keel-chain-{f.id}.png"


# --------------------------------------------------------------------------- #
# Confluence storage format
# --------------------------------------------------------------------------- #
def x(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def status(colour: str, title: str) -> str:
    return (
        '<ac:structured-macro ac:name="status">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{x(title)}</ac:parameter>'
        "</ac:structured-macro>"
    )


def panel(kind: str, body: str) -> str:
    return (
        f'<ac:structured-macro ac:name="{kind}">'
        f"<ac:rich-text-body>{body}</ac:rich-text-body></ac:structured-macro>"
    )


def expand(title: str, body: str) -> str:
    return (
        '<ac:structured-macro ac:name="expand">'
        f'<ac:parameter ac:name="title">{x(title)}</ac:parameter>'
        f"<ac:rich-text-body>{body}</ac:rich-text-body></ac:structured-macro>"
    )


def risk_badges(f: Finding) -> str:
    if f.risk_today:
        return (
            status(COLOUR[f.risk_today.severity], risk_label(f.risk_today, "today")) + " "
            + status(COLOUR[f.risk.severity], risk_label(f.risk, "at launch"))
        )
    return status(COLOUR[f.risk.severity], risk_label(f.risk))


def _link(url: str | None, text: str) -> str:
    if url and url.startswith("https://"):
        return f'<a href="{x(url)}">{x(text)}</a>'
    return x(text)


def _evidence(report: Report, ids: list[int]) -> str:
    by_id = {e.id: e for e in report.evidence}
    items = []
    for i in ids:
        e = by_id.get(i)
        if e is None:
            continue
        where = (
            f"{e.path}:{e.lines}" if e.path and e.lines else e.path or e.command or e.url or e.kind
        )
        items.append(
            f"<li><strong>[{i}]</strong> {_link(e.url, where)}"
            f"<br/><code>{x(e.quote)}</code></li>"
        )
    return f"<ul>{''.join(items)}</ul>" if items else "<p>None cited.</p>"


def page_title(report: Report) -> str:
    return f"AI security review: {report.system_name} ({report.date})"


def storage(
    report: Report,
    planned: list[Ticket],
    cards: dict[str, dict[str, Any]],
    issue_links: dict[str, tuple[str, str]],
    source: str,
) -> str:
    """`issue_links` maps a ticket label to (issue key, issue URL) once they exist."""
    fs = sorted_findings(report)
    out: list[str] = []
    banner = (
        f"<p>Generated by Keel from <code>{x(source)}</code>. Edits made here are "
        "overwritten on the next publish: change the report instead.</p>"
    )
    if report.status != "final":
        banner += "<p><strong>Draft.</strong> This assessment is not signed off yet.</p>"
    out.append(panel("info", banner))
    out.append(
        f"<p><strong>{len(fs)} risk(s) found, {len(planned)} thing(s) to build.</strong> "
        f"{len(report.discarded)} ruled out, {len(report.open_questions)} question(s) open. "
        f"Assessed {x(report.date)} by {x(report.assessor.split('<')[0].strip())}.</p>"
    )
    if report.delta_summary:
        out.append(f"<p><strong>Since the last review:</strong> {x(report.delta_summary)}</p>")

    if planned:
        out.append("<h2>What to build</h2>")
        rows = []
        for t in planned:
            worst = max(t.findings, key=lambda f: LEVEL[f.risk.severity])
            link = issue_links.get(t.label)
            ticket = _link(link[1], link[0]) if link else "not filed"
            rows.append(
                f"<tr><td>{risk_badges(worst)}</td><td>{x(t.fix.must_hold)}</td>"
                f"<td>{x(t.fix.where)}</td><td>{'<br/>'.join(x(d) for d in t.fix.done_when)}</td>"
                f"<td>{ticket}</td></tr>"
            )
        out.append(
            "<table><tbody><tr><th>Risk</th><th>Must hold</th><th>Where</th>"
            "<th>Done when</th><th>Ticket</th></tr>" + "".join(rows) + "</tbody></table>"
        )

    out.append("<h2>The risks</h2>")
    for f in fs:
        badges = risk_badges(f)
        if f.origin == "legacy":
            badges += " " + status("Grey", "legacy: existed before the AI")
        if f.review:
            badges += " " + status("Blue", f"checked: {f.review.verdict}")
        out.append(f"<h3>{x(title_of(f))}</h3><p>{badges} <code>{x(f.id)}</code></p>")
        out.append(
            f'<ac:image ac:width="760" ac:alt="{x(title_of(f))}">'
            f'<ri:attachment ri:filename="{x(picture_name(f))}"/></ac:image>'
        )
        out.append(f"<p><strong>What happens.</strong> {x(plain(f.scenario))}</p>")
        out.append(f"<p><strong>Why it matters.</strong> {x(plain(f.risk.reasoning))}</p>")
        if f.risk_today:
            out.append(
                f"<p><strong>Today.</strong> {x(plain(f.risk_today.reasoning))}</p>"
            )
        for req in f.requirements:
            if not to_build(req):
                continue
            fix = fix_of(req, cards)
            out.append(panel(
                "note",
                f"<p><strong>Fix.</strong> {x(fix.must_hold)}</p>"
                f"<p><strong>Where:</strong> {x(fix.where)}<br/>"
                f"<strong>Done when:</strong> {'; '.join(x(d) for d in fix.done_when)}</p>",
            ))
        covered = [r for r in f.requirements if not to_build(r)]
        details = (
            f"<p><strong>Who and why:</strong> {x(f.source.who)}, wants {x(f.source.motive)}, "
            f"reaches it through {x(f.source.access)}.</p>"
            f"<p><strong>Weak spot:</strong> {x(f.vulnerability)}. "
            f"Effort for an attacker: {x(f.exploitation_complexity)}.</p>"
            f"<p><strong>What the AI changed:</strong> {x(plain(f.delta))}</p>"
        )
        if covered:
            details += "<p><strong>Already in place:</strong> " + "; ".join(
                x(r.mitigation_id or r.description) for r in covered
            ) + "</p>"
        if f.review:
            details += (
                f"<p><strong>Refutation tried by {x(f.review.by)}:</strong> "
                f"{x(f.review.verdict)}. {x(f.review.note)}</p>"
            )
        details += "<p><strong>Evidence</strong></p>" + _evidence(report, f.evidence)
        out.append(expand("How we know, for reviewers", details))

    if report.discarded:
        out.append(
            "<h2>Ruled out</h2><p>These came up and do not apply to this system. "
            "The next review starts from this list.</p>"
        )
        rows = "".join(
            f"<tr><td><code>{x(d.id)}</code></td><td>{x(plain(d.reason))}</td>"
            f"<td>{'refuted in review' if d.by == 'review' else 'cannot be reached'}</td></tr>"
            for d in report.discarded
        )
        out.append(
            "<table><tbody><tr><th>Threat</th><th>Why it does not apply</th><th>How</th></tr>"
            + rows + "</tbody></table>"
        )

    if report.open_questions or report.paused:
        out.append("<h2>Still open</h2>")
        for q in report.open_questions:
            body = (
                f"<p><strong>{x(q.question)}</strong></p>"
                f"<p>Waiting on it: {x(q.needed_for)}"
                + (f"<br/>How to check: {x(q.how_to_check)}" if q.how_to_check else "")
                + (f"<br/>Answer: {x(q.answer)}" if q.answer else "")
                + "</p>"
            )
            out.append(panel("warning", body))
        if report.paused:
            out.append("<p>Branches waiting on these answers: " + ", ".join(
                f"<code>{x(p.id)}</code>" for p in report.paused
            ) + ".</p>")

    if report.surfaces:
        rows = "".join(
            f"<tr><td>{x(s.name)}</td><td><code>{x(s.where)}</code></td>"
            f"<td>{x(', '.join(s.outcome) or s.note or '')}</td></tr>"
            for s in report.surfaces
        )
        out.append(expand(
            f"Every surface walked ({len(report.surfaces)})",
            "<table><tbody><tr><th>Surface</th><th>Where</th><th>Outcome</th></tr>"
            + rows + "</tbody></table>",
        ))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Jira wiki markup
# --------------------------------------------------------------------------- #
_WIKI_SPECIAL = re.compile(r"([*_\-+^~{}\[\]|!#?])")


def w(value: Any) -> str:
    """Report text as literal wiki text: every markup character escaped, one line."""
    text = " ".join(str(value or "").split())
    text = text.replace("\\", "&#92;")
    return _WIKI_SPECIAL.sub(r"\\\1", text)


def ticket_summary(t: Ticket) -> str:
    # Jira limits a summary to 255 characters and takes it as plain text.
    s = " ".join(t.fix.summary.split())
    return s if len(s) <= 250 else s[:247] + "..."


def ticket_wiki(
    report: Report, t: Ticket, page_url: str | None, with_pictures: bool
) -> str:
    lines: list[str] = ["h3. Why"]
    for f in t.findings:
        lines.append(w(plain(f.scenario)))
        lines.append("")
        if with_pictures:
            lines.append(f"!{picture_name(f)}|width=760!")
            lines.append("")
        risk = (
            f"{risk_label(f.risk_today, 'today')}; {risk_label(f.risk, 'at launch')}"
            if f.risk_today else risk_label(f.risk)
        )
        lines.append(f"*Risk:* {w(risk)}. {w(plain(f.risk.reasoning))}")
        lines.append("")
    lines += ["h3. What must hold", w(t.fix.must_hold), "", f"*Where:* {w(t.fix.where)}", ""]
    lines.append("h3. Done when")
    lines += [f"* {w(d)}" for d in t.fix.done_when]
    lines += ["", "----"]
    origin = f"From the Keel assessment of {w(report.system_name)}, {w(report.date)}"
    if page_url and page_url.startswith("https://"):
        origin += f": [{w(page_title(report))}|{page_url}]"
    findings = ", ".join(w(f.id) for f in t.findings)
    lines.append(f"{origin} (finding {findings}). Keel never changes this ticket's status.")
    return "\n".join(lines)
