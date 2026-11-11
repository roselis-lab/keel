"""Report schema: a persisted assess-genai-with-library run.

A report has two lives, and the `status` field is what keeps them apart. As a **draft**
it is unfinished work: the skill writes the first pass, then the specialist corrects it
in the UI — grades, wording, which requirements actually ship. Once **final** it is a
dated record of what was assessed on that day, and nothing rewrites it; correcting a
final report means opening a new dated draft beside it. Without that split, "the
assessment of 2026-08-26" degrades into "whatever someone last typed".

Enum fields reuse the catalog's own vocabularies (`Harm`, `Surface`, `Source`) rather
than defining parallel ones, so a report's risk signals line up with the model they
came from.
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keel.schemas.threat import Harm, Source, Surface

# Three levels, and the same three for every graded axis. An organisation's own risk
# policy is what turns a grade into an action, and policies are written against three
# bands; a fourth level ("critical") only ever meant "high, but really" and gave the
# assessor a choice with no consequence attached to it.
ExploitationComplexity = Literal["low", "medium", "high"]
Likelihood = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high"]
CoverageStatus = Literal["already_covered", "needs_implementation", "partial"]
ReportStatus = Literal["draft", "final"]
# Whether the feature the finding rests on runs today. Kept apart from likelihood so a
# switched-off feature does not read as an unlikely attack: the grade describes the
# design as it will run, and this says what is switched on now.
Deployment = Literal["live", "pilot", "off", "not_deployed"]
# How an evidence entry was obtained in this session.
EvidenceKind = Literal["read", "command", "test"]
# What an open question asks for. "access" is for when the assessor knows where the
# fact lives and lacks the right or the document to read it: asking for that is a
# narrower request than asking someone to recall the fact.
AskKind = Literal["fact", "access"]
# What a ledger row is: a way in (endpoint, chat, inbox, webhook), a tool the model can
# call, a data path in or out (retrieval, memory, files, provider calls), or a file read
# to establish the others.
SurfaceKind = Literal["entry", "tool", "data", "file"]
# A reviewer who tried to break a finding and could not ("stands"), or broke one link
# only partly ("weakened"). A finding the reviewer broke is not a finding: it is ruled
# out, in `Report.discarded` with `by: review`.
ReviewVerdict = Literal["stands", "weakened"]
# What ruled a candidate out: its catalog reachability condition holding here, or a
# reviewer breaking a link of its chain after it was graded.
DiscardedBy = Literal["reachability", "review"]
# Where the threat stands against the state before the integration. "legacy" existed
# before and the integration did not change it: still graded and still given measures,
# only not counted against the integration.
Origin = Literal["new", "changed", "legacy"]


class Evidence(BaseModel):
    """One checked claim, kept out of the prose and referenced from it.

    The text of a finding stays readable: a claim carries one marker, `[3]`, or an
    embedded link to `#ev-3`, and the pointer itself lives here. A pointer is to the
    exact place, pinned to a commit: a file or a branch moves, and evidence that moved
    no longer proves anything. The quote is required so the entry still says something
    to a reader who cannot open the source.
    """

    model_config = ConfigDict(extra="forbid")
    id: int = Field(..., ge=1, description="Referenced from prose as [id] or #ev-id")
    kind: EvidenceKind
    quote: str = Field(
        ..., min_length=1,
        description="Verbatim: the lines read, or the output of the command or test",
    )
    commit: str | None = Field(
        None, pattern=r"^[0-9a-f]{7,40}$", description="kind=read: the commit the lines are read at"
    )
    # A system often spans several repositories, and a path alone does not say which
    # one it is in; the next assessor would have to search for it. A short name, not
    # an address: it is model output, so it stays a plain token that carries nothing.
    repo: str | None = Field(
        None, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]*$",
        description="kind=read: which repository `path` is in, when the system spans more "
        "than one. A short stable name, e.g. 'payments-api' or 'org/payments-api'; empty "
        "for a single-repository system. `keel recheck --repo NAME=PATH` maps it to a checkout",
    )
    path: str | None = Field(None, description="kind=read: the file, relative to the repository root")
    lines: str | None = Field(
        None, pattern=r"^[1-9][0-9]*(-[1-9][0-9]*)?$", description="kind=read: '42' or '42-57'"
    )
    url: str | None = Field(
        None,
        description="Optional permalink to the same lines. Must be https, on a host in the "
        "organisation's evidence_hosts, and contain the commit: anything else is refused on save",
    )
    command: str | None = Field(None, description="kind=command or test: exactly what was run")

    @model_validator(mode="after")
    def _validate(self) -> "Evidence":
        if self.kind == "read":
            missing = [k for k in ("commit", "path", "lines") if not getattr(self, k)]
            if missing:
                raise ValueError(
                    f"evidence {self.id}: a read needs {', '.join(missing)} - point at the "
                    "exact lines at a commit, not at a file or a branch"
                )
        elif not (self.command or "").strip():
            raise ValueError(f"evidence {self.id}: a {self.kind} needs the command that was run")
        return self


class OpenQuestion(BaseModel):
    """A fact the assessment cannot go past without.

    Not a note for later. The branch that needs it stops here (see `Paused`) and the
    report cannot be finalized while `answer` is empty. `looked_in` is what keeps the
    question honest: a fact the assessor could have read in the code is not a question.
    """

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^Q[1-9][0-9]*$")
    question: str = Field(..., min_length=1)
    asks_for: AskKind = Field(
        "fact", description="'access' when the place is known and the right or document is missing"
    )
    looked_in: str = Field(
        ..., min_length=1, description="Where the assessor looked before asking, and why it did not settle it"
    )
    needed_for: str = Field(..., min_length=1, description="Which branch waits, and at which step")
    how_to_check: str | None = Field(
        None, description="The exact check that settles it (a query, a command, a setting to "
        "open, who to ask), so the person answering can run it rather than recall it",
    )
    answer: str | None = None


class Paused(BaseModel):
    """A threat candidate whose branch waits on an open question.

    Neither a finding nor a discard: it carries no grade, no requirements and no reason
    to drop it, because the fact that would decide those is not in yet. Once the answer
    comes, it becomes one or the other.
    """

    model_config = ConfigDict(extra="forbid")
    id: str
    from_catalog: bool
    waiting_on: list[str] = Field(..., min_length=1, description="Ids of open questions")
    note: str = Field(..., min_length=1, description="What is established so far, and what the answer decides")


class SourceInfo(BaseModel):
    """Who or what drives the threat, and what makes it realistic here.

    The same two fields answer method step 3 for both kinds of source. For an attacker
    (external, supply chain, insider, the model's own goal): the goal, and the real access
    to the surface. For a source without one (model mistake, overeagerness, error,
    accident): what triggers it in this system, and the permissions it acts with. Such a
    source still has a trigger, so `motive` is never just "none".
    """

    model_config = ConfigDict(extra="forbid")
    who: Source
    motive: str = Field(
        ..., description="An attacker's goal; for a source without one, what triggers it in this system"
    )
    access: str = Field(
        ..., description="An attacker's real access to the surface; for a source without one, the permissions it acts with"
    )


class RiskInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    likelihood: Likelihood
    severity: Severity
    reasoning: str


class Review(BaseModel):
    """Someone who did not raise the finding tried to break it.

    Agreement is cheap; a finding that survived a real attempt to break its chain is what
    a `high` should rest on. The note says which links were tried and with what, so the
    verdict can itself be checked.
    """

    model_config = ConfigDict(extra="forbid")
    by: str = Field(..., min_length=1, description="A fresh reviewer agent, or the specialist by name")
    verdict: ReviewVerdict
    note: str = Field(..., min_length=1, description="Which links were tried, with which facts")


class Requirement(BaseModel):
    """One risk-reduction ask.

    Thin on purpose: a cataloged mitigation's `purpose`/`control_mechanism` already say
    what it does, and its threat-link `rationale` says why it fits — both one lookup away
    by `mitigation_id`. This records only the assessment-specific judgment (is it already
    covered in THIS deployment?) plus, for anything not yet in the catalog, the actual ask.
    """

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str | None = None
    coverage_status: CoverageStatus
    coverage_note: str | None = None
    description: str | None = None
    included: bool | None = Field(
        None,
        description="Ships in the hand-off to the product team. None means 'not decided "
        "yet' and resolves to the obvious default: anything already covered is left out.",
    )
    # A catalog card already carries these in general terms (purpose, locus,
    # validation). Here they say it for THIS system. An ask with no card has nothing
    # else to stand on, so finalizing waits for all three on such an ask.
    invariant: str | None = Field(None, description="What must always hold once it is built, about this system")
    enforce_at: str | None = Field(
        None, description="The narrowest place it is enforced: the last point the system still trusts before the harm"
    )
    done_check: str | None = Field(
        None, description="How to tell it is done, best a test that fails today and passes after the fix"
    )

    @model_validator(mode="after")
    def _validate(self) -> "Requirement":
        # Resolve `included` on read so it is always a concrete boolean downstream, and
        # so the decision is recorded in the file the moment the report is saved. This
        # used to be a checkbox that existed only at copy time: it could not survive a
        # reload, which made it look like decoration rather than a judgment.
        if self.included is None:
            self.included = self.coverage_status != "already_covered"
        if self.mitigation_id is None and not (self.description or "").strip():
            raise ValueError("description is required when mitigation_id is null")
        if self.mitigation_id is not None and self.description:
            raise ValueError(
                "description only applies when mitigation_id is null "
                "(a catalog card already names the control)"
            )
        needs_note = self.coverage_status in ("already_covered", "partial")
        if needs_note and not (self.coverage_note or "").strip():
            raise ValueError(
                "coverage_note is required when coverage_status is 'already_covered' or 'partial'"
            )
        if not needs_note and self.coverage_note:
            raise ValueError("coverage_note only applies to 'already_covered' or 'partial'")
        return self


class IgnoredMitigation(BaseModel):
    """A control linked to this threat in the catalog, but not applicable to this system."""

    model_config = ConfigDict(extra="forbid")
    mitigation_id: str
    reason: str


class Discarded(BaseModel):
    """A threat candidate ruled out, and why, so the next assessment does not re-derive it.

    Deliberately NOT the full `Finding` chain — a discard is an id and why, nothing more.
    Two things rule a candidate out. By `reachability`: the threat's catalog condition
    holds in this system, established from facts. By `review`: someone who did not raise
    a graded finding broke a link of its chain, and the reason says which link and with
    what fact. A small consequence is not a discard: that threat is live and graded low.
    A branch still waiting on a fact is not a discard either: it is `Paused`.

    A later assessment of the same system that raises it again is told so on save, and
    names the new fact that brings it back.
    """

    model_config = ConfigDict(extra="forbid")
    id: str
    by: DiscardedBy = "reachability"
    root_cause: str | None = Field(None, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    reason: str = Field(
        ..., description="By reachability: how the condition holds here, with the fact. By "
        "review: which link of the chain does not hold, with the fact"
    )
    evidence: list[int] = Field(default_factory=list, description="Ids of the evidence entries the reason rests on")


class SurfaceEntry(BaseModel):
    """One row of the surface ledger: a place something reaches this system.

    The catalog proves every threat class was considered; the ledger proves every surface
    was walked. A row ends with the findings, discards or paused branches
    that cross it, or with a note saying why nothing reaches harm through it.
    """

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^S[1-9][0-9]*$")
    kind: SurfaceKind
    name: str = Field(..., min_length=1)
    where: str = Field(..., min_length=1, description="The endpoint, tool name, path or flow")
    evidence: list[int] = Field(default_factory=list, description="Where it was seen")
    outcome: list[str] = Field(
        default_factory=list, description="Ids of the findings, discards or paused branches that cross it"
    )
    note: str | None = Field(None, description="With an empty outcome: why nothing reaches harm through it")
    found_by: Literal["assessor", "review"] = "assessor"


class DialogueEntry(BaseModel):
    """One question the agent asked the specialist, and what the answer changed.

    This is the reasoning that otherwise disappears into chat history: the question, the
    answer it got back, and how the analysis moved because of it.
    """

    model_config = ConfigDict(extra="forbid")
    question: str
    answer: str
    impact: str


class RunMeta(BaseModel):
    """How this assessment ran — the record kept to improve the assessor, not the system.

    Everything here is about the process, which is why none of it reaches the hand-off:
    a product team has nowhere to put "the agent asked four questions". It exists because
    the only way to make the skill better is to see where it fell short, and the three
    things that show that are: what it thought to ask, what it FAILED to ask (so the
    specialist had to volunteer it), and where the specialist said it was wrong.

    `volunteered` is the sharpest of the three. A question the agent asked is a question
    the skill already knows to ask; a fact the specialist had to supply unprompted is a
    hole in the skill, named precisely.
    """

    model_config = ConfigDict(extra="forbid")
    started_at: str | None = Field(
        None, description="ISO timestamp when the skill began, so the run can be timed"
    )
    finished_at: str | None = Field(None, description="ISO timestamp when the report was written")
    questions: list[DialogueEntry] = Field(
        default_factory=list, description="What the agent asked, and what each answer changed"
    )
    volunteered: list[str] = Field(
        default_factory=list,
        description="Context the specialist gave that the agent never asked for — the skill's blind spots",
    )
    critique: list[str] = Field(
        default_factory=list,
        description="Where the specialist said the agent's reasoning was wrong, in their words",
    )


class Finding(BaseModel):
    """A threat that survived analysis, with its full chain."""

    model_config = ConfigDict(extra="forbid")
    id: str
    from_catalog: bool
    scenario: str
    source: SourceInfo
    asset: str
    attack_surface: Surface | None = Field(
        None, description="The channel the path crosses. Empty only when the weakness has none, "
        "e.g. a standing credential reachable without anything crossing a boundary",
    )
    vulnerability: str
    exploitation_complexity: ExploitationComplexity
    harm: Harm
    risk: RiskInfo
    risk_today: RiskInfo | None = Field(
        None, description="Only when deployment is not live: the grade with today's switch, "
        "beside `risk` for the design as it will run",
    )
    delta: str
    origin: Origin | None = Field(
        None, description="new, changed by the integration, or legacy: existed before and "
        "unchanged, still graded and given measures, not counted against the integration",
    )
    deployment: Deployment | None = Field(
        None, description="What is switched on today. The grade describes the design as it will run"
    )
    root_cause: str | None = Field(
        None, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="Short stable slug of the defect, the same across re-assessments and across "
        "systems that share it. With system_id and id it forms the finding's fingerprint",
    )
    evidence: list[int] = Field(
        default_factory=list, description="Ids of the evidence entries this finding's claims rest on"
    )
    review: Review | None = Field(
        None, description="Required on a high-severity finding before finalizing"
    )
    requirements: list[Requirement] = Field(default_factory=list)
    ignored_mitigations: list[IgnoredMitigation] = Field(default_factory=list)


class Report(BaseModel):
    """One assessment of one system on one date."""

    model_config = ConfigDict(extra="forbid")
    system_id: str
    system_name: str
    system_description: str = Field(
        ..., description="What the skill compares against when proposing a system match later"
    )
    date: str
    assessor: str = Field(..., description="From git config user.name/user.email at write time")
    status: ReportStatus = Field(
        "draft",
        description="draft = still being corrected in the UI; final = frozen dated record",
    )
    delta_summary: str | None = Field(None, description="Re-assessments only: what changed and why")
    findings: list[Finding] = Field(default_factory=list)
    paused: list[Paused] = Field(
        default_factory=list, description="Branches waiting on an open question: no grade, no discard"
    )
    discarded: list[Discarded] = Field(default_factory=list)
    surfaces: list[SurfaceEntry] = Field(
        default_factory=list, description="The surface ledger: every place something reaches this system"
    )
    open_questions: list[OpenQuestion] = Field(
        default_factory=list, description="Facts the assessment needs; finalizing waits for every answer"
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="The addendum: every checked claim, referenced from the prose"
    )
    # Named `meta`, not `_meta`: pydantic treats a leading underscore as a private
    # attribute and would not accept it as a field.
    meta: RunMeta = Field(
        default_factory=RunMeta, description="How the assessment ran — see RunMeta"
    )
    # Free-form on purpose: an extension owns the shape of its own section and checks it
    # itself (keel/extensions.py). A report written with an extension must still open on
    # a Keel without it, so nothing here may refuse what is inside.
    extensions: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Data kept by an installed extension, under the extension's name. "
        "Keel stores it and does not read it.",
    )
