---
name: folding-into-the-model
description: Use when putting new information into the Keel model, or deciding whether it is already there - writing or changing a threat, weakness, mitigation or implementation, and working through incoming external material (an OWASP or ATLAS update, a CVE, an advisory, a whole taxonomy) to decide what the model already answers and what is a gap.
---

# Folding into the model

Placement is the work. Getting the words right is what the style guide is for; deciding *what kind of thing this is, whether the model already answers it, whether it is one record or two, and where it attaches* is what goes wrong.

Two rules hold the skill together. **Do not write from memory** - a card is a claim about the world, and the evidence for it has to be found, not recalled. **Make the judgment calls visible instead of resolving them silently** - communicating your reasoning is not enough, communicate your uncertainty.

Most of what arrives is already answered somewhere, so the skill starts by finding out. Steps 1 and 2 are often the whole job.

## 1. Decide what kind of thing it is, and whether the model already answers it

Follow [coverage.md](coverage.md). It carries the table of kinds and where each one lands on the chain, the four dispositions, and how to say `out_of_scope` honestly.

It ends in one of two places. **Covered or out of scope:** record the row and stop - the disposition is the output, there is nothing to author. **A gap, whole or partial:** carry on here.

Do not skip this because the subject feels new. Skipping it is what produces a near-duplicate of something that was already in the catalog under another name.

## 2. Research the subject

The step that gets skipped, and the one that shows in the finished card. A card written without it reads as plausible, cites nothing that supports it, and no reviewer can tell it from one written by someone who knew.

Follow [research.md](research.md). It is a procedure with a gate at the end: what you have to find, where to look, and when you are allowed to start writing.

## 3. Decide whether it is one record or part of one

The pivot, and the place where a record goes wrong in a way no amount of good writing repairs.

The style guide carries the test in its **`entity` block** - the bar for the record as a whole, returned by `get_style_guide(entity_type="threat")` or `get_style_guide(entity_type="mitigation")`. A field-scoped call does not return it, so ask for the entity. Read it before you name anything: it also says which decisions come first, and taking them in the wrong order means rewriting the record.

In short. **Threats:** two chains are two threats if and only if ruling one out does not rule out the other, or closing one does not close the other. **Mitigations:** two controls are two cards if and only if an organisation could adopt one without the other.

Run the test out loud. Name the reachability and the gating control you have in mind, then say which existing record they match. A subject that fails the test is a weakness on an existing threat, or a criterion on an existing card - which is also the smaller and better change.

## 4. Write to the bar

Call `get_style_guide(entity_type=..., field_name=...)` for each field as you write it. One field at a time is far cheaper than the whole entity, and the bar it returns is what the entry will be reviewed against.

Write the card against the control or the chain, never against the one threat that prompted it. A card that carries the shape of its first occasion is not reusable for the second.

## 5. Say what was debatable

For each of these, name the fork, state your lean, and say how confident you are:

- **New record or a change to an existing one.** Usually the biggest call, and step 3 is where you made it.
- **Which record it attaches to**, when two are plausible.
- **The fields that carry modelling judgment:** `component`, `surface`, `harm`, `nature`, and a link's `strength`.
- **Whether it is in scope at all**, if step 1 did not settle it.
- **What the research did not find.** Absence of evidence is a finding, and it changes how much weight the card can carry.

If two reasonable modellers would disagree, the human decides.

## 6. Ask before changing meaning

Additive and reversible - a new weakness, a link with a clear rationale - lean toward doing it, and still show the reasoning.

Changing what an existing entry means is not yours to decide: retitling a threat, widening its applicability, re-grading a link's `strength`, splitting or merging records, deleting anything. Present the change, the why and the trade-off, and get an explicit yes before writing. Never bury one inside an additive change as a "recommendation".

## 7. Read what the write returns, then get it judged

Every write answers with what it broke. A `problems` key means this write left the catalog inconsistent - a link pointing at nothing, a `gating` grade on a control that does not block, a coverage row still claiming something you deleted. Fix it in the same turn. No `problems` key means there is nothing structural to fix.

That is the deterministic half only. Run the `check-style` skill on what you just wrote before you report it as done. It is the half that reads the card against its bar, and it is not optional because you feel good about the card.

## Where this goes wrong

- Treating a subject as new without checking. Most incoming material is already answered, often on a part of the chain you were not looking at.
- Writing from memory, then adding a plausible-looking reference afterwards. The reference decides the card, not the other way round.
- Presenting a debatable placement as settled. State the fork and your confidence.
- Skipping the splitting test and producing an umbrella - one record covering several chains closed by different controls.
- Naming a card after the threat it was written for, which makes it unusable for the next one.
- Using `out_of_scope` for anything unfamiliar, which quietly turns Keel's boundary into a list of things nobody looked at.
- Quietly widening an existing entry's scope as a buried "recommendation". Pull it out and ask.
- Reporting the entry as done on the strength of a clean `keel validate`. That gate cannot read a sentence.
