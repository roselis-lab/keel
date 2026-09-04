---
name: check-style
description: Use to judge a Keel entry against the style guide - a threat or a mitigation card - after writing or changing one, or when auditing the catalog's content. Not for structural checks (schema, links, vocabularies), which are `keel validate`.
---

# check-style

Judges the **content** of an entry against the **style guide**: the per-field bar, and the few things about a record that no single field's bar can hold.

This skill *applies* the bar, it does not own it. If a field is wrong and the bar is silent, the finding is against the **bar**, and the fix is `update_style_guide`, not a patch to the entry. Re-encoding rules here would create a second source of truth that drifts.

Judgment, not structure. The deterministic gate - schema, links, vocabularies, rules - is `uv run keel validate` and `check_library_health`. Assume it passed. It cannot read a sentence, which is the whole reason this exists.

## Two modes

**One entry, after a write.** The default, and the one that matters. Run it on whatever you just created or changed, in the same turn, before reporting it as done. No agents, no report file: read the entry, apply [rubric.md](rubric.md), give the verdict in the reply.

**The catalog, as an audit.** Dispatch review agents in parallel, four or five entries each, same rubric. Write the collected result using [report-template.md](report-template.md), to a path the caller names.

## Procedure

Both modes run [rubric.md](rubric.md). In short:

1. Fetch the bar. `get_style_guide(entity_type="threat")` plus `weakness` and `mitigation_link`, or `get_style_guide(entity_type="mitigation")` plus `implementation`.
2. Rate every populated field **PASS / MINOR / FAIL** against *its own bar*.
3. Apply the record-level checks in rubric section B - the ones that need reading the whole entry.

```
ENTRY_ID | field | PASS/MINOR/FAIL | current | expected (per bar) | reason
```

`current` and `expected` are not optional. A finding without both cannot be acted on by anyone but its author.

## Severity

| | Criteria |
|---|---|
| **critical** | The record is the wrong shape: an umbrella covering chains closed by different controls, a card named after the threat that prompted it, a technique or a consequence sitting in `weakness`, `reachability` that re-negates the weakness or names a control, a `soft` link claiming it closes the threat, a card with no evidence behind a claim that needs it |
| **major** | A vague or non-architectural `weakness`, a wrong `nature`, an attacker-only `source` on a threat that is real without one, thin `reachability`, `scope` written against one threat, org-specific prose in a card field, acceptance criteria that no reviewer could check |
| **minor** | Wording, title phrasing, tags, reference relevance |

## Common mistakes

| Mistake | Fix |
|---|---|
| Re-encoding rules in the review | Fetch them from the style guide; if a rule is missing, the finding is against the bar |
| A "good enough" verdict | PASS or FAIL. MINOR is a defect, not a hedge |
| No `current` or `expected` | Always both, or the finding is unactionable |
| Judging only the fields | The record-level checks in rubric B are where the expensive mistakes are |
| Passing a fluent card | Fluency is what a card written from memory has. Check that the evidence exists and supports what the card claims |
