---
name: checking-model-coverage
description: Use when new external material arrives — an OWASP or ATLAS update, a CVE, an advisory, an incident writeup, or a whole external taxonomy — and you must decide whether the Keel model already covers it, on both the threat side and the mitigation side, or whether there is a gap.
---

# Checking model coverage

Given incoming material, decide for each distinct item whether the Keel catalog already covers it. External sources carry BOTH threats and mitigations — ATLAS lists techniques *and* mitigations, an OWASP entry has a risk *and* a prevention section, a CVE names a flaw *and* a fix — so first decide what KIND of thing each item is, then coverage-check against the right part of the model.

## What kind of thing is it?
- A **threat / technique / tactic** → check the threats.
- A **mitigation / control / "prevention"** → check the mitigations.
- A **specific tool, patch, or product** that realizes a control → an *implementation* of a mitigation (orgs fill these in; the reference catalog leaves them empty).
- A **mechanism** (prompt injection, a delivery channel) → not its own entry; it lives in a threat's `source`/`references`.
- A **mapping / reference** (an OWASP or ATLAS id) → provenance on the matching entry's `references`.

## The coverage call (per item)
Check against ALL candidates, not just the obvious one, then assign one disposition:
- **Covered** — name the exact existing threat(s)/weakness(es) or mitigation(s).
- **Partial gap** — the entry exists but a specific angle is missing → name it and the precise missing piece (a weakness on a threat; a field or implementation on a mitigation).
- **Genuine gap** — not modeled at all → a new threat, or a new mitigation.
- **Out of scope** — below the defender's altitude (for example, extracting a hosted model's weights is the model provider's concern, not the integrator's).

Prefer the smallest true change: add a weakness to an existing threat, or a mitigation link / implementation to an existing control, before creating a new entry. Map an external impact onto the frozen `harm` values.

## Output
Per item: what kind it is, its disposition, and the exact Keel entry it maps to (or the precise gap). This is a decision, not an edit — authoring a confirmed gap is a separate step.

## Common mistakes
- Only looking at threats. External sources are half mitigations — check both.
- Waving items through as "new"; most incoming material is already covered.
- Missing partial coverage, or turning a mechanism or a control into a threat.
