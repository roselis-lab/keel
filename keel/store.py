"""In-memory, file-backed catalog store.

`catalog/*.yaml` is the single source of truth. The store loads it into memory on
startup and every write patches the affected YAML file directly — there is no
database. Reads are served from memory; writes update memory and the file together.
This is what lets Keel start with zero setup and stay git-native: an edit is a file
diff, whether it came from the UI, an MCP tool, or a text editor.
"""
from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"

# A file name, and nothing that could be read as a path.
_STEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# Windows resolves these as devices whatever the extension, and git checkouts of a repo
# containing them fail on Windows entirely. A catalog is a git repository people clone,
# so a name that cannot exist on a common platform is not a usable id anywhere.
_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

# NAME_MAX is 255 on ext4 and APFS; the id also has ".yaml" appended and sits inside a
# path, so leave room. An id this long is a mistake regardless.
_MAX_STEM = 100


def is_safe_stem(stem: str) -> str | None:
    """None if `stem` is usable as a file name, else why it is not.

    One rule with two callers, on purpose: the schema asks so it can refuse an id in a
    sentence the author can act on, and the store asks so that a gap in the schema
    cannot become a write it did not intend. Stating it twice is how the two drift.
    """
    if not stem or not _STEM_RE.match(stem):
        return "use letters, digits, dot, hyphen and underscore, starting with a letter or digit"
    if len(stem) > _MAX_STEM:
        return f"at most {_MAX_STEM} characters"
    if stem[-1] in ". ":
        return "cannot end in a dot or a space - Windows silently strips them"
    if stem.split(".")[0].lower() in _RESERVED:
        return f"{stem.split('.')[0]!r} is a reserved device name on Windows"
    return None


def resolve_catalog_dir() -> Path:
    """The catalog directory in force: `settings.catalog_dir` (env `CATALOG_DIR`) or the
    repo's own `catalog/`. Every reader must go through this — when the CLI resolved the
    path differently from the server, `keel validate` could pass on a catalog nobody was
    serving."""
    from keel.config import settings

    return Path(settings.catalog_dir) if settings.catalog_dir else DEFAULT_CATALOG_DIR


def dump_yaml(data: Any) -> str:
    # width kept effectively unlimited so prose values stay one line per value
    # (clean diffs) instead of being hard-wrapped at ~80 columns.
    return yaml.dump(
        data, allow_unicode=True, default_flow_style=False, sort_keys=False, width=1_000_000
    )


# Stable on-disk field order, so files stay diffable regardless of write path.
THREAT_ORDER = [
    "id", "title", "harm", "source", "weaknesses", "reachability",
    "mitigations", "references", "positioning", "tags",
]
MITIGATION_ORDER = [
    "id", "name", "mitigation_class", "purpose", "formal_implementation_risk",
    "review", "maintainer", "locus", "scope", "out_of_scope", "control_mechanism",
    "failure_behavior", "telemetry", "anti_patterns", "validation", "faq",
    "positioning", "requires", "implementations",
]


def _ordered(rec: dict[str, Any], order: list[str]) -> dict[str, Any]:
    out = {k: rec[k] for k in order if k in rec}
    for k, v in rec.items():  # keep any unexpected extras rather than dropping them
        if k not in out:
            out[k] = v
    return out


def _model_for(name: str):
    """The schema a record of this kind must satisfy. Imported lazily so `keel.store`
    stays importable from the schema modules."""
    from keel.schemas.mitigation import MitigationCreate
    from keel.schemas.threat import Threat

    return {"threats": Threat, "mitigations": MitigationCreate}[name]


_SINGULAR = {"threats": "threat", "mitigations": "mitigation"}


class Store:
    """Loads the catalog into memory and writes changes straight back to YAML.

    Loading is a gate, not a copy. A file that does not satisfy its schema never enters
    the working set — it lands in `problems` instead, with the file, the field and the
    reason. Every write path already validates, so the only way to produce a bad record
    is to hand-edit YAML or pull someone else's; before this gate those records loaded
    silently and the app served them, and `keel validate` only found out when a person
    happened to run it.
    """

    def __init__(self, catalog_dir: Path | str = DEFAULT_CATALOG_DIR) -> None:
        self.dir = Path(catalog_dir)
        self.lock = threading.RLock()
        self.threats: dict[str, dict[str, Any]] = {}
        self.mitigations: dict[str, dict[str, Any]] = {}
        self.style_guide: dict[str, dict[str, dict[str, Any]]] = {}
        # Guidance about the record as a whole, keyed by entity type. Kept beside
        # `style_guide` rather than inside it so a field name can never collide with it.
        self.style_guide_entity: dict[str, dict[str, Any]] = {}
        self.vocabulary: dict[str, dict[str, Any]] = {}
        self.problems: list[dict[str, Any]] = []
        self.reload()

    # -- loading ------------------------------------------------------------
    def reload(self) -> None:
        self.problems = []
        self.threats = self._load_records("threats")
        self.mitigations = self._load_records("mitigations")
        self.style_guide = {}
        self.style_guide_entity = {}
        sg = self.dir / "style_guide"
        if sg.is_dir():
            for path in sorted(sg.glob("*.yaml")):
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if not isinstance(data, dict) or not isinstance(data.get("fields"), dict):
                    self._problem(
                        f"style_guide/{path.name}", None, None, "fields",
                        "expected a mapping with a 'fields' mapping", dropped=True,
                    )
                    continue
                self.style_guide[path.stem] = data["fields"]
                entity = data.get("entity")
                if entity is not None and not isinstance(entity, dict):
                    self._problem(
                        f"style_guide/{path.name}", None, None, "entity",
                        "expected a mapping", dropped=False,
                    )
                    entity = None
                self.style_guide_entity[path.stem] = entity or {}

        from keel.vocabulary import load_vocabularies, vocabulary_errors

        self.vocabulary = load_vocabularies(self.dir)
        for msg in vocabulary_errors(self.dir):
            file, _, rest = msg.partition(": ")
            self._problem(file, None, None, None, rest, dropped=False)

    # Cross-record integrity is deliberately NOT checked here. The store's question is
    # whether a record can be loaded at all, which one record can answer about itself.
    # Whether its links resolve is a question about the catalog, and it is answered once,
    # by the rules - reporting it in both places gave the dashboard the same defect twice
    # at two different severities.

    def _problem(
        self, file: str, entity_type: str | None, entity_id: str | None,
        field: str | None, message: str, *, dropped: bool,
    ) -> None:
        """Record one hard defect. `dropped` says whether the record was kept out of the
        working set — a whole-record failure is dropped, one bad link is not."""
        self.problems.append({
            "file": file,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "message": message,
            "dropped": dropped,
        })

    def _load_records(self, name: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        directory = self.dir / name
        if not directory.is_dir():
            return out
        model = _model_for(name)
        singular = _SINGULAR[name]

        for path in sorted(directory.glob("*.yaml")):
            rel = f"{name}/{path.name}"
            try:
                rec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as e:
                self._problem(rel, singular, None, None, f"not readable as YAML: {e}", dropped=True)
                continue
            if not isinstance(rec, dict):
                self._problem(rel, singular, None, None, "not a YAML mapping", dropped=True)
                continue

            rid = rec.get("id")
            if not rid:
                self._problem(rel, singular, None, "id", "missing `id`", dropped=True)
                continue
            if rid != path.stem:
                self._problem(
                    rel, singular, rid, "id",
                    f"id {rid!r} does not match filename {path.stem!r}", dropped=True,
                )
                continue
            if rid in out:
                self._problem(rel, singular, rid, "id", f"duplicate id {rid!r}", dropped=True)
                continue

            try:
                model(**rec)
            except ValidationError as e:
                for err in e.errors():
                    field = ".".join(str(x) for x in err["loc"]) or None
                    self._problem(rel, singular, rid, field, err["msg"], dropped=True)
                continue

            out[rid] = rec
        return out

    def _path(self, subdir: str, stem: str) -> Path:
        """The one place a caller-supplied name becomes a path.

        Every id here arrives from outside - an MCP argument, a URL segment, a YAML
        file - and `dir / f"{stem}.yaml"` happily accepts `../../elsewhere`. Ids were
        pattern-checked by the schema, but a check the caller has to remember is a check
        that gets forgotten by the next code path, and the blast radius is writing any
        file on the machine.

        So the component that owns the filesystem refuses to leave its own directory,
        whatever it is asked. The schema still rejects a bad id with a useful message;
        this exists so that a bug there cannot become an arbitrary write.
        """
        problem = is_safe_stem(stem)
        if problem:
            raise ValueError(f"{stem!r} is not a usable file name: {problem}")
        directory = (self.dir / subdir).resolve()
        path = (directory / f"{stem}.yaml").resolve()
        if path.parent != directory:
            raise ValueError(f"{stem!r} would write outside {subdir}/")
        return path

    def write_threat(self, threat_id: str) -> None:
        path = self._path("threats", threat_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = _ordered(self.threats[threat_id], THREAT_ORDER)
        path.write_text(dump_yaml(rec), encoding="utf-8")

    def write_mitigation(self, mitigation_id: str) -> None:
        path = self._path("mitigations", mitigation_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = _ordered(self.mitigations[mitigation_id], MITIGATION_ORDER)
        path.write_text(dump_yaml(rec), encoding="utf-8")

    def write_style(self, entity_type: str) -> None:
        path = self._path("style_guide", entity_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {}
        entity = self.style_guide_entity.get(entity_type)
        if entity:
            payload["entity"] = entity          # the record first, then its parts
        payload["fields"] = self.style_guide.get(entity_type, {})
        path.write_text(dump_yaml(payload), encoding="utf-8")

    def write_coverage(self, source_id: str, payload: dict[str, Any]) -> None:
        path = self._path("coverage", source_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_yaml(payload), encoding="utf-8")

    def coverage_path(self, source_id: str) -> Path:
        """Guarded read path, so the matrix cannot be pointed at a file elsewhere."""
        return self._path("coverage", source_id)

    def delete_threat_file(self, threat_id: str) -> None:
        self._path("threats", threat_id).unlink(missing_ok=True)

    def delete_mitigation_file(self, mitigation_id: str) -> None:
        self._path("mitigations", mitigation_id).unlink(missing_ok=True)


_store: Store | None = None


def get_store() -> Store:
    """Return the process-wide store, loading the catalog on first access.

    Honors `settings.catalog_dir` (env `CATALOG_DIR`) so the app can run against a
    throwaway copy of the catalog; empty falls back to the repo's own `catalog/`.
    """
    global _store
    if _store is None:
        _store = Store(resolve_catalog_dir())
    return _store


def set_store(store: Store | None) -> None:
    """Replace the process-wide store (used by tests to point at a temp catalog)."""
    global _store
    _store = store
