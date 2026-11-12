"""Read access to `org/`: facts an organisation keeps between assessments.

Read-only on purpose. People write these files; an assessment reads them and proposes
edits for a person to make. Like reports, they are read fresh off disk on every call,
and one broken file is listed as broken rather than failing the rest.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from keel.schemas.org import OrgFile
from keel.schemas.report import Report

DEFAULT_ORG_DIR = Path(__file__).resolve().parent.parent.parent / "org"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# How a report cites a stored fact: org:<file name without .yaml>#<fact id>.
REF_RE = re.compile(r"\borg:([a-z0-9]+(?:-[a-z0-9]+)*)#([a-z0-9]+(?:-[a-z0-9]+)*)")


def _org_dir() -> Path:
    """Honors `settings.org_dir` (env `ORG_DIR`); empty falls back to `org/`."""
    from keel.config import settings

    return Path(settings.org_dir) if settings.org_dir else DEFAULT_ORG_DIR


def load_file(path: Path) -> OrgFile:
    """Parse one org file; raises ValueError saying what is wrong with it."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ValueError(f"not readable YAML ({type(e).__name__})") from None
    if not isinstance(data, dict):
        raise ValueError("not a mapping")
    try:
        return OrgFile(**data)
    except ValidationError as e:
        raise ValueError("; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())) from None


def _files() -> tuple[dict[str, OrgFile], list[dict[str, str]]]:
    root = _org_dir()
    files: dict[str, OrgFile] = {}
    broken: list[dict[str, str]] = []
    if not root.is_dir():
        return files, broken
    for path in sorted(root.glob("*.yaml")):
        if not NAME_RE.match(path.stem):
            broken.append({"file": path.name, "error": "the name must be lowercase words joined by hyphens"})
            continue
        try:
            files[path.stem] = load_file(path)
        except ValueError as e:
            broken.append({"file": path.name, "error": str(e)})
    return files, broken


def list_facts() -> dict[str, Any]:
    """Every stored fact, compact: what an assessment needs to ask "still true?".

    `ref` is how a report cites it. Code evidence is counted here; the file has it in
    full, and `keel recheck` checks it."""
    files, broken = _files()
    facts = [
        {
            "ref": f"org:{name}#{fact.id}",
            "about": f"{org.title} ({org.kind})",
            "statement": fact.statement,
            "confirmed_by": fact.confirmed_by,
            "confirmed_on": fact.confirmed_on.isoformat(),
            "documents": fact.documents,
            "code_evidence": len(fact.evidence),
            "systems": fact.systems,
        }
        for name, org in files.items() for fact in org.facts
    ]
    out: dict[str, Any] = {"dir": str(_org_dir()), "facts": facts}
    if broken:
        out["broken"] = broken
    return out


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def unknown_refs(report: Report) -> list[str]:
    """Advice: an `org:<file>#<fact>` the report cites that no stored file holds.

    Advice and not a refusal, because the folder is private and a report opened on
    another machine may not have it. But a cited fact that resolves to nothing is either
    a typo or one the model made up, and a threat ruled out on it is ruled out on nothing.
    """
    refs = {ref for text in _strings(report.model_dump()) for ref in REF_RE.findall(text)}
    if not refs:
        return []
    files, _ = _files()
    out = []
    for name, fact_id in sorted(refs):
        org = files.get(name)
        if org is None or fact_id not in {f.id for f in org.facts}:
            out.append(
                f"org:{name}#{fact_id} is cited but no file in {_org_dir().name}/ holds it; "
                "cite a stored fact, or propose it as a new one"
            )
    return out
