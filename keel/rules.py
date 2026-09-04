"""Every catalog rule, defined once and run from two entry points.

The checks used to live in five functions across four modules. Over-graded link strength
was computed twice, referential integrity three times, and "this record is missing
something" was split between two of them so that a threat with no weaknesses was reported
by the dashboard but not by the write that caused it. Adding `requires` nearly made it a
sixth place.

The shape here is the ordinary linter one - a registry of self-describing rules and an
engine that runs them (ESLint, Biome, Bicep, SQLMesh all do this). Three properties
matter and are the reason it works:

* **Rules are pure.** A rule receives records and returns findings. No filesystem, no
  store lookups of its own, nothing async. That is what lets the same rule run against
  one entity after a write and against the whole catalog in `keel validate`.
* **The registry populates itself.** A rule is registered by defining it. A hand-kept
  list is how a rule silently misses one of the entry points.
* **Severity belongs to the rule, not to the caller.** Otherwise each entry point grows
  its own table of what is serious, and they drift.

What is NOT here: anything about the wording of a field. Whether a `purpose` restates the
name is semantics, it cannot be decided mechanically, and it is the style guide's job and
the review skill's - not a rule that would only ever guess.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Literal

Severity = Literal["error", "advice"]
EntityKind = Literal["threat", "mitigation", "catalog"]


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    entity_type: str | None
    entity_id: str | None
    message: str
    field: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out = {"code": self.code, "severity": self.severity, "message": self.message}
        for key, value in (("entity_type", self.entity_type),
                           ("entity_id", self.entity_id),
                           ("field", self.field)):
            if value:
                out[key] = value
        return out


@dataclass
class Catalog:
    """Everything a rule is allowed to see. Passed in, never fetched, so a rule stays
    pure and testable without a store on disk."""

    threats: dict[str, dict[str, Any]] = field(default_factory=dict)
    mitigations: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage: list[Any] = field(default_factory=list)

    @classmethod
    def from_store(cls, store: Any, coverage: list[Any] | None = None) -> "Catalog":
        return cls(threats=store.threats, mitigations=store.mitigations,
                   coverage=coverage if coverage is not None else [])


RuleFn = Callable[[str, dict[str, Any], Catalog], Iterable[Finding]]


@dataclass(frozen=True)
class Rule:
    entity: EntityKind
    severity: Severity
    label: str
    fn: RuleFn


REGISTRY: dict[str, Rule] = {}


def rule(code: str, *, entity: EntityKind, severity: Severity,
         label: str) -> Callable[[RuleFn], RuleFn]:
    """Define a rule. Defining it registers it - there is no list to remember to update.

    `entity` is what the rule is handed: one threat, one mitigation, or the whole catalog
    for the few questions only answerable across records. `label` is how the finding is
    grouped in a UI; it lives here so that a screen cannot carry its own copy of the rule
    list and fall behind it.
    """
    def decorate(fn: RuleFn) -> RuleFn:
        if code in REGISTRY:
            raise ValueError(f"duplicate rule code {code!r}")
        REGISTRY[code] = Rule(entity, severity, label, fn)
        return fn
    return decorate


def catalogue() -> list[dict[str, str]]:
    """Every rule, for a caller that needs to group or explain findings."""
    return [{"code": c, "entity": r.entity, "severity": r.severity, "label": r.label,
             "explanation": ((r.fn.__doc__ or "").strip().splitlines() or [""])[0]}
            for c, r in sorted(REGISTRY.items())]


# --------------------------------------------------------------------------- #
# Threats
# --------------------------------------------------------------------------- #
@rule("threat_incomplete", entity="threat", severity="error", label="Incomplete threat")
def _threat_incomplete(tid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A threat with no weakness names no condition to fix, and one with no harm names no
    consequence. Either way there is nothing to assess."""
    for name in ("harm", "reachability"):
        if not (rec.get(name) or "").strip():
            yield Finding("threat_incomplete", "error", "threat", tid,
                          f"no {name}", field=name)
    if not (rec.get("weaknesses") or []):
        yield Finding("threat_incomplete", "error", "threat", tid,
                      "no weaknesses: nothing names the condition that makes this possible",
                      field="weaknesses")


@rule("dangling_link", entity="threat", severity="error", label="Link to a control that is not there")
def _dangling_link(tid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    for i, link in enumerate(rec.get("mitigations") or []):
        if isinstance(link, dict) and link.get("id") not in cat.mitigations:
            yield Finding("dangling_link", "error", "threat", tid,
                          f"links {link.get('id')!r}, which is not in the catalog",
                          field=f"mitigations.{i}.id")


@rule("over_graded_strength", entity="threat", severity="advice", label="Over-graded link")
def _over_graded(tid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A detector or a process does not architecturally block, so it cannot back a
    `gating` link. Advice rather than an error: the grade is a judgment, and an author
    may be mid-way through re-classing the control."""
    for i, link in enumerate(rec.get("mitigations") or []):
        if not isinstance(link, dict) or link.get("strength") != "gating":
            continue
        target = cat.mitigations.get(link.get("id"))
        cls = (target or {}).get("mitigation_class")
        if target is not None and cls and cls != "gating_control":
            yield Finding("over_graded_strength", "advice", "threat", tid,
                          f"{link['id']} is a {cls}, so it should not back a gating link",
                          field=f"mitigations.{i}.strength")


@rule("no_gating_control", entity="threat", severity="advice", label="Nothing closes the threat")
def _no_gating(tid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    links = rec.get("mitigations") or []
    if links and not any(link.get("strength") == "gating" for link in links):
        yield Finding("no_gating_control", "advice", "threat", tid,
                      "every linked control is soft, so nothing closes this threat",
                      field="mitigations")


@rule("missing_references", entity="threat", severity="advice", label="No references")
def _missing_references(tid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    if not (rec.get("references") or []):
        yield Finding("missing_references", "advice", "threat", tid,
                      "no references: nothing recorded shows this threat is real",
                      field="references")


# --------------------------------------------------------------------------- #
# Mitigations
# --------------------------------------------------------------------------- #
# What a card has to say to be a card. `mitigation_class` announces how the next two are
# read, so a class without them announces nothing.
CARD_FIELDS = ("purpose", "scope", "out_of_scope", "control_mechanism")


@rule("card_incomplete", entity="mitigation", severity="advice", label="Incomplete card")
def _card_incomplete(mid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """Advice, not an error, because an unfinished card is not a broken one.

    An error means the record cannot be served: it failed its schema, or it names
    something that is not there. A card missing `locus` parses, resolves and answers
    every question it does answer - it is simply not done. Filing that as an error made
    `keel validate` refuse a whole catalog for content that was merely unwritten, which
    turned the CI gate into something you route around instead of fix. The count belongs
    in the advisory tier, where the health view can say how much of the library is
    finished and which field each card is waiting on."""
    for name in CARD_FIELDS:
        if not (rec.get(name) or "").strip():
            yield Finding("card_incomplete", "advice", "mitigation", mid,
                          f"no {name}", field=name)
    # A decision recorded without its reasoning is a label. The schema refuses one built
    # by hand; this catches a card that never got the field at all.
    for name in ("locus", "failure_behavior"):
        if not (rec.get(name) or {}):
            yield Finding("card_incomplete", "advice", "mitigation", mid,
                          f"no {name}", field=name)


@rule("no_acceptance_criteria", entity="mitigation", severity="advice", label="No acceptance criteria")
def _no_validation(mid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    if not (rec.get("validation") or []):
        yield Finding("no_acceptance_criteria", "advice", "mitigation", mid,
                      "no validation: a control nobody can check is a recommendation",
                      field="validation")


@rule("unchecked_anti_patterns", entity="mitigation", severity="advice",
      label="Anti-patterns nothing checks")
def _unchecked_anti_patterns(mid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """Anti-patterns and acceptance criteria stay separate fields on purpose - one is read
    while designing, the other while accepting - but a list of ways to get it wrong with
    nothing that would catch any of them is a warning nobody can act on."""
    if (rec.get("anti_patterns") or []) and not (rec.get("validation") or []):
        yield Finding("unchecked_anti_patterns", "advice", "mitigation", mid,
                      "anti-patterns are listed but no acceptance criterion would catch "
                      "one of them", field="validation")


@rule("dangling_prerequisite", entity="mitigation", severity="error", label="Prerequisite that is not there")
def _dangling_prereq(mid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    for req in rec.get("requires") or []:
        if req not in cat.mitigations:
            yield Finding("dangling_prerequisite", "error", "mitigation", mid,
                          f"requires {req!r}, which is not in the catalog", field="requires")


@rule("orphan_control", entity="mitigation", severity="advice", label="Control no threat links")
def _orphan(mid: str, rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A card no threat links is a control with nothing to control."""
    linked = any(
        any(link.get("id") == mid for link in (t.get("mitigations") or []))
        for t in cat.threats.values()
    )
    if not linked and cat.threats:
        yield Finding("orphan_control", "advice", "mitigation", mid,
                      "no threat links this control")


# --------------------------------------------------------------------------- #
# Whole-catalog questions
# --------------------------------------------------------------------------- #
@rule("unused_nature", entity="catalog", severity="advice", label="Unused vocabulary")
def _unused_nature(_id: str, _rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A switch with one position costs a decision on every weakness and returns nothing."""
    weaknesses = [w for t in cat.threats.values() for w in (t.get("weaknesses") or [])]
    if weaknesses and not any(w.get("nature") == "secondary" for w in weaknesses):
        yield Finding("unused_nature", "advice", None, None,
                      "no weakness is marked 'secondary': the nature field may be unused")


@rule("merge_candidate", entity="catalog", severity="advice", label="Threats nothing tells apart")
def _merge_candidate(_id: str, _rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """Two chains are two threats only if ruling one out does not rule out the other, or
    closing one does not close the other. The second half is checkable: threats with the
    same harm closed by exactly the same gating controls differ, if at all, only in their
    reachability - and if that matches too, they are one threat with more weaknesses.

    Advice, not an error. A deliberate split with two genuinely different reachability
    gates is legitimate; the finding asks for that difference to be visible, and the style
    guide carries the test itself, which no rule can run."""
    seen: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for tid, rec in cat.threats.items():
        gating = tuple(sorted(
            link["id"] for link in (rec.get("mitigations") or [])
            if isinstance(link, dict) and link.get("strength") == "gating" and link.get("id")
        ))
        if not gating:                       # no_gating_control already speaks for these
            continue
        seen.setdefault((rec.get("harm") or "", gating), []).append(tid)
    for (harm, gating), ids in seen.items():
        if len(ids) < 2:
            continue
        for tid in sorted(ids):
            others = ", ".join(sorted(i for i in ids if i != tid))
            yield Finding(
                "merge_candidate", "advice", "threat", tid,
                f"same harm ({harm}) and the same gating controls ({', '.join(gating)}) "
                f"as {others}: say what rules one out and not the other, or make this one "
                f"threat with more weaknesses", field="reachability")


@rule("stale_coverage_claim", entity="catalog", severity="error", label="Coverage claim naming a deleted entry")
def _stale_coverage(_id: str, _rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """The matrix is Keel's public claim, so a row naming a deleted entry is not a broken
    link - it is a false statement about what Keel does."""
    for doc in cat.coverage:
        for entry in doc.entries:
            for kind, ids, known in (("threat", entry.threats, cat.threats),
                                     ("mitigation", entry.mitigations, cat.mitigations)):
                for ident in ids:
                    if ident not in known:
                        yield Finding(
                            "stale_coverage_claim", "error", "coverage", doc.source.id,
                            f"{entry.ref} claims {kind} {ident!r}, which is not in the catalog",
                            field=entry.ref)


@rule("partial_import", entity="catalog", severity="advice", label="Unfinished import")
def _partial_import(_id: str, _rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A matrix showing twelve rows of a hundred-and-one-entry release reads as complete.
    Saying "12 of 101" is the difference between a claim and a boast."""
    for doc in cat.coverage:
        got, want = len(doc.entries), doc.source.entry_count
        if got != want:
            yield Finding("partial_import", "advice", "coverage", doc.source.id,
                          f"{doc.source.title} {doc.source.version}: {got} of {want} "
                          f"entries imported")


@rule("nothing_answered", entity="catalog", severity="advice", label="Source nothing answers")
def _nothing_answered(_id: str, _rec: dict[str, Any], cat: Catalog) -> Iterable[Finding]:
    """A decline counts as an answer; a source of nothing but gaps is untouched."""
    for doc in cat.coverage:
        if doc.entries and all(e.state == "gap" for e in doc.entries):
            yield Finding("nothing_answered", "advice", "coverage", doc.source.id,
                          f"{doc.source.title} {doc.source.version}: every entry is a "
                          f"gap, so nothing in the catalog answers this source yet")


# --------------------------------------------------------------------------- #
# The two entry points
# --------------------------------------------------------------------------- #
def check_entity(entity_type: str, entity_id: str, cat: Catalog) -> list[Finding]:
    """Everything the rules say about one record. Run after a write, where it is all
    advice - the record is already on disk and blocking it now would be theatre."""
    records = cat.threats if entity_type == "threat" else cat.mitigations
    rec = records.get(entity_id)
    out: list[Finding] = []
    for r in REGISTRY.values():
        if r.entity != entity_type or rec is None:
            continue
        out.extend(r.fn(entity_id, rec, cat))

    # A change to one record can invalidate a claim made about it elsewhere, and only the
    # catalog-wide rules can see that.
    for r in REGISTRY.values():
        if r.entity == "catalog":
            out.extend(f for f in r.fn("", {}, cat)
                       if f.entity_id == entity_id or entity_id in f.message)
    return out


def check_all(cat: Catalog) -> list[Finding]:
    """Everything the rules say about everything. `keel validate` and the dashboard."""
    out: list[Finding] = []
    for r in REGISTRY.values():
        if r.entity == "threat":
            for tid, rec in sorted(cat.threats.items()):
                out.extend(r.fn(tid, rec, cat))
        elif r.entity == "mitigation":
            for mid, rec in sorted(cat.mitigations.items()):
                out.extend(r.fn(mid, rec, cat))
        else:
            out.extend(r.fn("", {}, cat))
    return sorted(out, key=lambda f: (f.severity != "error", f.entity_id or "", f.code))
