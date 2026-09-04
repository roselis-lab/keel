"""The shape of the model itself.

`get_style_guide` says what each field must contain and `get_vocabulary` says what its
values mean, but neither says how the pieces fit together, and that is what decides
placement. "Is prompt injection a threat or something else?" is not a question about a
field; it is a question about the shape.

Derived from the pydantic models rather than written out, so it cannot drift from the
schema it describes. Only the prose - the chain, and what Keel deliberately does not
model - is authored here, because neither is recoverable from a type.
"""
from typing import get_args

from keel.mcp.registry import register_tool
from keel.schemas.mitigation import MitigationClass, MitigationCreate
from keel.schemas.threat import (
    Component, Harm, MitigationLink, Nature, Source, Strength, Surface, Threat, Weakness,
)

_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

CHAIN = (
    "A weakness sits on a component, reached across a surface - the channel whose "
    "content that component treats as trustworthy. A threat rests on one or more "
    "weaknesses, is driven by a source, and lands as exactly one harm. Its reachability "
    "says when it is not a live path at all. Mitigations link to it, each link graded "
    "gating or soft. One threat is one chain: two chains are two threats if and only if "
    "ruling one out does not rule out the other, or closing one does not close the other."
)

NOT_ENTITIES = {
    "mechanisms": (
        "How untrusted influence gets in - prompt injection, jailbreaking, a poisoned "
        "document. These are not threats and not weaknesses. They appear as a weakness's "
        "`surface`, a threat's `source`, and in `references`; a technique aimed at "
        "defeating a control appears in that control's acceptance criteria. A threat "
        "titled after a technique is the most common modelling error here."
    ),
    "consequences": (
        "What follows the harm - a fine, a headline, a rollback. The `harm` value is "
        "where the consequence class is recorded; the story of a particular incident "
        "belongs in an assessment, not in the catalog."
    ),
    "absent controls": (
        "\"There is no rate limit\" is a weakness only if it is an architectural "
        "condition of the system. A control that ought to exist is a mitigation, or an "
        "ad hoc requirement on an assessment - never a threat."
    ),
    "org specifics": (
        "How a particular company realises a control, who owns it, what it covers: "
        "`Implementation` on the mitigation card, which ships empty in the shared "
        "catalog. Never in a card's own prose."
    ),
}


def _fields(model) -> dict:
    out = {}
    for name, f in model.model_fields.items():
        entry = {"required": f.is_required()}
        vocab = {
            "harm": Harm, "surface": Surface, "source": Source, "component": Component,
            "nature": Nature, "strength": Strength, "mitigation_class": MitigationClass,
        }.get(name)
        if vocab is not None:
            entry["values"] = list(get_args(vocab))
        out[name] = entry
    return out


@register_tool(annotations=_RO)
async def get_model() -> dict:
    """Explains how Keel's model fits together - read this before deciding where a new
    piece of information belongs.

    Returns `chain` (one sentence connecting component, weakness, threat, harm and
    mitigation), `entities` (every field of every entity, which are required, and the
    frozen value list where one applies), `relationships` (what points at what), and
    `not_modelled` - the four kinds of thing that look like entries and are not, with
    where each actually goes.

    `not_modelled` is the scope test. Something that is not a threat, a weakness, a
    mitigation or an implementation is out of scope, and the coverage matrix records
    every scope decision already taken with its reasoning - call get_coverage with
    state="out_of_scope" for the precedents before deciding a new one."""
    return {
        "chain": CHAIN,
        "entities": {
            "threat": {"stored": "catalog/threats/<id>.yaml", "fields": _fields(Threat)},
            "weakness": {"stored": "inside a threat", "fields": _fields(Weakness)},
            "mitigation": {"stored": "catalog/mitigations/<id>.yaml",
                           "fields": _fields(MitigationCreate)},
            "mitigation_link": {"stored": "inside a threat", "fields": _fields(MitigationLink)},
        },
        "relationships": [
            "threat.weaknesses[].component -> one of the frozen component values",
            "threat.mitigations[].id -> a mitigation card, graded gating or soft",
            "coverage entry -> the threats and mitigations that answer it (never stored "
            "on the card; read it back with get_threat's `cited_by`)",
            "report finding -> a catalog threat id, or its own id when the threat is "
            "specific to that system",
            "report requirement -> a mitigation id, or null plus a description when the "
            "library has no card for it",
        ],
        "not_modelled": NOT_ENTITIES,
    }
