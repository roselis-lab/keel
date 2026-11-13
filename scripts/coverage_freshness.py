"""Is each source pinned in catalog/coverage/ still the latest one upstream?

Run weekly by .github/workflows/coverage-freshness.yml. For every coverage file it asks
the source's own publisher for the current release, compares it with the pinned
`source.version`, and for each source that moved on opens one GitHub issue - or updates
the one already open - saying what changed and how much there is to map. It never edits
the catalog and never opens a pull request: deciding covered, out of scope or gap is a
person's reading of the new release.

The signal is chosen per source, the most reliable one each publisher offers:

  mitre-atlas    GitHub releases of mitre-atlas/atlas-data (`releases/latest`). When the
                 tag is newer, the release's dist/manifest.yaml names the data file, and
                 its techniques are diffed against the rows to count what is new.
  owasp-llm,     The OWASP GenAI project's WordPress REST API, resource posts. Editions
  owasp-agentic  are named by year in the resource title ("... for 2026"); the newest
                 year found is the current edition. The site has no release feed.
  owasp-mcp      The list page in OWASP/www-project-mcp-top-10 (tab_top10.md), which
                 states "version [v0.1]". The project publishes no releases or tags.
  google-saif    The last commit touching yaml/ in google/saif-data, against the date in
                 the pinned version ("saif-data @ <date>"). The repo has no releases.
  eu-ai-act      EUR-Lex's page listing every version of CELEX 32024R1689: the newest
                 consolidated text (02024R1689-<yyyymmdd>) against the pinned one in
                 source.url.

A source with no checker, or whose publisher could not be reached, is reported in the
run summary and never turned into an issue: a network blip is not a new release.

Usage:
  python scripts/coverage_freshness.py [--catalog DIR] [--repo OWNER/NAME] [--dry-run]

GITHUB_TOKEN authorises the GitHub API calls and the issue writes.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

USER_AGENT = "keel-coverage-freshness"
MARKER = "<!-- coverage-freshness:{id} -->"

# fetch(url) -> response body as text. Injected so tests run on fixtures, offline.
Fetch = Callable[[str], str]


@dataclass
class Result:
    source_id: str
    title: str
    pinned: str
    latest: str | None = None
    outdated: bool = False
    summary: str = ""            # one line, used in the issue title
    details: list[str] = field(default_factory=list)
    error: str | None = None


# --------------------------------------------------------------------------- #
# Checkers: (source block, refs already in the file, fetch) -> Result
# --------------------------------------------------------------------------- #
def _calver(v: str) -> tuple[int, ...]:
    """'v2026.10' / '2026.10' / '5.6.0' -> comparable tuple. Calendar versions start with a
    four-digit year, so any of them sorts after the old 5.x numbering."""
    return tuple(int(x) for x in re.findall(r"\d+", v))


def atlas_parents(data: dict) -> dict[str, str]:
    """Parent techniques (no sub-techniques) of an ATLAS v6 data file: id -> name."""
    tech = data.get("techniques") or {}
    return {k: v["name"] for k, v in tech.items() if re.fullmatch(r"AML\.T\d{4}", k)}


def check_atlas(source: dict, refs: set[str], fetch: Fetch) -> Result:
    r = Result(source["id"], source["title"], str(source["version"]))
    rel = json.loads(fetch("https://api.github.com/repos/mitre-atlas/atlas-data/releases/latest"))
    tag = rel["tag_name"]
    r.latest = tag.lstrip("v")
    if _calver(r.latest) <= _calver(r.pinned):
        return r
    r.outdated = True
    raw = f"https://raw.githubusercontent.com/mitre-atlas/atlas-data/{tag}/dist/"
    manifest = yaml.safe_load(fetch(raw + "manifest.yaml")) or []
    entry = next((m for m in manifest if str(m.get("release")) == r.latest), None)
    paths = [v["path"] for v in (entry or {}).get("versions", []) if str(v.get("path", "")).startswith("v6/")]
    if not paths:
        r.summary = f"{r.pinned} → {tag}: release out, technique count unknown"
        r.details.append(f"The manifest of {tag} names no v6 data file; read the release by hand.")
        return r
    techniques = atlas_parents(yaml.safe_load(fetch(raw + paths[0])) or {})
    new = sorted(set(techniques) - refs)
    gone = sorted(refs - set(techniques))
    r.summary = f"{r.pinned} → {tag}: {len(new)} techniques to map"
    r.details.append(f"Release: {rel.get('html_url', raw)}")
    r.details.append(f"{len(techniques)} techniques in {tag} against {len(refs)} rows pinned.")
    if new:
        r.details.append("New, each needs a row (covered / out_of_scope with a note / gap):")
        r.details += [f"- {k} {techniques[k]}" for k in new]
    if gone:
        r.details.append("No longer in the release (merged or withdrawn), move or drop the row:")
        r.details += [f"- {k}" for k in gone]
    r.details.append("Renamed or regrouped techniques are not counted; diff the titles too.")
    return r


GENAI_RESOURCES = ("https://genai.owasp.org/wp-json/wp/v2/resource"
                   "?search={q}&per_page=100&_fields=title,link,date")


def _owasp_genai(pattern: str, query: str) -> Callable[[dict, set[str], Fetch], Result]:
    rx = re.compile(pattern, re.IGNORECASE)

    def check(source: dict, refs: set[str], fetch: Fetch) -> Result:
        r = Result(source["id"], source["title"], str(source["version"]))
        posts = json.loads(fetch(GENAI_RESOURCES.format(q=urllib.parse.quote(query))))
        editions = []
        for p in posts:
            title = html.unescape(p.get("title", {}).get("rendered", "")).strip()
            m = rx.match(title)
            if m:
                editions.append((int(m.group(1)), title, p.get("link"), p.get("date", "")[:10]))
        if not editions:
            r.error = f"no resource titled like {pattern!r} on genai.owasp.org"
            return r
        year, title, link, date = max(editions)
        r.latest = str(year)
        if year > int(re.sub(r"\D", "", r.pinned) or 0):
            r.outdated = True
            r.summary = f"{r.pinned} → {year}: {len(refs)} entries to re-read"
            r.details.append(f"New edition: {title}, published {date}: {link}")
            r.details.append("Every entry gets a row again; ids and titles may have moved.")
        return r

    return check


def check_owasp_mcp(source: dict, refs: set[str], fetch: Fetch) -> Result:
    r = Result(source["id"], source["title"], str(source["version"]))
    page = fetch("https://raw.githubusercontent.com/OWASP/www-project-mcp-top-10/main/tab_top10.md")
    m = re.search(r"version\s*\[?\s*(v?\d+(?:\.\d+)*)\s*\]?", page, re.IGNORECASE)
    if not m:
        r.error = "tab_top10.md states no version"
        return r
    r.latest = m.group(1)
    if r.latest.lstrip("v") != r.pinned.lstrip("v"):
        r.outdated = True
        listed = set(re.findall(r"MCP0?(\d+):\d{4}", page))
        r.summary = f"{r.pinned} → {r.latest}: {len(listed) or len(refs)} entries to re-read"
        r.details.append("List: https://owasp.org/www-project-mcp-top-10/ (tab Top 10).")
    return r


def check_saif(source: dict, refs: set[str], fetch: Fetch) -> Result:
    r = Result(source["id"], source["title"], str(source["version"]))
    pinned = re.search(r"(\d{4}-\d{2}-\d{2})", r.pinned)
    commits = json.loads(fetch("https://api.github.com/repos/google/saif-data/commits?path=yaml&per_page=1"))
    if not commits or not pinned:
        r.error = "no commit under yaml/ or no date in the pinned version"
        return r
    last = commits[0]["commit"]["committer"]["date"][:10]
    r.latest = f"saif-data @ {last}"
    if last > pinned.group(1):
        r.outdated = True
        r.summary = f"data changed {last}: diff yaml/ against the {len(refs)} rows"
        r.details.append(f"Last change: {commits[0].get('html_url', '')}")
    return r


def check_eu_ai_act(source: dict, refs: set[str], fetch: Fetch) -> Result:
    r = Result(source["id"], source["title"], str(source["version"]))
    pinned = re.search(r"02024R1689-(\d{8})", str(source.get("url", "")))
    page = fetch("https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32024R1689")
    found = sorted(set(re.findall(r"02024R1689-(\d{8})", page)))
    if not found or not pinned:
        r.error = "no consolidated version listed, or none pinned in source.url"
        return r
    r.latest = f"consolidated {found[-1]}"
    if found[-1] > pinned.group(1):
        r.outdated = True
        r.summary = f"consolidated {pinned.group(1)} → {found[-1]}: check amended articles"
        r.details.append(f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-{found[-1]}")
        r.details.append("A regulation is mapped in full: new articles fail `keel validate` until mapped.")
    return r


CHECKERS: dict[str, Callable[[dict, set[str], Fetch], Result]] = {
    "mitre-atlas": check_atlas,
    "owasp-agentic": _owasp_genai(r"^OWASP (?:GenAI )?Top 10 for Agentic Applications (?:for )?(20\d\d)$",
                                  "Top 10 for Agentic Applications"),
    "owasp-llm": _owasp_genai(r"^OWASP (?:GenAI )?(?:LLM Top 10|Top 10 for LLM Applications?) (?:for )?(20\d\d)$",
                              "LLM Top 10"),
    "owasp-mcp": check_owasp_mcp,
    "google-saif": check_saif,
    "eu-ai-act": check_eu_ai_act,
}


def check_all(catalog: Path, fetch: Fetch) -> list[Result]:
    out = []
    for path in sorted((catalog / "coverage").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        source = doc["source"]
        refs = {e["ref"] for e in doc.get("entries", [])}
        checker = CHECKERS.get(source["id"])
        if checker is None:
            out.append(Result(source["id"], source["title"], str(source["version"]),
                              error="no checker for this source"))
            continue
        try:
            out.append(checker(source, refs, fetch))
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as e:
            out.append(Result(source["id"], source["title"], str(source["version"]),
                              error=f"{type(e).__name__}: {e}"))
    return out


# --------------------------------------------------------------------------- #
# Issues
# --------------------------------------------------------------------------- #
def issue_title(r: Result) -> str:
    return f"Coverage: {r.title} {r.summary}"


def issue_body(r: Result) -> str:
    return "\n".join([
        MARKER.format(id=r.source_id),
        f"`catalog/coverage/{r.source_id}.yaml` is pinned to **{r.pinned}**; upstream is now "
        f"**{r.latest}**.",
        "",
        *r.details,
        "",
        "Bump `source.version`, `entry_count` and `checked`, then give every new or changed "
        "entry a row and run `keel validate`. Opened by the weekly coverage freshness check; "
        "it updates this issue and never edits the catalog.",
    ])


def plan_issues(results: list[Result], open_issues: list[dict]) -> list[tuple[str, int | None, dict]]:
    """What to write: ("create", None, payload) or ("update", number, payload). An open
    issue already carrying the same title and body is left alone."""
    by_marker = {}
    for i in open_issues:
        for r in results:
            if MARKER.format(id=r.source_id) in (i.get("body") or ""):
                by_marker[r.source_id] = i
    actions = []
    for r in results:
        if not r.outdated:
            continue
        payload = {"title": issue_title(r), "body": issue_body(r)}
        existing = by_marker.get(r.source_id)
        if existing is None:
            actions.append(("create", None, payload))
        elif existing.get("title") != payload["title"] or existing.get("body") != payload["body"]:
            actions.append(("update", existing["number"], payload))
    return actions


def _github(method: str, url: str, token: str, payload: dict | None = None):
    req = urllib.request.Request(url, method=method, data=json.dumps(payload).encode() if payload else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode() or "null")


def make_fetch(token: str) -> Fetch:
    def fetch(url: str) -> str:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", USER_AGENT)
        if token and url.startswith("https://api.github.com/"):
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Accept", "application/vnd.github+json")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8", errors="replace")
    return fetch


def report(results: list[Result]) -> str:
    lines = ["| Source | Pinned | Upstream | State |", "| --- | --- | --- | --- |"]
    for r in results:
        state = ("could not check: " + r.error) if r.error else ("outdated: " + r.summary if r.outdated else "current")
        lines.append(f"| {r.title} | {r.pinned} | {r.latest or '-'} | {state} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalog", default="catalog")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--dry-run", action="store_true", help="report only, write no issues")
    args = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN", "")

    results = check_all(Path(args.catalog), make_fetch(token))
    text = report(results)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Coverage freshness\n\n" + text + "\n")

    if args.dry_run or not args.repo:
        return 0
    api = f"https://api.github.com/repos/{args.repo}/issues"
    open_issues = [i for i in _github("GET", api + "?state=open&per_page=100", token) or []
                   if "pull_request" not in i]
    for action, number, payload in plan_issues(results, open_issues):
        if action == "create":
            made = _github("POST", api, token, payload)
            print(f"opened #{made['number']}: {payload['title']}")
        else:
            _github("PATCH", f"{api}/{number}", token, payload)
            print(f"updated #{number}: {payload['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
