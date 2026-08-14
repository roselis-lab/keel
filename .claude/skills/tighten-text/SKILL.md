---
name: tighten-text
description: "Tightens English security/assessment prose produced in this repo — threat assessments, the analysis trail, mitigation writeups — into dense expert writing. Cuts filler, hedges, intensifiers, bureaucratese, nominalizations, passive voice, and tangled syntax; never touches substance. Returns edited text, a compression figure, and a rule-linked breakdown. Use on 'tighten', 'make it shorter', 'cut the fluff', 'too much text', 'polish this assessment', 'clean up the writeup'."
---

# Tightening security/assessment prose

An execution skill: it edits a given text. Tuned for this repo's output — GenAI threat assessments and library prose — where **precision beats brevity**. Principles are inline; nothing external is required.

## Scope

**Does:** removes language clutter and de-bullets a chain into connected expert prose, without touching meaning. Typical result — minus 20–40%.

**Doesn't, by default:** doesn't add facts absent from the source; doesn't change the assessment's structure or verdicts; doesn't invent findings.

**The one hard guardrail — never cut substance.** Tighten the *voice*, not the content. The following are load-bearing and MUST survive verbatim in meaning: risk levels ("critical/high/low" are levels, not evaluations to delete), HARD vs SOFT distinctions, GATE ITEMS / stated uncertainty (a hedge that marks an honest missing fact is not filler — keep it), the delta (MITRE ATLAS framing), refutation/"NOT applicable if" reasoning, asset/attacker/surface/scenario specifics, and every domain term. Removing honest uncertainty to sound confident is a defect, not an improvement.

## Procedure

Passes in strict order, bottom-up. Because this is security prose, only the precision-safe passes run by default: **P1, P3, P5, P7** (and P0/P9/P10). The meaning-touching passes (P2, P4, P6, P8) run only with `--hard` and always flag rather than guess.

**P0. Reader, goal, inventory.** Identify the genre and list the protected elements (above). Note the four parameters if they matter: who reads it, what they already know, the goal, the cost of an error. If a needed one is missing, ask once as a block and stop.

**P1. Filler & throat-clearing.** Stating the obvious, appeals to your own opinion, false candor ("it's worth noting", "to be honest"), needless qualifiers, verbal enumeration, needless "for example", "by the way", empty parentheticals, AI signposting ("Let's dive in", "In summary"). Marker — paired commas/dashes/parentheses at a sentence start.

**P3. Clichés & bureaucratese.** Compress a cliché to a word; collapse bureaucratic phrasing to a verb; delete time-filler.

**P5. Action (nominalizations & passive).** Collapse "provide / perform / carry out + a nominalization" into a verb ("performs execution of" → "executes"). Flip passive to active, except when describing a state.

**P7. Syntax & de-bullet.** Split run-ons with a period; break nested subordination; one idea per sentence (up to three in technical writing). **De-bullet:** when a bulleted chain encodes step logic (X → Y because Z → impact), render it as one connected scenario sentence, not a field dump — unless the list is a genuine enumeration (then keep it as a list).

**P2 / P4 / P6 / P8 (only with `--hard`).** Intensifiers (delete); an evaluation with no supporting fact (drop + `[FACT]`); fancy word → plain **only if** meaning fully matches (else `[TERM]`); vague quantifier → figure (`[UNSOURCED]` if no source); a string of synonyms → the single precise term (never cut a list that proves the point).

**P9. Read-aloud check.** Read the whole result. A stumble, an unnatural seam, a lost connective, a dropped nuance — go back. Formally correct is not the same as alive, and shorter is not the same as complete.

**P10. Report** per the format below.

## What we never touch

Numbers, dates, amounts, units; names, titles, orgs, links; domain terms and their exact wording; direct quotes; risk levels and HARD/SOFT tags; GATE ITEMS and stated uncertainty; legally significant wording (may simplify, not drop — `[LEGAL]`); caveats/warnings that protect the reader (never drop silently — `[CAVEAT]`); what makes the text actionable (what to do, by when, whom to contact).

## Modes

| Flag | Behavior |
|---|---|
| default | P1, P3, P5, P7 + P0/P9/P10 — precision-safe clutter and de-bulleting only |
| `--hard` | plus P2/P4/P6/P8 (meaning-touching), always flagging rather than guessing |
| `--analyze-only` | text not rewritten; returns found problems with quotes; P0 ask skipped |

## Report flags

`[FACT]` evaluation removed, no replacing fact · `[UNSOURCED]` claim with no source · `[TERM]` left un-simplified for precision · `[LEGAL]` legal wording touched · `[CAVEAT]` formal detail kept · `[STRUCTURE]` text-level problem, not word-level · `[AUDIENCE]` call depends on what the reader knows.

## Output format

```
## Result
<edited text, no marks, ready to copy>

## Compression
Was: N words / M chars → Now: N₂ / M₂  (−X% / −Y%)

## Breakdown
| Was | Now | Rule |
|---|---|---|
| <fragment> | <fragment or "deleted"> | <rule> |

## Needs your decision
- [FACT] "<fragment>" — evaluation "<word>" removed, a fact is needed
```

Group the breakdown by rule with counts ("filler — deleted 11"); show separate lines only for decided edits. If compression came out under 10% — say so and name the reason (already clean / all facts / the problem is structure, not words). Empty after cleaning is a diagnosis, not a failure — say the source had no substance.
