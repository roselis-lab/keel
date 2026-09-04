"""Which style-guide entity each write tool authors, and the rule that goes with it.

Methodology is deliberately NOT inlined into tool descriptions — it is thousands of
tokens, it goes stale against the catalog, and it dilutes in long contexts. The model
fetches it with `get_style_guide` right before writing.

The rule saying so used to be repeated in full on every write tool: five copies of the
same paragraph, 11% of the whole tool list, paid for in every conversation. It is stated
once now, in the server's `instructions`, and each tool carries only the one fact that
differs between them — which entity it authors.
"""
from __future__ import annotations

# Tool name -> entity type; populated by the registry decorator.
TOOL_ENTITY_TYPES: dict[str, str] = {}

SERVER_INSTRUCTIONS = """Keel is a threat model you author, not a document you read.

The catalog is YAML on disk and every write lands in a file. `catalog/` holds only
content a maintainer has vouched for; `drafts/` holds the rest and is not served here.

Before authoring or editing anything the style guide covers, call
`get_style_guide(entity_type=...)` and follow it — it defines the required field
formats, content rules, avoid-lists and examples, and it is the difference between a
card that survives review and one that does not. Each write tool names its entity type.
For one field, `get_style_guide(entity_type=..., field_name=...)` is far cheaper than
the whole entity.

`get_model` explains how the pieces fit together and what Keel deliberately does not
model. Read it before deciding where a new piece of information belongs; the field-level
guide cannot answer a placement question.

`search` runs one query across threats, mitigations, coverage rows and past
assessments. Reach for it before listing anything: whether a subject is already in the
library is a search, not an enumeration.

`get_coverage` is the answer to "does Keel cover X?" for the sources Keel tracks
(OWASP LLM Top 10, OWASP Agentic Top 10, MITRE ATLAS, Google SAIF). An entry there is
`covered` (sometimes in a shape of its own, which its note explains), `out_of_scope` with
the reasoning, or `gap`. Check it before concluding something is missing — both of the
first two read like omissions if you only search the catalog.

Assessments are written through `create_report` and `save_report`, never as files. Those
calls check what a file write cannot — that grades are on the allowed scale, and that
every catalog id the report names exists. Finalising a report is the specialist's own
judgment and is not exposed here.

`check_library_health` reports three separate tiers: `errors` (a record failed its
schema and is not being served — file, field and reason are given), `warnings`
(advisory, and a half-authored draft may legitimately trip them), and `issues`
(content gaps in records that loaded fine)."""


def register_tool_entity(tool_name: str, entity_type: str) -> None:
    TOOL_ENTITY_TYPES[tool_name] = entity_type


def get_tool_style_pointer(tool_name: str) -> str:
    """The one style-guide fact that differs per tool. The rule itself is in
    SERVER_INSTRUCTIONS, stated once."""
    entity_type = TOOL_ENTITY_TYPES.get(tool_name)
    if not entity_type:
        return ""
    return f'\n\nStyle guide entity: "{entity_type}".'
