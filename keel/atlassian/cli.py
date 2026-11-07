"""`keel export` and `keel publish`.

    keel export REPORT.yaml --out DIR
    keel publish REPORT.yaml [--confluence-space KEY [--parent ID]]
                             [--jira-project KEY [--issue-type Task] [--security-level NAME]]
                             [--dry-run] [--allow-draft]

`export` writes the page, the pictures and the ticket texts to a folder and sends nothing.
`publish` pushes them with the person's own token, from the environment, never from the
command line, where it would land in the shell history:

    KEEL_CONFLUENCE_URL   https://your-site.atlassian.net/wiki  or  https://confluence.corp
    KEEL_JIRA_URL         https://your-site.atlassian.net       or  https://jira.corp
    KEEL_ATLASSIAN_TOKEN  Cloud API token, or a Data Center personal access token
    KEEL_ATLASSIAN_EMAIL  Cloud only: the account the API token belongs to
    KEEL_CONFLUENCE_TOKEN, KEEL_JIRA_TOKEN  when the two products need different tokens

What was created is written next to the report as `<date>.published.json`, so the next
publish updates the same page and the same tickets. Commit it with the report.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.atlassian import render
from keel.atlassian.client import Api, AtlassianError, Confluence, Jira
from keel.atlassian.picture import chain_png
from keel.schemas.report import Report
from keel.store import get_store
from keel.vocabulary import load_vocabularies


def load(path: Path, allow_draft: bool) -> Report:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        report = Report(**data)
    except (OSError, yaml.YAMLError, TypeError) as e:
        raise SystemExit(f"{path}: cannot read the report ({e}).") from e
    except ValidationError as e:
        raise SystemExit(f"{path}: not a valid report:\n{e}") from e
    if report.status != "final" and not allow_draft:
        raise SystemExit(
            f"{path} is a draft. Finalize it first, or pass --allow-draft: the page will say draft."
        )
    return report


def source_name(path: Path) -> str:
    parts = path.resolve().parts
    return "/".join(parts[-3:]) if len(parts) >= 3 else path.name


class Bundle:
    """Everything one report turns into, computed once."""

    def __init__(self, path: Path, report: Report):
        store = get_store()
        self.path = path
        self.report = report
        self.cards = store.mitigations
        self.vocab = load_vocabularies(store.dir)
        self.tickets = render.tickets(report, self.cards)
        self.pictures = {
            render.picture_name(f): chain_png(report, f, self.vocab, render.fix_on_picture(f, self.cards))
            for f in report.findings
        }

    def page(self, issue_links: dict[str, tuple[str, str]]) -> str:
        return render.storage(self.report, self.tickets, self.cards, issue_links, source_name(self.path))

    def ticket_text(self, t: render.Ticket, page_url: str | None, pictures: bool) -> str:
        return render.ticket_wiki(self.report, t, page_url, pictures)

    def pictures_of(self, t: render.Ticket) -> dict[str, bytes]:
        return {render.picture_name(f): self.pictures[render.picture_name(f)] for f in t.findings}


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
def export(path: Path, out: Path, allow_draft: bool) -> dict[str, int]:
    b = Bundle(path, load(path, allow_draft))
    out.mkdir(parents=True, exist_ok=True)
    (out / "confluence-page.xhtml").write_text(b.page({}), encoding="utf-8")
    for name, data in b.pictures.items():
        (out / name).write_bytes(data)
    jira = out / "jira"
    jira.mkdir(exist_ok=True)
    for n, t in enumerate(b.tickets, 1):
        text = (
            f"Summary: {render.ticket_summary(t)}\nLabels: keel {t.label}\n\n"
            + b.ticket_text(t, None, pictures=True)
        )
        (jira / f"{n:02d}-{t.label}.txt").write_text(text, encoding="utf-8")
    return {"tickets": len(b.tickets), "pictures": len(b.pictures)}


# --------------------------------------------------------------------------- #
# publish
# --------------------------------------------------------------------------- #
def _env(*names: str) -> str | None:
    for n in names:
        if os.environ.get(n):
            return os.environ[n]
    return None


def _api(product: str, url: str | None) -> Api:
    url = url or _env(f"KEEL_{product}_URL")
    token = _env(f"KEEL_{product}_TOKEN", "KEEL_ATLASSIAN_TOKEN")
    if not url or not token:
        raise SystemExit(
            f"Set KEEL_{product}_URL and KEEL_ATLASSIAN_TOKEN (or KEEL_{product}_TOKEN) "
            "in the environment. The token is never taken from the command line."
        )
    try:
        return Api(url, token, _env("KEEL_ATLASSIAN_EMAIL"))
    except AtlassianError as e:
        raise SystemExit(str(e)) from e


def sidecar_path(path: Path) -> Path:
    return path.with_name(path.stem + ".published.json")


def publish(
    path: Path, *, space: str | None, parent: str | None, project: str | None,
    issue_type: str, security_level: str | None, dry_run: bool, allow_draft: bool,
    confluence: Confluence | None = None, jira: Jira | None = None,
    say=print,
) -> dict[str, Any]:
    if not space and not project:
        raise SystemExit("Name at least one target: --confluence-space and/or --jira-project.")
    b = Bundle(path, load(path, allow_draft))
    side_path = sidecar_path(path)
    side: dict[str, Any] = json.loads(side_path.read_text(encoding="utf-8")) if side_path.exists() else {}
    side.setdefault("jira", {})
    title = render.page_title(b.report)

    if dry_run:
        if space:
            say(f"Confluence {space}: page \"{title}\" with {len(b.pictures)} picture(s), "
                "created or updated in place.")
        if project:
            for t in b.tickets:
                known = side["jira"].get(t.label, {}).get("key")
                say(f"Jira {project}: {'update ' + known if known else 'create or update'} "
                    f"\"{render.ticket_summary(t)}\" (label {t.label})")
            if not security_level:
                say("No --security-level: the tickets are visible to everyone who can see "
                    f"project {project}.")
        say("Dry run: nothing was sent.")
        return side

    page = None
    if space:
        confluence = confluence or Confluence(_api("CONFLUENCE", None))
        page = confluence.find_page(space, title)
        if page is None:
            # The page exists before its pictures, or Confluence shows them as unknown.
            page = confluence.create_page(space, title, render.panel("info", "<p>Publishing...</p>"), parent)
            say(f"Confluence: created page {page['id']}")
        side["confluence"] = {"page_id": page["id"], "url": confluence.url_of(page)}

    if project:
        jira = jira or Jira(_api("JIRA", None))
        page_url = (side.get("confluence") or {}).get("url")
        for t in b.tickets:
            fields: dict[str, Any] = {
                "summary": render.ticket_summary(t),
                "description": b.ticket_text(t, page_url, pictures=False),
            }
            found = jira.find_issue(project, t.label)
            if found:
                key = found["key"]
                for name, data in b.pictures_of(t).items():
                    jira.put_attachment(key, name, data)
                fields["description"] = b.ticket_text(t, page_url, pictures=True)
                jira.update_issue(key, fields)
                say(f"Jira: updated {key}")
            else:
                fields.update({
                    "project": {"key": project},
                    "issuetype": {"name": issue_type},
                    "labels": ["keel", f"keel-system-{b.report.system_id}", t.label],
                })
                if security_level:
                    fields["security"] = {"name": security_level}
                key = jira.create_issue(fields)
                say(f"Jira: created {key}")
                # Pictures go up after the issue exists, then the text that shows them.
                for name, data in b.pictures_of(t).items():
                    jira.put_attachment(key, name, data)
                jira.update_issue(key, {"description": b.ticket_text(t, page_url, pictures=True)})
            side["jira"][t.label] = {"key": key, "url": jira.url_of(key)}

    if space and confluence and page:
        for name, data in b.pictures.items():
            confluence.put_attachment(page["id"], name, data)
        fresh = confluence.find_page(space, title) or page
        links = {label: (v["key"], v["url"]) for label, v in side["jira"].items()}
        confluence.update_page(fresh, b.page(links))
        say(f"Confluence: {side['confluence']['url']}")

    side_path.write_text(json.dumps(side, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    say(f"Wrote {side_path.name}; commit it with the report so the next publish updates in place.")
    return side


# --------------------------------------------------------------------------- #
# entry points
# --------------------------------------------------------------------------- #
def export_main(argv: list[str]) -> None:
    p = argparse.ArgumentParser(
        prog="keel export",
        description="Write a report as a Confluence page, pictures and Jira ticket texts. Sends nothing.",
    )
    p.add_argument("report", type=Path, help="the report YAML file")
    p.add_argument("--out", type=Path, required=True, help="folder to write into")
    p.add_argument("--allow-draft", action="store_true", help="export a report that is not final")
    a = p.parse_args(argv)
    r = export(a.report, a.out, a.allow_draft)
    print(f"Wrote the page, {r['pictures']} picture(s) and {r['tickets']} ticket text(s) to {a.out}.",
          file=sys.stderr)


def publish_main(argv: list[str]) -> None:
    p = argparse.ArgumentParser(
        prog="keel publish",
        description="Publish a report to Confluence and/or Jira with your own token.",
    )
    p.add_argument("report", type=Path, help="the report YAML file")
    p.add_argument("--confluence-space", metavar="KEY", help="space to publish the page into")
    p.add_argument("--parent", metavar="PAGE_ID", help="parent page for a new page")
    p.add_argument("--jira-project", metavar="KEY", help="project to file one ticket per thing to build")
    p.add_argument("--issue-type", default="Task", help="issue type for new tickets (default: Task)")
    p.add_argument("--security-level", metavar="NAME",
                   help="Jira issue security level for new tickets, to limit who sees them")
    p.add_argument("--dry-run", action="store_true", help="say what would be sent and send nothing")
    p.add_argument("--allow-draft", action="store_true", help="publish a report that is not final")
    a = p.parse_args(argv)
    try:
        publish(
            a.report, space=a.confluence_space, parent=a.parent, project=a.jira_project,
            issue_type=a.issue_type, security_level=a.security_level,
            dry_run=a.dry_run, allow_draft=a.allow_draft,
            say=lambda m: print(m, file=sys.stderr),
        )
    except AtlassianError as e:
        raise SystemExit(f"Stopped: {e}") from e
