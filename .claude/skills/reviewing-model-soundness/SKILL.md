---
name: reviewing-model-soundness
description: Use when auditing or reviewing a whole Keel threat model for quality — overlapping or duplicate threats, coverage gaps, structure violations, dishonest mitigation strength, or reachability that names a control; before merging a large model edit or a fork.
---

# Reviewing model soundness

A whole-model quality pass for a Keel catalog. Run the automated checks first, then apply judgment to what a machine cannot: overlap, coverage, and honesty. Report findings by category with the file and the fix — advisory, never blocking.

## First, run the automated checks
- `keel validate` — structure, vocabulary, link integrity, plus the advisory warnings (over-graded `gating` links, empty `references`, an unused `nature` field). Read its output before reviewing by hand; do not re-flag what it already catches. Add `--strict` to make warnings fail.
- Per-entry prose quality is the **check-style** skill's job — use it for wording. This skill is about the model as a *set*.

## The semantic checklist (judgment, not mechanical)
Go threat by threat, then across the whole set.

Structure violations (the style guide's rules):
- A technique used as a threat or weakness identity (prompt injection, jailbreak) — it is a mechanism; it belongs in `source`/`references`, never as a title or a short weakness.
- A "weakness" that is really a harm/consequence, or model behaviour ("the model shouldn't…") — model behaviour is never a weakness.
- `reachability` that names a control or just re-negates the weakness — it must be a materiality/reachability carve-out on the *un-mitigated* architecture.

Honesty:
- `strength` matches the control's real nature: only an architectural control that blocks belongs on a `gating` link; detectors, advisory, and best-effort controls are `soft`. A soft link's `rationale` must not claim it closes the threat.
- `source` includes non-attacker causes (error/accident/hallucination) when the threat fires without an attacker.

Coverage and overlap (the set):
- A threat whose mitigations are all soft has no real closure — flag it.
- Two threats covering the same outcome, or the same weakness repeated across threats — decide which threat owns it and demarcate; prefer adding a weakness to an existing threat over a near-duplicate threat.
- Are the harm classes, surfaces, and sources adequately covered, or is there a blind spot?
- Mitigation links with no matching weakness (a control filed under the wrong threat).

## Output
A structured report grouped by category, each finding naming the exact file/entry and the concrete fix, ordered by severity. Findings are advice for a maintainer — never a blocking gate.

## Common mistakes
- Re-listing what `keel validate` already flags. Run it first; spend your attention on judgment.
- Treating advice as blocking. This is a review, not a gate.
- Checking entries one at a time and missing set-level overlap and coverage.
