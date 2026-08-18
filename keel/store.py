"""In-memory, file-backed catalog store.

`catalog/*.yaml` is the single source of truth. The store loads it into memory on
startup and every write patches the affected YAML file directly — there is no
database. Reads are served from memory; writes update memory and the file together.
This is what lets Keel start with zero setup and stay git-native: an edit is a file
diff, whether it came from the UI, an MCP tool, or a text editor.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


def dump_yaml(data: Any) -> str:
    # width kept effectively unlimited so prose values stay one line per value
    # (clean diffs) instead of being hard-wrapped at ~80 columns.
    return yaml.dump(
        data, allow_unicode=True, default_flow_style=False, sort_keys=False, width=1_000_000
    )


# Stable on-disk field order, so files stay diffable regardless of write path.
THREAT_ORDER = [
    "id", "title", "harm", "surface", "source", "weaknesses", "reachability",
    "mitigations", "references", "tags",
]
MITIGATION_ORDER = [
    "id", "name", "status", "mitigation_class", "purpose", "formal_implementation_risk",
    "review", "maintainer", "owner", "locus", "scope", "control_mechanism",
    "failure_behavior", "telemetry", "anti_patterns", "validation", "faq",
]


def _ordered(rec: dict[str, Any], order: list[str]) -> dict[str, Any]:
    out = {k: rec[k] for k in order if k in rec}
    for k, v in rec.items():  # keep any unexpected extras rather than dropping them
        if k not in out:
            out[k] = v
    return out


class Store:
    """Loads the catalog into memory and writes changes straight back to YAML."""

    def __init__(self, catalog_dir: Path | str = DEFAULT_CATALOG_DIR) -> None:
        self.dir = Path(catalog_dir)
        self.lock = threading.RLock()
        self.threats: dict[str, dict[str, Any]] = {}
        self.mitigations: dict[str, dict[str, Any]] = {}
        self.style_guide: dict[str, dict[str, dict[str, Any]]] = {}
        self.reload()

    # -- loading ------------------------------------------------------------
    def reload(self) -> None:
        self.threats = self._load_records("threats")
        self.mitigations = self._load_records("mitigations")
        self.style_guide = {}
        sg = self.dir / "style_guide"
        if sg.is_dir():
            for path in sorted(sg.glob("*.yaml")):
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                self.style_guide[path.stem] = data.get("fields") or {}

    def _load_records(self, name: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        directory = self.dir / name
        if directory.is_dir():
            for path in sorted(directory.glob("*.yaml")):
                rec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if rec.get("id"):
                    out[rec["id"]] = rec
        return out

    # -- persistence --------------------------------------------------------
    def write_threat(self, threat_id: str) -> None:
        directory = self.dir / "threats"
        directory.mkdir(parents=True, exist_ok=True)
        rec = _ordered(self.threats[threat_id], THREAT_ORDER)
        (directory / f"{threat_id}.yaml").write_text(dump_yaml(rec), encoding="utf-8")

    def write_mitigation(self, mitigation_id: str) -> None:
        directory = self.dir / "mitigations"
        directory.mkdir(parents=True, exist_ok=True)
        rec = _ordered(self.mitigations[mitigation_id], MITIGATION_ORDER)
        (directory / f"{mitigation_id}.yaml").write_text(dump_yaml(rec), encoding="utf-8")

    def write_style(self, entity_type: str) -> None:
        directory = self.dir / "style_guide"
        directory.mkdir(parents=True, exist_ok=True)
        payload = {"fields": self.style_guide.get(entity_type, {})}
        (directory / f"{entity_type}.yaml").write_text(dump_yaml(payload), encoding="utf-8")

    def delete_threat_file(self, threat_id: str) -> None:
        (self.dir / "threats" / f"{threat_id}.yaml").unlink(missing_ok=True)

    def delete_mitigation_file(self, mitigation_id: str) -> None:
        (self.dir / "mitigations" / f"{mitigation_id}.yaml").unlink(missing_ok=True)


_store: Store | None = None


def get_store() -> Store:
    """Return the process-wide store, loading the catalog on first access."""
    global _store
    if _store is None:
        _store = Store()
    return _store


def set_store(store: Store | None) -> None:
    """Replace the process-wide store (used by tests to point at a temp catalog)."""
    global _store
    _store = store
