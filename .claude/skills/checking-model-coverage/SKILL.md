---
name: checking-model-coverage
description: Use when new external threat intel arrives — an OWASP or ATLAS update, an advisory, a CVE, an incident writeup, or a whole external taxonomy — and you must decide whether the Keel model already covers it or there is a genuine gap to add.
---

# Checking model coverage

Given incoming information, decide for each distinct claim whether the Keel catalog already covers it, and author only what is genuinely missing. The hard part is honest *partial* coverage — the general threat exists but a specific angle is missing.

## The method
For each distinct claim in the incoming material:

1. Check it against ALL threats, not just the obvious one. Read the candidates' weaknesses; a claim often lands on a threat you did not expect (a poisoning claim → an integrity threat, not a disclosure one).
2. Assign exactly one disposition:
   - **Covered** — name the exact threat(s)/weakness(es) that already model it.
   - **Partial gap** — the threat exists but a specific angle is missing → name the threat and the precise missing weakness.
   - **Genuine gap** — not modeled at all → a new threat.
   - **Not a threat** — a *mechanism* (prompt injection, or a delivery channel like hidden instructions in image ALT text) belongs in `source`/`references`; an *absent control* ("missing input validation") is a mitigation, not a threat.
   - **Out of scope** — below the defender's altitude (for example, extracting a hosted model's weights is the model provider's concern, not the integrator's).
3. Prefer the smallest true change. Add a weakness to an existing threat before creating a new threat. Map an external "impact" onto the frozen `harm` values, not a new one.

## Authoring a confirmed gap
Only after the disposition is decided. Write through the MCP tools — the style guide is embedded there, so authoring stays on-standard. Keep provenance: put the external id/url in the threat's `references`. For structure questions while authoring (mechanism vs threat vs weakness vs harm), defer to the style guide.

## Common mistakes
- Waving everything through as "new". Most incoming intel is already covered; duplication is the failure mode.
- Missing *partial* coverage — claiming "covered" when only some of the angles are modeled.
- Turning a mechanism or an absent control into a threat.
