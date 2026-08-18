---
name: folding-into-the-model
description: Use when adding new information to the Keel model — writing a new threat, weakness, mitigation, or implementation, or changing an existing entry — especially when the correct placement is a judgment call rather than obvious.
---

# Folding into the model

Adding to the Keel model is rarely mechanical: the value is getting the placement right, and much of that is a judgment call. The core discipline — **make the judgment calls visible and get sign-off on the consequential ones, instead of silently deciding.** Communicating your *reasoning* is not enough; communicate your *uncertainty*.

## Surface the judgment calls — don't resolve them silently
When you fold something in, several choices are genuinely debatable. For each, name it, state your lean and why, and flag how confident you are. Do not present a debatable choice as a settled conclusion:
- **New entry vs. change to an existing one** — a new threat, or a new weakness on an existing threat? a new mitigation, or a link/implementation on an existing one? This is usually the biggest call.
- **Which existing entry** it attaches to — two threats can both look plausible; say so.
- **The structured fields that carry modeling judgment** — `component`, `harm`, `nature` (targeted vs. secondary), and whether the thing is actually a **mechanism** (prompt injection, a delivery channel → `source`/`references`) rather than a weakness.
- **Scope / altitude** — is it even inside Keel's defender scope?

If two reasonable modelers would disagree, the human decides, not you.

## Low-risk vs. consequential
- **Additive and reversible** (a new weakness, a mitigation link with a clear rationale): lean toward doing it, but still show the placement reasoning.
- **Consequential — any change to an EXISTING entry's meaning or scope**: retitling a threat, broadening its applicability, re-grading a link's `strength`, deleting. These are not yours to decide silently. Present the change, the why, and the trade-off, and get explicit confirmation *before* writing. Never bury one inside an additive change as a "recommendation."

## Procedure
1. Decide what KIND of thing it is (threat / weakness / mitigation / implementation / mechanism / out-of-scope). A mechanism or an absent control is not a new threat.
2. Draft the smallest true change — prefer extending an existing entry over a near-duplicate.
3. Surface the judgment calls (above): for each grey area, your lean + your uncertainty; for each consequential change, ask.
4. Write the confirmed content through the MCP tools — the style guide is embedded there, so the wording stays on-standard. Keep provenance in `references`.
5. Run `keel validate` afterward.

## Common mistakes (seen when this goes wrong)
- Presenting a debatable placement (new-threat-vs-weakness, which threat, which `component`) as settled. State the fork and your confidence.
- Quietly changing an existing entry — retitling, broadening scope, re-grading `strength` — as a buried "recommendation." Pull it out and ask.
- Resolving "is this a mechanism or a weakness?" silently. It is often the crux — say so.
- Over-confidence. Careful and transparent beats decisive-but-silent.
