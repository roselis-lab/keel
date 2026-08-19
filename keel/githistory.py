"""Read-only Git history for catalog entries.

Shells out to `git` for one YAML file at a time so the product can show a
per-entry commit list and per-commit diff. Everything here is read-only: it runs
only `rev-parse`, `log`, and `show`, always with an argument LIST (never
`shell=True`), so untrusted `entity`/`id`/`sha` values can never reach a shell.

It degrades gracefully. When the catalog is not inside a git repo (for example a
throwaway `CATALOG_DIR` copy), when `git` is missing, or when a command fails,
history reports `{"available": False, ...}` and diffs return `None` — nothing
raises to the caller.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from keel.store import get_store

# `git log --format` / `git show --format` fields joined by the unit separator
# (\x1f, %x1f), which cannot appear in the values, so parsing stays unambiguous.
_FORMAT = "%h%x1f%an%x1f%aI%x1f%s"
_US = "\x1f"

# Allowlists — validated before any subprocess call, so bad input never shells out.
_ENTITIES = {"threats", "mitigations"}
_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")

_TIMEOUT = 15


def _run(args: list[str]) -> subprocess.CompletedProcess | None:
    """Run a git command read-only. Return None on any failure (missing git,
    non-zero exit, timeout) rather than raising."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc


def is_valid_ref(entity: str, id: str) -> bool:
    """True if `entity` is on the allowlist and `id` matches the safe pattern.

    Lets the route distinguish a rejected reference (→ 404) from a valid entry that
    simply has no tracked history (→ 200 with `available: False`).
    """
    return entity in _ENTITIES and bool(_ID_RE.match(id))


def _resolve(entity: str, id: str) -> tuple[str, str] | None:
    """Validate input and locate the file inside its git repo.

    Returns `(repo_root, relpath)` where `relpath` is the file's path relative to
    the repo root (forward slashes, git's native form), or None if the entity/id
    is rejected, the catalog is not a git repo, or the file is absent.
    """
    if entity not in _ENTITIES or not _ID_RE.match(id):
        return None

    catalog_dir = get_store().dir
    file_path = Path(catalog_dir) / entity / f"{id}.yaml"
    if not file_path.is_file():
        return None

    proc = _run(["git", "-C", str(catalog_dir), "rev-parse", "--show-toplevel"])
    if proc is None:
        return None
    repo_root = proc.stdout.strip()
    if not repo_root:
        return None

    try:
        relpath = file_path.resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return None
    return repo_root, relpath.as_posix()


def _parse_meta(line: str) -> dict[str, str]:
    sha, author, date, message = (line.split(_US, 3) + ["", "", "", ""])[:4]
    return {"sha": sha, "author": author, "date": date, "message": message}


def history(entity: str, id: str) -> dict:
    """Commit list for one catalog entry's YAML file.

    Unavailable (bad input, not a git repo, git missing, or the file is
    untracked/absent) → `{"available": False, "commits": []}`. Otherwise
    `{"available": True, "file": <repo-relative path>, "commits": [...]}` where each
    commit is `{"sha", "author", "date", "message"}`, newest first. Handles shallow
    clones (may show only one commit); no minimum count is assumed.
    """
    resolved = _resolve(entity, id)
    if resolved is None:
        return {"available": False, "commits": []}
    repo_root, relpath = resolved

    proc = _run(
        ["git", "-C", repo_root, "log", "--follow", f"--format={_FORMAT}", "--", relpath]
    )
    if proc is None:
        return {"available": False, "commits": []}

    commits = [_parse_meta(line) for line in proc.stdout.splitlines() if line.strip()]
    if not commits:  # tracked path with history is expected; empty ⇒ untracked
        return {"available": False, "commits": []}
    return {"available": True, "file": relpath, "commits": commits}


def diff(entity: str, id: str, sha: str) -> dict | None:
    """Unified diff for one commit, scoped to the entry's YAML file.

    Returns `{"sha", "author", "date", "message", "diff"}`, or None if the input is
    rejected (bad entity/id/sha), the catalog is not a git repo, or the commit is
    not found. The `sha` is pattern-checked before any git call, so it can never
    reach a shell.
    """
    if not _SHA_RE.match(sha):
        return None
    resolved = _resolve(entity, id)
    if resolved is None:
        return None
    repo_root, relpath = resolved

    proc = _run(
        ["git", "-C", repo_root, "show", sha, f"--format={_FORMAT}", "--patch", "--", relpath]
    )
    if proc is None:
        return None

    out = proc.stdout
    if not out:
        return None
    # `git show --format=<fmt> --patch` prints the formatted meta line first, then
    # the unified diff for the scoped file.
    meta_line, _, patch = out.partition("\n")
    result = _parse_meta(meta_line)
    result["diff"] = patch
    return result
