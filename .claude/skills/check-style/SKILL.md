---
name: check-style
description: Use when reviewing the content quality of a Keel threat entry — after authoring or migrating a threat, or auditing the catalog's writing. Not for structural checks (schema, links, vocab), which are `keel validate`.
---

# check-style

## Overview

Reviews the **content** of a threat against the **style guide** — the per-field authoring bar and the single source of truth. This skill *applies* the bar; it does not own the rules. If a field is wrong but the bar is silent, fix the **bar**, not the entry.

Judgement, not structure. The deterministic gate (schema, links, vocab, lints) is `keel validate`, run separately in CI. Assume it already passed.

## Review

Dispatch review agents in parallel (~4–5 threats each). **REQUIRED:** each agent follows [rubric.md](rubric.md) — the procedure, not the rules. In short:

1. `get_style_guide(entity_type="threat")` (+ `weakness`, `mitigation_link`) → each field's bar.
2. Rate each populated field **PASS / MINOR / FAIL** against *its own bar*.
3. Apply the two judgement invariants no single field's bar can hold (rubric §B).

```
THREAT_ID | field | PASS/MINOR/FAIL | current | expected (per bar) | reason
```

## Report

Write `threat_model_reports/<YYYY-MM-DD_HHMM>/report.md` ([report-template.md](report-template.md)): status, counts, top-3 priorities.

## Severity

| | Criteria |
|---|---|
| **critical** | A field badly breaks its bar with security impact — a technique or consequence sitting in `weakness`; `reachability` that re-negates the weakness or names a control; a `soft` link claiming it closes the threat |
| **major** | Vague/non-architectural `weakness`; wrong `nature`; attacker-only `source` on a threat real without an attacker; thin `reachability` |
| **minor** | Wording, title, tags, reference relevance |

## Common mistakes

| Mistake | Fix |
|---|---|
| Re-encoding rules in the review | Fetch them from the style guide; if missing, fix the bar |
| "Good enough" verdict | PASS or FAIL — MINOR is a defect, not a hedge |
| No `current` / `expected` | A fix skill can't act on it — always include both |
