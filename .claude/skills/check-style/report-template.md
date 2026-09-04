# Report template

For the audit mode only. A single-entry review after a write is answered in the reply, not written to a file.

**Location:** the path the caller names. Do not invent one, and do not write into `reports/` - that directory is assessments of real systems, written through `create_report`, and a catalog review is not one.

```markdown
# Catalog content review

**Date:** YYYY-MM-DD HH:MM
**Scope:** which entries were reviewed
**Status:** healthy / needs_attention / unhealthy

## Summary

| | Critical | Major | Minor | Total |
|---|---|---|---|---|
| Per field (rubric A) | X | X | X | X |
| Record level (rubric B) | X | X | X | X |
| Against the style guide itself | X | X | X | X |
| **Total** | **X** | **X** | **X** | **X** |

The third row is not a defect in the catalog. It is a rule the bar does not carry yet,
found by trying to apply it, and it is fixed with `update_style_guide`.

## Stats

- Threats reviewed: X (X pass, X fail)
- Mitigations reviewed: X (X pass, X fail)
- Records flagged as one that should be two, or two that should be one: X

---

## Critical

- [ ] **T-XXX** (B1, one record): covers two chains closed by different controls
  - current: "..."
  - expected: "..."
  - reason: FAIL - ruling out one does not rule out the other, so reachability is true of neither

## Major

- [ ] **CTRL-YYY** (A, scope): written against the threat it was created for
  - current: "..."
  - expected: "..."
  - reason: ...

## Minor

- [ ] **T-ZZZ** (A, references): the note identifies the source instead of saying what it supports
  - current: "..."
  - expected: "..."

## Against the style guide

- [ ] **mitigation.telemetry**: the bar does not say whether an event list may be empty
  - what was hit: ...
  - what the bar should require: ...

---

## Priority order

1. **T-XXX** - one line on why it is highest
2. ...
```
