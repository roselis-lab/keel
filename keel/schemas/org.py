"""Organisation facts: what an organisation knows about itself, kept between assessments.

A platform many systems run on, a data-class policy, an answer that held for more than
one system. Without a place for these, every assessment asks the same people the same
questions, and a threat ruled out because "the gateway strips personal data" rests on a
sentence in one report that the next report cannot see.

One file per platform or policy, `org/<name>.yaml`, written by people. An assessment
reads them, asks once whether each fact it relies on still holds, and cites it as
`org:<name>#<fact-id>`. It never writes these files: it proposes an edit, and a person
makes it. A fact is a record of who confirmed what and when, not a control marked done;
nothing in Keel turns a fact into an implementation or a grade.
"""
import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keel.schemas.report import Evidence

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"

# A platform is something systems run on (a gateway, an agent runtime, an identity
# provider); a policy is a rule the organisation set (what counts as personal data, where
# each class may go). Anything else is still one of these two to whoever reads it.
OrgFileKind = Literal["platform", "policy"]


class OrgFact(BaseModel):
    """One statement, who stood behind it, and what it rests on."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=SLUG, description="Cited as org:<file>#<id>; stable once cited")
    statement: str = Field(..., min_length=1, description="The fact, in one or two sentences")
    confirmed_by: str = Field(..., min_length=1, description="The person who confirmed it: 'Name <email>' or a role")
    confirmed_on: datetime.date = Field(..., description="YYYY-MM-DD, the day it was confirmed")
    documents: list[str] = Field(
        default_factory=list,
        description="Links to the documents it rests on (an architecture page, a policy), "
        "or their names when there is no link",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Code it rests on, in the same shape as report evidence, so "
        "`keel recheck org/<file>.yaml --repo PATH` says whether the lines are still there",
    )
    systems: list[str] = Field(
        default_factory=list,
        description="Optional: ids of the assessed systems that rely on it",
    )

    @model_validator(mode="after")
    def _rests_on_something(self) -> "OrgFact":
        if not self.documents and not self.evidence:
            raise ValueError(
                f"fact {self.id}: say what it rests on - a document in `documents` or "
                "code in `evidence`. A confirmation alone is someone's memory"
            )
        return self


class OrgFile(BaseModel):
    """One platform or one policy, and the facts about it."""

    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=1)
    kind: OrgFileKind
    about: str = Field(..., min_length=1, description="What this platform or policy is, so an assessor can tell whether it applies")
    facts: list[OrgFact] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _ids_unique(self) -> "OrgFile":
        for label, ids in (
            ("fact", [f.id for f in self.facts]),
            ("evidence", [e.id for f in self.facts for e in f.evidence]),
        ):
            dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
            if dup:
                raise ValueError(f"{label} ids repeat in this file: {', '.join(map(str, dup))}")
        return self

    @property
    def evidence(self) -> list[Evidence]:
        """Every evidence entry in the file, so `keel recheck` reads it like a report."""
        return [e for f in self.facts for e in f.evidence]
