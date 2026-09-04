"""Coverage: what the sources we track say, and what Keel has to say back.

Keel's whole claim to trust is that it is not a fourth list nobody asked for. That claim
only means something if it is checkable, so each tracked source gets a file naming every
entry in a pinned release, and every entry gets one of three states.

The states are the point. `covered` is easy and everyone claims it. `gap` is the honest
admission that we have not got to it. `out_of_scope` is the one that earns a reader's
trust: it draws Keel's boundary with the reasoning attached, so someone who came looking
for an entry can see it was considered and where the line fell, rather than guessing
whether it was missed.

A row records the mapping and nothing else. Why a particular entry answers a source is a
property of that entry - it lives in the entry's `positioning`, because a row is about the
whole set of ids and a sentence written about one of them stops being true when a second
is added.

`out_of_scope` describes Keel, not the source. It is not a disagreement with the source's
judgment, and it is not the place to record "we cover this differently" - an entry Keel
answers in a shape of its own is `covered`, and the shape is explained on the entry.
The only thing that belongs here is a subject Keel does not model at all.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

CoverageState = Literal["covered", "out_of_scope", "gap"]


class CoverageSource(BaseModel):
    """The tracked release itself. Pinned, because "we cover OWASP" is not a claim you
    can check unless it says which OWASP."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Slug, matching the filename (e.g. 'owasp-llm')")
    title: str
    version: str = Field(..., description="The published release this file describes")
    released: str | None = Field(None, description="Release date, ISO, when the source states one")
    url: HttpUrl
    checked: str = Field(..., description="ISO date this file was last read against the source")
    entry_count: int = Field(
        ...,
        ge=0,
        description="How many entries the release has. Stated separately from the list "
        "below so a half-finished import counts as unfinished instead of looking complete",
    )
    note: str | None = None


class CoverageEntry(BaseModel):
    """One entry of the tracked source, and what Keel does about it."""

    model_config = ConfigDict(extra="forbid")
    ref: str = Field(..., description="The source's own identifier (LLM01, ASI02, AML.T0051)")
    title: str = Field(..., description="The source's own name for it, verbatim")
    group: str | None = Field(
        None,
        description="The source's own grouping, where it has one (an ATLAS tactic). A flat "
        "list of eighty-odd rows is not readable; grouped, it is",
    )
    state: CoverageState
    threats: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    note: str | None = Field(
        None,
        description="Required when out_of_scope: where Keel's boundary falls and why. "
        "Allowed on a gap, for what it is waiting on. Refused on a covered row: why an "
        "entry answers this source belongs on the entry, in `positioning`",
    )

    @model_validator(mode="after")
    def _state_matches_content(self) -> "CoverageEntry":
        has_ids = bool(self.threats or self.mitigations)
        if self.state == "covered":
            if not has_ids:
                raise ValueError("covered must name at least one threat or mitigation")
            if (self.note or "").strip():
                raise ValueError(
                    "a covered row carries no note: why an entry answers this source is a "
                    "property of the entry, so it goes in that entry's `positioning`. A "
                    "note here is written about the set of ids as it stands and goes stale "
                    "the moment a second one joins it"
                )
        if self.state == "gap" and has_ids:
            raise ValueError("gap must name nothing — if something answers it, it is covered")
        if self.state == "out_of_scope":
            if has_ids:
                raise ValueError(
                    "out_of_scope must name nothing — an entry Keel answers in a shape of "
                    "its own is covered, with a note explaining the shape"
                )
            if not (self.note or "").strip():
                raise ValueError(
                    "out_of_scope needs a note: a boundary without its reasoning is "
                    "indistinguishable from an omission"
                )
        return self


class CoverageFile(BaseModel):
    """One tracked source: `catalog/coverage/<id>.yaml`."""

    model_config = ConfigDict(extra="forbid")
    source: CoverageSource
    entries: list[CoverageEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs_are_unique(self) -> "CoverageFile":
        seen = set()
        for e in self.entries:
            if e.ref in seen:
                raise ValueError(f"duplicate ref {e.ref!r}")
            seen.add(e.ref)
        return self
