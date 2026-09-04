"""Shared fixtures.

The important one is `catalog_dir`: a factory that writes a throwaway catalog under
`tmp_path`. Tests must state the content they are asserting on rather than reaching
into `catalog/` — a test bound to the real catalog stops testing its check and starts
locking the catalog's current state in place, so it fails the day the content is fixed.
"""
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_CATALOG = Path(__file__).resolve().parent.parent / "catalog"

# A card in `catalog/` is one somebody has vouched for, so the rules treat a card that
# does not say what it does as an error. The fixture therefore produces a complete card:
# a fixture that only passes because it is thin is not a catalog.
MITIGATION_DEFAULTS = {
    "mitigation_class": "gating_control",
    "purpose": "Stops the action leaving on model judgement alone.",
    "scope": "Every tool call that moves money or changes access.",
    "out_of_scope": "Reads that change nothing.",
    "control_mechanism": "A middleware between the model's decision and the tool call.",
    "locus": {"value": "infrastructure",
              "note": "The interception point is a property of the runtime."},
    "failure_behavior": {"value": "fail_closed",
                         "note": "Without an approval the call is refused."},
    "telemetry": {
        "events": [{"name": "decision.granted",
                    "records": "A person allowed this call.",
                    "attributes": ["call id", "authenticated identity"]}],
        "evidence": "Held where the producing system cannot rewrite it.",
    },
    "validation": [{"criterion": "A call without a recorded approval is refused.",
                    "test_scenario": "Replay a tool call with the approval removed."}],
}
THREAT_DEFAULTS = {
    "harm": "data-exposed",
    "reachability": "the model never sees anything worth taking",
}


@pytest.fixture
def catalog_dir(tmp_path):
    """Return `write(threats=[...], mitigations=[...]) -> Path`.

    Each record is a plain dict; the few fields every record needs but no test cares
    about are filled in, so a test only spells out what it is actually asserting on.
    A threat with no `weaknesses` gets one, since the schema requires at least one.
    """

    def write(threats=(), mitigations=(), style_guide=None):
        (tmp_path / "threats").mkdir(exist_ok=True)
        (tmp_path / "mitigations").mkdir(exist_ok=True)
        # A real catalog always has the four vocabulary files, and `validate_catalog`
        # requires them to match the schema's Literals. Copying them keeps the fixture
        # a real catalog rather than one that only passes because it is missing pieces.
        for stem in ("harm", "surface", "source", "components"):
            src = REPO_CATALOG / f"{stem}.yaml"
            if src.is_file():
                (tmp_path / f"{stem}.yaml").write_text(
                    src.read_text(encoding="utf-8"), encoding="utf-8"
                )

        for rec in mitigations:
            rec = {**MITIGATION_DEFAULTS, **rec}
            rec.setdefault("name", rec["id"])
            (tmp_path / "mitigations" / f"{rec['id']}.yaml").write_text(
                yaml.safe_dump(rec, sort_keys=False), encoding="utf-8"
            )

        for rec in threats:
            rec = {**THREAT_DEFAULTS, **rec}
            rec.setdefault("title", rec["id"])
            rec.setdefault("weaknesses", [{"component": "tool", "text": "no scoping on lookups"}])
            (tmp_path / "threats" / f"{rec['id']}.yaml").write_text(
                yaml.safe_dump(rec, sort_keys=False), encoding="utf-8"
            )

        if style_guide:
            (tmp_path / "style_guide").mkdir(exist_ok=True)
            for entity_type, fields in style_guide.items():
                (tmp_path / "style_guide" / f"{entity_type}.yaml").write_text(
                    yaml.safe_dump({"fields": fields}, sort_keys=False), encoding="utf-8"
                )

        return tmp_path

    return write


# --------------------------------------------------------------------------- #
# Git-backed catalog
# --------------------------------------------------------------------------- #
GIT_MISSING = shutil.which("git") is None


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def git_catalog(tmp_path):
    """A throwaway git repo containing a catalog with two commits of real history.

    The history endpoints used to be tested against this repo's own `catalog/`, which
    tied them to specific entry ids and broke the moment a file was moved. Everything
    they need — a tracked file, more than one commit, a commit touching a mitigation —
    is cheap to build here instead.

    Yields the catalog directory (already installed as the process-wide store).
    """
    from keel.store import Store, set_store

    repo = tmp_path / "repo"
    catalog = repo / "catalog"
    (catalog / "threats").mkdir(parents=True)
    (catalog / "mitigations").mkdir(parents=True)

    _git(repo.parent, "init", "-q", "repo")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test Author")

    threat = {
        "id": "T-FIXTURE",
        "title": "Fixture threat",
        "harm": "data-exposed",
        "weaknesses": [{"component": "tool", "text": "no scoping on lookups"}],
        "reachability": "the model never sees anything worth taking",
    }
    mitigation = {"id": "CTRL-FIXTURE", "name": "Fixture control", "mitigation_class": "gating_control"}
    threat_path = catalog / "threats" / "T-FIXTURE.yaml"
    threat_path.write_text(yaml.safe_dump(threat, sort_keys=False), encoding="utf-8")
    (catalog / "mitigations" / "CTRL-FIXTURE.yaml").write_text(
        yaml.safe_dump(mitigation, sort_keys=False), encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat(catalog): the fixture threat and its control")

    threat["title"] = "Fixture threat, retitled"
    threat_path.write_text(yaml.safe_dump(threat, sort_keys=False), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fix(catalog): a clearer title")

    set_store(Store(catalog))
    try:
        yield catalog
    finally:
        set_store(None)
