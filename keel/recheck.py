"""`keel recheck REPORT --repo PATH`: are the lines a report quotes still where it saw them?

A report pins every `read` evidence entry to a commit, a path, a line range and a
verbatim quote. Months later the code has moved on, and a reassessment needs to know
where to look first. This answers that without a model: for each quote it reads the
file at the checkout's HEAD and says one of

* **in place** — the quoted lines are still inside the recorded range;
* **moved** — the same lines are elsewhere in the file (the new range is printed);
* **gone** — the file no longer has them, or the file itself is gone;
* **not checked** — there is no checkout for that repository, or git could not read it.

None of these says a finding still holds or was fixed. "Gone" follows a fix and a
refactor alike, and "in place" says nothing about the controls around the lines. The
list is where to look first, not a verdict.

`command` and `test` entries are listed with their command and never run. A report is
written by a model, and a command in it is text nobody has reviewed yet: a person runs
it, or puts it in CI where it goes through review like any other change.

Quotes are compared line by line with surrounding whitespace ignored, so re-indenting
code does not read as a change. git runs with an argument list, read-only (`show`).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from keel.schemas.org import OrgFile
from keel.schemas.report import Evidence, Report

IN_PLACE, MOVED, GONE, NOT_CHECKED, BY_HAND = "in place", "moved", "gone", "not checked", "run by hand"
_TIMEOUT = 15


def _lines(text: str) -> list[str]:
    out = [line.strip() for line in text.splitlines()]
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return out


def _matches(hay: list[str], needle: list[str]) -> list[int]:
    """1-based start lines where `needle` occurs in `hay` as consecutive lines."""
    n = len(needle)
    return [i + 1 for i in range(len(hay) - n + 1) if hay[i:i + n] == needle]


def _file_at_head(repo: Path, path: str) -> tuple[list[str] | None, str | None]:
    """The file's lines at HEAD; (None, reason) when it cannot be read."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "show", f"HEAD:{path}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git could not run: {e}"
    if proc.returncode == 0:
        return proc.stdout.splitlines(), None
    probe = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"],
        capture_output=True, text=True, timeout=_TIMEOUT,
    )
    if probe.returncode != 0:
        return None, f"{repo} is not a git checkout with a commit"
    return [], "file not found"


def check(ev: Evidence, repos: dict[str | None, Path]) -> dict:
    """One evidence entry's status, with where it was and, if moved, where it is now."""
    row = {"id": ev.id, "kind": ev.kind, "repo": ev.repo, "path": ev.path, "lines": ev.lines}
    if ev.kind != "read":
        return {**row, "status": BY_HAND, "command": ev.command}
    repo = repos.get(ev.repo)
    if repo is None:
        name = f'"{ev.repo}"' if ev.repo else "the default"
        return {**row, "status": NOT_CHECKED, "note": f"no --repo given for {name} repository"}
    file_lines, reason = _file_at_head(repo, ev.path or "")
    if file_lines is None:
        return {**row, "status": NOT_CHECKED, "note": reason}
    if reason:
        return {**row, "status": GONE, "note": reason}
    needle = _lines(ev.quote)
    if not needle:
        return {**row, "status": NOT_CHECKED, "note": "the quote is blank"}
    starts = _matches([line.strip() for line in file_lines], needle)
    first, _, last = (ev.lines or "").partition("-")
    lo, hi = int(first), int(last or first)
    if any(lo <= s and s + len(needle) - 1 <= hi for s in starts):
        return {**row, "status": IN_PLACE}
    if starts:
        now = [f"{s}-{s + len(needle) - 1}" if len(needle) > 1 else str(s) for s in starts]
        return {**row, "status": MOVED, "now": now}
    return {**row, "status": GONE, "note": "the quoted lines are not in the file"}


def recheck(report: Report | OrgFile, repos: dict[str | None, Path]) -> list[dict]:
    return [check(ev, repos) for ev in report.evidence]


def _parse_repos(values: list[str]) -> dict[str | None, Path]:
    """`PATH` is the checkout for evidence with no `repo`; `NAME=PATH` for a named one."""
    repos: dict[str | None, Path] = {}
    for value in values:
        name, sep, path = value.partition("=")
        if sep and name and not any(c in name for c in "/\\:"):
            repos[name] = Path(path)
        else:
            repos[None] = Path(value)
    return repos


def _describe(row: dict) -> str:
    where = f"{row['path']}:{row['lines']}" if row["kind"] == "read" else row.get("command") or ""
    if row.get("repo"):
        where = f"{row['repo']}: {where}"
    extra = ""
    if row["status"] == MOVED:
        extra = f"  -> now {', '.join(row['now'])}"
    elif row.get("note"):
        extra = f"  ({row['note']})"
    return f"  [{row['id']}] {row['status']:<11}  {where}{extra}"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="keel recheck",
        description="Say, for every line a report quotes, whether it is still where the "
        "report saw it. Reads each file at the checkout's HEAD; runs no command from the report.",
    )
    p.add_argument("report", help="the report file, e.g. reports/<system-id>/<date>.yaml, "
                   "or an org facts file, e.g. org/<name>.yaml")
    p.add_argument(
        "--repo", action="append", default=[], metavar="[NAME=]PATH",
        help="a checkout of the assessed code. PATH for evidence with no `repo`; "
        "NAME=PATH for evidence whose `repo` is NAME. Repeat for several repositories.",
    )
    return p


def main(argv: list[str]) -> None:
    args = parser().parse_args(argv)
    path = Path(args.report)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        # An org facts file (keel/schemas/org.py) pins its code the same way a report
        # does; it is told apart by its `facts`, which a report does not have.
        report = OrgFile(**data) if isinstance(data, dict) and "facts" in data else Report(**data)
    except (OSError, yaml.YAMLError, ValidationError, TypeError) as e:
        raise SystemExit(f"{path}: not a readable report or org facts file ({type(e).__name__}).") from None
    rows = recheck(report, _parse_repos(args.repo))
    print(f"{path}: {len(rows)} evidence entries, checked at HEAD")
    for row in rows:
        print(_describe(row))
    counts = {s: sum(r["status"] == s for r in rows) for s in (IN_PLACE, MOVED, GONE, NOT_CHECKED, BY_HAND)}
    print("  " + ", ".join(f"{n} {s}" for s, n in counts.items() if n))
    if counts[BY_HAND]:
        print("  Commands and tests are listed, never run: a person runs them, or CI after review.",
              file=sys.stderr)
