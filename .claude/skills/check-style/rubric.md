# Review procedure - judge an entry against the style guide

**The authoring rules are NOT in this file.** They live in the style guide, the single forkable source of truth. This file is only *how to apply* them, plus the record-level checks that no single field's bar can express. Re-encoding field rules here would create a second source of truth that drifts from the guide.

---

## A. Per field

For the entry under review:

1. Fetch the bar. A threat: `get_style_guide(entity_type="threat")`, plus `weakness` and `mitigation_link` for its sub-entities. A mitigation: `get_style_guide(entity_type="mitigation")`, plus `implementation`. Each field returns `purpose`, `content_requirements`, `instructions`, `avoid`, `examples`.
2. For every field that has content, rate **PASS / MINOR / FAIL** against *its own bar*. Nothing invented here.
3. If the content is wrong and the bar is **silent** on the rule, the finding is a style-guide gap. Report it against the bar, and say what the bar should require.

Output line:

```
ENTRY_ID | field | PASS/MINOR/FAIL | current | expected (per bar) | reason
```

Two traps worth naming, because both produce a PASS that should not be one.

**Reading the bar loosely.** The bar says what the text must contain. A field that gestures at the requirement without meeting it is a FAIL, not a MINOR.

**Reading a field in isolation when its bar names another field.** Several bars draw a boundary against a neighbour - `scope` against `control_mechanism`, `out_of_scope` against `reachability`, `anti_patterns` against `validation`. Check the boundary held, not just that the field says something.

---

## B. Record level

These need the whole entry read at once. They are where the expensive mistakes are, and none of them can be a per-field bar.

**1. Is this one record?** The test is in the style guide's `entity` block, returned by `get_style_guide(entity_type=...)` without a field name. That block is the bar for section B as a whole - read it first, and check the record against every line of it, not only the test.

For a threat: are there two chains here that are ruled out by different conditions, or closed by different controls? If so it is an umbrella, and that is critical - no wording fixes it, and every field below it inherits the fault, because `reachability` will be true of neither half.

For a mitigation: could an organisation adopt half of this card without the other half? If so it is two controls in one.

The mirror also fails. A record that duplicates one already in the catalog - same harm, same gating control, no stated difference in what rules it out - should have been a weakness or a criterion on the existing one. `keel validate` flags the clear case as `merge_candidate`; this check catches the ones it cannot see.

**2. Is the record written against itself, or against its first occasion?** A mitigation named or scoped for the threat it was created against is critical: it will not link to a second threat without reading oddly, so the same control gets written twice under two names. The same fault on a threat looks like a `reachability` that only makes sense for one deployment.

**3. Reachability against weaknesses.** Closing any `targeted` weakness should make the `reachability` carve-out fire. If it does not, the pair is incoherent - either the weakness is not really targeted, or the carve-out is describing something else.

**4. Source completeness.** If the threat is real without an attacker, `source` must include the non-attacker cause: `hallucination`, `error` or `accident`. An attacker-only source on a threat that fires from a plain model mistake understates it.

**5. Surface against weakness.** A weakness about content crossing into a component names the channel. A weakness about the component's own authority names none - and a channel put there anyway is a wrong answer in a field readers filter on. Check the two agree with the text.

**6. Evidence.** The one that catches a card written from memory, and the reason a fluent entry can still fail. For each `references` entry: does the note say what the source *supports*, and does the source actually support the claim the card makes? A note that only identifies the source ("this is LLM01", "a paper about agents") is not evidence, and a framework mapping is a duplicate of the coverage matrix rather than a reference at all.

A card asserting that something happens in practice, with nothing behind it, is critical. A card whose references were plainly found after the fact reads the same way: the notes describe the sources instead of supporting the sentences.

**7. Org-specific prose.** Anything of the form "the organisation decides", "depending on your risk appetite", "teams should choose" does not belong in a card field. It belongs in `implementations`, or nowhere. Major.

---

## Verdict

**PASS** - every populated field PASS, and every record-level check holds.

**FAIL** - any critical, or two or more major.

State the verdict explicitly. A review that ends in a summary without a verdict is the "good enough" hedge under another name.
