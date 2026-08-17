# Report template

**Location:** `threat_model_reports/<YYYY-MM-DD_HHMM>/report.md`

```markdown
# Threat model check — report

**Date:** YYYY-MM-DD HH:MM
**Status:** healthy / needs_attention / unhealthy

## Summary

| Phase | Critical | Major | Minor | Total |
|-------|----------|-------|-------|-------|
| 1 · Deterministic (schema/links/vocab) | X | X | X | X |
| 2 · Content (rubric) | X | X | X | X |
| **Total** | **X** | **X** | **X** | **X** |

## Stats
- Threats: X (X passed, X with issues)
- Mitigations: X (X orphaned — linked by no threat)
- Harm coverage: which of the 5 classes have zero threats (gap)

---

## Critical (must fix)
- [ ] **T-XXX** (check#1 entity typing): weakness names a technique
  - current: "…"
  - expected: "…"
  - reason: FAIL — a technique belongs in `source`/`references`, not `weakness`

## Major (should fix)
- [ ] **T-YYY** (check#5 surface/source): attacker-only source on a threat real without an attacker
  - current: "…"
  - expected: "…"

## Minor (fix when possible)
- [ ] **T-ZZZ** (check#7 references): reference url off-topic
  - current: "…"
  - expected: "…"

---

## Priority order
1. **T-XXX** — one-line reason it is highest priority
2. …
```
