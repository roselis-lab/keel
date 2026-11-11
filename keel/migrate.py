"""`keel reports migrate --extension NAME`: carry fields Keel does not know into an
extension's section.

A report written while an extension was part of Keel holds fields the schema no longer
has, so it does not open. This moves every such field into `extensions[NAME]`, where
Keel keeps it without reading it and the extension finds it:

    extensions:
      NAME:
        <report field>: ...                      # on the report, by its own name
        findings:     {"<finding id>": {<field>: ...}}
        requirements: {"<finding id>/<index>": {<field>: ...}}

`--diagrams DIR` also takes `DIR/<system>/<date>.yaml` as that report's
`extensions[NAME].system_diagram`, unless the report has one already.

Nothing is dropped. A field that is both on the report and already in the section with a
different value stops that report, and it is named in the output. Each report is checked
the way a save checks it before it is written, so one that would come out invalid stays
as it is and is named too. The catalog lookup is left out: an archived report naming a
control renamed since is carried over, not stopped. Status does not change, because
moving data is not an edit of the assessment. Running it again changes nothing.
"""
from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path
from typing import Any, Callable

import yaml

from keel.errors import KeelError
from keel.schemas.report import Finding, Report, Requirement
from keel.services import report_service

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REPORT_FIELDS = frozenset(Report.model_fields)
FINDING_FIELDS = frozenset(Finding.model_fields)
REQUIREMENT_FIELDS = frozenset(Requirement.model_fields)


class Refused(Exception):
    """This report cannot be carried over as it is. The message says why."""


def _mapping(holder: dict[str, Any], key: str, where: str) -> dict[str, Any]:
    value = holder.setdefault(key, {})
    if not isinstance(value, dict):
        raise Refused(f"{where} is not a mapping")
    return value


def carry(raw: dict[str, Any], name: str, diagram: Any = None) -> tuple[dict[str, Any], list[str]]:
    """The report with every unknown field moved into `extensions[name]`, and what moved.
    `raw` is left as it is. Raises Refused when a move would overwrite something."""
    data = copy.deepcopy(raw)
    exts = data.get("extensions")
    exts = {} if exts is None else exts
    if not isinstance(exts, dict):
        raise Refused("extensions is not a mapping")
    section = exts.get(name)
    section = {} if section is None else section
    if not isinstance(section, dict):
        raise Refused(f"extensions.{name} is not a mapping")
    moved: list[str] = []

    def put(holder: dict[str, Any], key: str, value: Any, label: str) -> None:
        if key in holder and holder[key] != value:
            raise Refused(f"{label} is on the report and in extensions.{name} with another value")
        holder[key] = value
        moved.append(label)

    for key in [k for k in data if k not in REPORT_FIELDS]:
        put(section, key, data.pop(key), key)

    findings = data.get("findings")
    for f in findings if isinstance(findings, list) else []:
        if not isinstance(f, dict):
            continue
        fid = f.get("id")
        extra = [k for k in f if k not in FINDING_FIELDS]
        reqs = f.get("requirements")
        reqs = reqs if isinstance(reqs, list) else []
        req_extra = [(i, r, [k for k in r if k not in REQUIREMENT_FIELDS])
                     for i, r in enumerate(reqs) if isinstance(r, dict)]
        if (extra or any(ks for _, _, ks in req_extra)) and not isinstance(fid, str):
            raise Refused("a finding without an id carries fields to move, so they have no key")
        if extra:
            entry = _mapping(_mapping(section, "findings", f"extensions.{name}.findings"),
                             fid, f"extensions.{name}.findings.{fid}")
            for k in extra:
                put(entry, k, f.pop(k), f"findings[{fid}].{k}")
        for i, r, keys in req_extra:
            if not keys:
                continue
            key = f"{fid}/{i}"
            entry = _mapping(_mapping(section, "requirements", f"extensions.{name}.requirements"),
                             key, f"extensions.{name}.requirements.{key}")
            for k in keys:
                put(entry, k, r.pop(k), f"requirements[{key}].{k}")

    if diagram is not None and "system_diagram" not in section:
        section["system_diagram"] = diagram
        moved.append("system_diagram from the diagrams folder")

    if moved:
        exts[name] = section
        data["extensions"] = exts
    return data, moved


def _diagrams(folder: Path | None, say: Callable[[str], None]) -> dict[tuple[str, str], Any]:
    """`{(system, date): diagram}` from `folder/<system>/<date>.yaml`."""
    out: dict[tuple[str, str], Any] = {}
    if folder is None:
        return out
    for path in sorted(folder.glob("*/*.yaml")):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            say(f"skipped diagram {path}: does not read ({type(e).__name__})")
            continue
        if value is None:
            say(f"skipped diagram {path}: the file is empty")
            continue
        out[(path.parent.name, path.stem)] = value
    return out


def migrate(name: str, diagrams: Path | None = None, *, dry_run: bool = False,
            say: Callable[[str], None] = print) -> int:
    """Run over every report in the reports folder. 0 when every report that needed it was
    carried over, 1 when any was not."""
    if not NAME_RE.match(name):
        say(f"{name!r} is not an extension name: letters, digits, '.', '_' and '-'")
        return 2
    if diagrams is not None and not diagrams.is_dir():
        say(f"no diagrams folder at {diagrams}")
        return 2
    root = report_service._reports_dir()
    if not root.is_dir():
        say(f"no reports folder at {root}")
        return 1

    pending = _diagrams(diagrams, say)
    verb = "would migrate" if dry_run else "migrated"
    changed = refused = 0
    for path in sorted(root.glob("*/*.yaml")):
        system_id, date = path.parent.name, path.stem
        label = f"{system_id}/{date}"
        diagram = pending.pop((system_id, date), None)
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise Refused("the file is not a report")
            data, moved = carry(raw, name, diagram)
            if not moved:
                continue
            report = report_service.checked(system_id, date, data, catalog=False)
        except (OSError, yaml.YAMLError) as e:
            refused += 1
            say(f"not migrated {label}: does not read ({type(e).__name__})")
            continue
        except Refused as e:
            refused += 1
            say(f"not migrated {label}: {e}")
            continue
        except KeelError as e:
            refused += 1
            why = "; ".join(d.get("message", "") for d in e.details[:3])
            say(f"not migrated {label}: {e.message}" + (f" ({why})" if why and why != e.message else ""))
            continue
        if not dry_run:
            report_service._write(path, report)
        changed += 1
        say(f"{verb} {label}: {', '.join(moved)}")

    for system_id, date in sorted(pending):
        say(f"skipped diagram {system_id}/{date}: no such report")
    say(f"{changed} report{'' if changed == 1 else 's'} "
        f"{'would change' if dry_run else 'changed'}, {refused} not migrated")
    return 1 if refused else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="keel reports", description="Work on the reports folder.")
    sub = p.add_subparsers(dest="command", required=True)
    m = sub.add_parser(
        "migrate",
        help="move fields Keel does not know into an extension's section",
        description="Move every field the report schema does not know, on a report, a "
        "finding or a requirement, into extensions[NAME]. Safe to run twice.",
    )
    m.add_argument("--extension", required=True, metavar="NAME", help="the extension's name")
    m.add_argument("--diagrams", metavar="DIR", type=Path,
                   help="a folder of <system>/<date>.yaml diagrams to add as system_diagram")
    m.add_argument("--dry-run", action="store_true", help="say what would change; write nothing")
    return p


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv)
    return migrate(args.extension, args.diagrams, dry_run=args.dry_run)
