"""Threat schema: component/surface → weakness(nature) → threat → harm → source →
reachability → mitigation(strength). Frozen vocabularies as Literals; prose fields
free; references are real URLs.
"""
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl

# --- frozen vocabularies (mirrored in catalog/{components,harm,surface,source}.yaml) ---
Component = Literal["model", "tool", "downstream", "memory", "knowledge-base", "identity-store"]
Harm = Literal[
    "wrong-decision", "data-integrity", "data-exposed", "code-execution",
    "downtime", "reputation-legal",
]

# The channel through which content reaches a component. A boundary is not a pair of
# talkers ("user to agent") — that list is never closed and says nothing about where a
# control goes. It is what a component takes in and treats as trustworthy: the model
# trusts its prompt, the tool layer trusts what a call returns, the agent trusts what
# search brought back. Component + surface together name the place a control sits.
Surface = Literal[
    "user-input", "retrieved-content", "tool-output", "agent-message",
    "memory", "training-data", "model-output",
]

# Who or what put the bad thing there. Kept apart from `surface`, which is how it
# arrived, and from `component`, which is where it landed — three questions, three
# fields. `training-data` used to sit here and was the odd one out: it is a channel,
# not an origin. Poisoned training data is an external-attacker arriving through the
# training-data surface at the model.
Source = Literal["external-attacker", "internal", "hallucination", "error", "accident"]
Nature = Literal["targeted", "secondary"]
Strength = Literal["gating", "soft"]


class Weakness(BaseModel):
    """An architectural predisposing condition on a component."""

    model_config = ConfigDict(extra="forbid")
    component: Component
    surface: list[Surface] = Field(
        default_factory=list,
        description="The channels this weakness is reached through, when it is about "
        "content crossing into the component. A list, because one condition is often "
        "reachable over several channels and one control closes it on all of them - "
        "splitting it per channel would make three weaknesses of one. Empty for a "
        "weakness about the component's own authority, which nothing has to flow in to "
        "exploit",
    )
    text: str = Field(..., description="Architectural condition: cause + where + defect")
    nature: Nature = "targeted"


class MitigationLink(BaseModel):
    """Link to a mitigation card, with its role for this threat."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="A real CTRL-* mitigation id")
    strength: Strength = Field(..., description="gating (blocks) | soft (only lowers likelihood)")
    rationale: str
    exception: str | None = Field(
        None,
        description="Rare, narrow carve-out where this control doesn't apply to this threat "
        "(the threat itself stays live) — NOT a restatement of reachability",
    )


class Reference(BaseModel):
    """Evidence for the threat: an incident, a paper, an advisory.

    NOT a framework mapping. Which OWASP or ATLAS entries this threat answers is
    recorded once in `catalog/coverage/` and read back from there, so a reference
    that only says "this is LLM01" is a duplicate of the coverage matrix.
    """

    model_config = ConfigDict(extra="forbid")
    title: str
    url: HttpUrl
    note: str = Field(
        ...,
        description="One line: what this source actually supports. A bare link asks every "
        "later reader to re-derive why it was worth citing",
    )


def _checked_id(value: str) -> str:
    """An id is also a file name, so it is constrained here rather than left to the store
    to discover. The store refuses to leave its directory regardless; this layer exists to
    say why in a sentence the author can act on, using the same rule so the two cannot
    disagree."""
    from keel.store import is_safe_stem

    problem = is_safe_stem(value)
    if problem:
        raise ValueError(f"not usable as an id or a file name: {problem}")
    return value


EntityId = Annotated[str, AfterValidator(_checked_id)]


class Threat(BaseModel):
    """A threat: what can go wrong, resting on weaknesses at components."""

    model_config = ConfigDict(extra="forbid")
    id: EntityId = Field(
        ...,
        description="Letters, digits, dot, hyphen and underscore. It is also the file "
        "name, so anything that could be read as a path is refused",
    )
    title: str
    harm: Harm
    # No `surface` here: a threat is a chain and crosses more than one boundary, so a
    # list on the threat could never say which weakness sits on which. It is a property
    # of the weakness, and the threat's set of surfaces is read back off them.
    source: list[Source] = Field(default_factory=list)
    weaknesses: list[Weakness] = Field(..., min_length=1)
    reachability: str = Field(
        ...,
        description="Rule-out gate: the condition under which this threat is not a live "
        "path at all, judged on the un-mitigated architecture",
    )
    mitigations: list[MitigationLink] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    positioning: str | None = Field(
        None,
        description="How this entry sits relative to the entries in the sources Keel "
        "tracks - only what the mapping itself does not already say. Where a source's "
        "entry is broader than this one, say what the rest of it is and where that "
        "lives. Never catalog state (which is computed) and never a to-do",
    )
    tags: list[str] = Field(default_factory=list)


class ThreatCreate(Threat):
    """Create payload — same shape, id required."""


class ThreatUpdate(BaseModel):
    """Partial update; only provided fields change."""

    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    harm: Harm | None = None
    source: list[Source] | None = None
    weaknesses: list[Weakness] | None = None
    reachability: str | None = None
    mitigations: list[MitigationLink] | None = None
    references: list[Reference] | None = None
    positioning: str | None = None
    tags: list[str] | None = None
