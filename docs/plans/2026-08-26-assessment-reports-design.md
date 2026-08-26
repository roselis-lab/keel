# Assessment reports — design

Date: 2026-08-26. Branch: threat-model-v2.

## What this covers

Today `assess-genai-with-library` (the Keel-specific overlay on the calibrated `assessing-genai-security` methodology) produces a two-part chat response — an auditable analysis trail, then a final risk table — and nothing persists. The user wants each assessment run written to a markdown-backed record the team can build an archive from, browse in the app, and hand to a product team without re-explaining the whole analysis every time.

Beyond the two obvious readers (the assessor checking their own work, and the product team receiving requirements), the archive earns its keep in three more ways already wired into the rest of the model: it is what makes a mitigation card's `review` field (change-triggers for revisiting a card) actionable — something to diff against on re-assessment — instead of a triggered check with nothing to compare to; it is raw material the `folding-into-the-model` and `checking-model-coverage` skills can mine for catalog gaps a specialist flagged but that never made it into the model; and it can serve as audit/compliance evidence, a third audience distinct from the assessor and the product team.

This design also depends on two small catalog changes made earlier the same session, in support of this feature: `MitigationLink.exception` (a rare, narrow carve-out where one linked control doesn't apply to one threat, even though the threat stays live — gives the report skill a starting hypothesis for `ignored_mitigations`) and `Implementation.owner` (the accountable role for a specific deployed instance — surfaced in reports next to any requirement that maps to a real catalog control).

## Storage and file layout

`reports/<system-slug>/<YYYY-MM-DD>.yaml` (source of truth) plus `<YYYY-MM-DD>.md` (a full, git-browsable self-check rendering, written at the same time). Both live inside the repository, versioned alongside `catalog/` — no separate infrastructure, no `.gitignore` carve-out, on the reasoning that `Implementation.owner`/`covers` already commit an org's real deployment details into this repo, so the repo is already expected to be private once forked; reports don't need a different trust boundary.

A report is written once and never edited after the fact (no PATCH route, no in-app editor) — a series for one system is just every file in its folder, newest date last; "is this a re-assessment" and "what's the previous report" are both derivable from the folder listing, not stored fields.

Only the YAML is authoritative. The `.md` companion is a pre-baked full rendering for reading the record without the app running (browsing the repo, a PR diff); it is safe to bake once and never regenerate because the record is immutable — unlike the JSON-schema-from-Pydantic case elsewhere in this codebase, there's no drift risk from a source that keeps changing after the derived file is written.

## Report schema

```yaml
system_id: checkout-agent
system_name: Checkout Agent
system_description: >
  Short description — what the report skill compares against when it proposes
  a system match on a later assessment.
date: 2026-08-26
assessor: Jane Doe <jane@example.com>     # from git config user.name/user.email at write time
delta_summary: >                          # present only on a re-assessment
  What changed since the previous report and why it was re-evaluated.

findings:                                 # SURVIVED only; full chain
  - id: T-SSRF                            # a real catalog id if matched, else a local slug
    from_catalog: true
    scenario: "prose: who does what, what is lost, for this system"
    source: {who: external-attacker, motive: "...", access: "..."}   # who: reuses catalog Source enum
    asset: "..."
    attack_surface: agent-environment      # reuses catalog Surface enum
    vulnerability: "..."
    exploitation_complexity: medium        # enum: low | medium | high
    harm: code-execution                   # reuses catalog Harm enum
    risk: {likelihood: medium, severity: high, reasoning: "..."}   # both enums: low | medium | high (severity also: critical)
    delta: "... in MITRE ATLAS terms"
    requirements:
      - mitigation_id: CTRL-URL-ALLOWLIST   # null => an ad hoc requirement, not in the catalog yet
        coverage_status: needs_implementation   # already_covered | needs_implementation | partial
        coverage_note: null                 # required only for already_covered / partial
        description: null                   # required only when mitigation_id is null
    ignored_mitigations:                    # linked to this threat in the catalog, not used here
      - mitigation_id: CTRL-SOME-OTHER
        reason: "no outbound network egress on this system at all"

discarded:                                  # id/label + reason ONLY — no chain fields
  - id: T-XSS
    reason: "output is returned as plain JSON to the caller, no render path"

dialogue:
  - question: "Does the agent's output render as HTML anywhere downstream?"
    answer: "No — plain JSON to the caller."
    impact: "Ruled out stored-XSS; recorded under discarded with this reasoning."
```

**Enum vs. free prose, decided per field, not by default:** `source.who`, `harm`, `attack_surface` reuse the exact `Source`/`Harm`/`Surface` Literals from `keel/schemas/threat.py` — no parallel vocabulary. `exploitation_complexity` and `risk.likelihood`/`risk.severity` are new narrow Literals (the methodology already calls these out as qualitative low/medium/high judgments); typing them is what makes the "important vs. less important" grouping in the UI reliable — sorting on inconsistent free text wouldn't work. Everything else in a finding (`scenario`, `asset`, `vulnerability`, `delta`, `coverage_note`, `discarded[].reason`, `dialogue[].*`) stays free prose, the same split the catalog itself already uses between enum fields and `weakness.text`/`reachability`.

**Requirements stay thin on purpose.** A requirement doesn't restate what a cataloged mitigation does (that's the card's `purpose`/`control_mechanism`) or why it applies to this threat class (that's the threat→mitigation link's `rationale`) — both are one MCP call away by `mitigation_id`. A requirement only records the assessment-specific judgment: is this already covered here, partially, or does it need building — and, for anything not yet in the catalog, the actual ask in `description`.

**No `owner` placeholder for requirements.** The generic methodology's step 11 says "leave an Owner column blank for the system owner to fill in" — but there's no such column in this schema, so there's nowhere for the model to invent a name even by accident. Real accountability data that already exists — a linked mitigation's `Implementation.owner` — is resolved live at render/copy time instead (see Rendering, below), not duplicated into the report.

## System identification

A security specialist assessing dozens of systems won't reliably remember whether "this" is the same system as one assessed months ago. Rather than asking them to recall from an unordered list, step 1 of `assess-genai-with-library` (System context) reads the frontmatter (`system_name`, `system_description`) of every folder under `reports/*/`, compares against the system now being assessed, and — only when something plausibly matches — proposes it ("this looks like `reports/checkout-agent` — same service?") for the specialist to confirm or reject. No fuzzy-matching engine; this is an instruction to the same LLM agent that's already gathering system-context facts in that step.

On a confirmed match, the skill loads that system's most recent report as context and is instructed to assess the delta since then rather than re-deriving every finding from scratch. This is a light instruction addition, not a rewrite of the underlying calibrated methodology (which stays untouched, per the existing two-skill split).

## Handling a sparse/draft catalog

All 71 mitigation cards are currently `status: draft` with mostly empty `owner`/`maintainer`. The report-writing step must not assume a mature catalog: when a requirement's `mitigation_id` resolves to a `status: draft` card, the self-check/with-explanation renderings add a short note ("control definition still in draft") next to it — the bare product-team view omits this, since a product engineer doesn't need Keel's internal catalog-maturity state, only the ask. Empty `owner`/`maintainer` on a resolved mitigation are simply omitted from rendering, matching the omit-if-empty convention already used throughout the UI (e.g. the Ownership section, Implementation cards).

## Rendering and the two product-team views

Three views, all generated from the same report JSON (never a fourth stored format):

1. **Self-check (full).** Everything: `findings` with full chain, `discarded`, `dialogue`, `delta_summary`, each requirement's `coverage_status`/`coverage_note`, `ignored_mitigations` with reasons, plus (live-resolved by `mitigation_id`) each mitigation's `name`, `owner`, `maintainer`, and draft-status note.
2. **Requirements only (product-team default).** For each `finding` marked for inclusion (see below), one line per requirement: the mitigation's `name` (resolved live) or the ad hoc `description`, plus its `owner` (live-resolved) — routing information, not "explanation," so it's in this view too.
3. **Requirements + explanations.** Same list, each line followed by that finding's own `scenario` prose — the terse, system-specific causal chain the user asked for. Deliberately not the catalog's `rationale` text (which explains the control in the abstract, independent of this system) — using the finding's own prose keeps the report self-contained and immune to the catalog's `rationale` text changing after the report was written.

**Inclusion is copy-time, not persisted.** There is no `include_in_export` field on the report. The Reports screen shows a checkbox per requirement when the specialist opens either product-team view, defaulted (survived-and-not-`already_covered` = checked, `already_covered` = unchecked, `discarded` never shown at all) and freely adjustable before hitting Copy. Nothing about that adjustment is saved — the report YAML never changes after the skill writes it, so a completed record can't be reopened to a different edited state days later.

## Backend

- `GET /reports` — list, grouped by `system_id`, most recent report per system for the summary row.
- `GET /reports/{system_id}` — the full series for one system (dates, one-line `delta_summary` if present).
- `GET /reports/{system_id}/{date}` — one report's parsed body.

All read-only; nothing writes through the API — a report is created by the skill via the Write tool, the same way design docs land in `docs/plans/`. `keel validate` does not check `reports/` (it's an assessment archive, not the reference catalog); the read service is defensive instead — a malformed or unparseable file is skipped/flagged in the list response rather than making the whole endpoint fail.

A `keel/schemas/report.py` Pydantic model mirrors the YAML shape above, used only for parsing/validation on read, not for accepting writes.

## UI

A fifth screen, "Reports," alongside Overview/Threats/Mitigations/Style guide — read-only, no draft/save flow, so it's structurally simpler than the Threats/Mitigations editors (no three-pane edit/preview split needed).

- Rail: systems, each with its report dates; picking a date opens that report.
- Detail: renders the self-check view natively, using the same visual language already established (`readsec`-style sections, `.card`/`.badge` components) — findings grouped by `risk.severity` (important vs. less important), `discarded` shown collapsed/de-emphasized at the bottom, `dialogue` as a short Q&A list.
- Two buttons, "Copy requirements" and "Copy requirements + explanations," each building a markdown string client-side from the already-loaded report JSON plus a live mitigation lookup (the same `mitById`-style pattern the Threats screen already uses to show a mitigation's name next to a link) — copied via `navigator.clipboard.writeText`. The inclusion checkboxes described above sit above these buttons.

No style-guide entity for `report` — that machinery exists to guide human/LLM authoring through the generic MCP/UI editing flow, and a report is authored entirely inside the skill's own instructions, not through that flow.

## Testing

Backend: `keel/schemas/report.py` unit tests (enum validation, `description` required iff `mitigation_id` is null, `coverage_note` required iff `coverage_status` is `already_covered`/`partial`, `discarded` entries reject chain fields); `report_service` list/get tests against a temp `reports/` fixture, including a malformed-file-is-skipped-not-fatal case; route tests mirroring the existing REST test style.

Frontend: manual verification via the Browser pane (no JS test harness in this repo) — a sample fixture report renders correctly in the self-check view, both copy buttons produce the expected markdown for a known fixture, the inclusion checkboxes toggle the copy output, and toggling them does not persist across a reload.

The skill instructions themselves (the new system-identification step and the final report-writing step in `assess-genai-with-library`) are not unit-testable — verifying them means running a real or fixture assessment through the skill once implemented and inspecting the resulting `reports/` file, not something pytest covers.
