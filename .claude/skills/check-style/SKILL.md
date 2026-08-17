---
name: check-style
description: Use when reviewing the CONTENT quality of Keel threat entries against the style guide — after authoring or migrating a threat, or auditing the catalog's writing. Judgement-based (LLM), applies the per-field authoring bar; does not own the rules (the style guide does). Triggers "check style", "content review", "is this threat authored right", "authoring quality", "review threats". For structural checks (schema/links/vocab) run `keel validate` instead — this skill assumes structure is already valid.
---

## Overview

Reviews the **content quality** of threat entries against the **style guide** — the per-field authoring bar (`purpose` / `content_requirements` / `avoid` / `examples`), which is the single, forkable source of truth.

This skill **applies** the bar; it does not encode the rules. If a field is wrong but the bar is silent, the fix is to the **style guide**, not the entry.

Judgement-based → uses LLM review agents, run on demand while authoring. It is **not** the deterministic structural check.

## Precondition — structure must be valid

Run the deterministic gate first:

```
uv run keel validate
```

That covers schema, link integrity, frozen vocabularies, URL references, and the lint invariants (≥1 `gating` mitigation for a blockable threat; no technique as a `title`/`weakness`/`harm`). If it fails, fix structure before reviewing content — content-reviewing a broken entry wastes the pass.

## Review

For each threat in scope, dispatch review agents **in parallel** (~4–5 threats per agent), following **[rubric.md](rubric.md)** — the *procedure*, not the rules:

1. `get_style_guide(entity_type="threat")` (+ `weakness`, `mitigation_link`) → each field's bar.
2. Rate each field with content **PASS / MINOR / FAIL** against *its own bar*.
3. Apply the two **judgement invariants** that no single field's bar can hold (reachability ↔ targeted-weakness coherence; source completeness).

Output line:
```
THREAT_ID | field | PASS/MINOR/FAIL | current | expected (per bar) | reason
```

## Report

Write `threat_model_reports/<YYYY-MM-DD_HHMM>/report.md` ([report-template.md](report-template.md)). Present status + counts + top-3 priorities.

## Severity

| Severity | Criteria (content) |
|----------|--------------------|
| **critical** | A field badly violates its bar with security impact — e.g. `weakness` names a technique or a consequence; `reachability` re-negates the weakness or points at a control; a `soft` mitigation's rationale claims it closes the threat |
| **major** | Vague/non-architectural `weakness` text; wrong `nature`; attacker-only `source` where the threat is real without an attacker; thin `reachability` |
| **minor** | Wording, title format, tag hygiene, reference relevance |

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Re-encoding rules in the review | Fetch them from the style guide; if missing there, fix the bar |
| Reviewing a structurally-broken entry | Run `keel validate` first |
| "Good enough" verdict | PASS or FAIL — MINOR is a real defect, not a hedge |
| No `current` / `expected` | A fix skill can't act on it — always include both |
