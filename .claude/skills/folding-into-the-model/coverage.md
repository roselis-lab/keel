# Is it already in the model?

Two questions, in this order. What kind of thing is this? And does the catalog already answer it?

Both have to be settled before anything gets written, and for incoming external material they are often the whole job: most of what arrives is already answered somewhere.

---

## A. What kind of thing is it

An external item almost never lines up one-to-one with a Keel record, and it does not have to. Different kinds land on different parts of the chain, and all of these count as answered.

| The item is | It is answered by |
|---|---|
| A threat, an outcome, a scenario | a **threat** |
| A weakness, or a technique that exploits one | a **weakness** inside a threat, so the answering id is that threat |
| A control, a "prevention", a hardening measure | a **mitigation** |
| A technique for defeating a control - obfuscation, a split payload, a lookalike | the **acceptance criteria** of the control that has to survive it, so the answering id is that mitigation |
| An impact or an exfiltration route | the **harm** of a threat that lands there |
| A specific tool, patch or product | an **implementation** of a mitigation. The shared catalog leaves these empty; orgs fill them in |
| A mechanism - prompt injection, a poisoned document | not a record. It is a weakness's `surface` and the threat's `source` |
| A consequence - a fine, a rollback, a headline | already carried by `harm`. The story of one incident belongs in an assessment |
| An absent control - "there is no rate limit" | a mitigation, or an ad hoc requirement on an assessment. It is a weakness only when it names an architectural condition |
| Something org-specific - who owns it, how our company does it | an `Implementation`, never a card's prose |
| A mapping or an id - "LLM01", "AML.T0051" | provenance. It belongs in the coverage matrix, never as a `reference` |

Two rows are easy to miss and between them account for a large share of a taxonomy like ATLAS. A technique that defeats a detector is answered by the detector's criteria. An item that is purely an impact is answered by the threat whose `harm` it is. Recording either as a gap is the common error.

External sources mix kinds freely. ATLAS lists techniques *and* mitigations, an OWASP entry has a risk section *and* a prevention section, a CVE names a flaw *and* a fix. Checking a control against the threat list is how an answered item gets recorded as a gap.

`get_model()` returns the same list as `not_modelled`, if you want it from the server.

---

## B. Does the catalog already answer it

1. `search(q)` with two or three phrasings. It covers threats, mitigation cards, coverage rows and past assessments in one query, so you do not have to guess which kind the answer is.
2. `get_coverage(source_id=..., state=...)` if a tracked source names it. A row already marked `covered` or `out_of_scope` means the decision is taken; read it before reopening it.
3. `get_style_guide` and `get_model()` if the placement is still not obvious.

Check every candidate, not the obvious one, then assign one of four:

- **Covered.** Name the exact record, and which part of it answers the item: the threat, a named weakness inside it, the control, or a criterion on the control.
- **Partial gap.** The record exists, a specific angle is missing. Name both the record and the precise missing piece.
- **Genuine gap.** Not modelled anywhere.
- **Out of scope.** Keel does not model this at all, and here is where the line falls.

Prefer the smallest true answer. A weakness on an existing threat, or a criterion on an existing control, before a new record.

### Where this ends

**Covered or out of scope:** record the row and stop. There is nothing to author, and the useful output is the disposition itself.

**Partial or genuine gap:** carry on with the rest of the skill. This is the confirmed gap that authoring exists for.

---

## Out of scope, said honestly

The state that earns trust, and the one most easily abused. It describes Keel's boundary, never a disagreement with the source.

The legitimate case is an item with no component of ours and nothing we could do about it: the attacker's own preparation on their own infrastructure - acquiring infrastructure, registering accounts, building a surrogate model, reading public research. There is nothing to place a control on.

It is **not** the right state for an item that merely looks unfamiliar. Reconnaissance against our system usually is impedable: not echoing a model's version and family, rate-limiting inference, not returning confidence scores, watching what gets published in public repositories. Those are controls. They carry no harm of their own, so they attach to the threats they slow down with `strength: soft` - which is what `soft` is for, and the correct answer for a large part of a technique taxonomy.

It is also not the right state for something Keel answers in a different shape. That is `covered`, and the shape is explained in the record's `positioning`.

When a whole block goes out of scope, give every row the same reason in the same words. Thirty-eight separate excuses read as evasion; one boundary applied consistently reads as a decision.

---

## Writing the rows

`set_coverage_entry`. A `covered` row carries no note: why a record answers a source is a property of the record and lives in its `positioning`, because a note here goes stale the moment a second id joins the row. A `gap` may carry a note saying what it is waiting on. An `out_of_scope` row must carry one.

For a batch - a whole release, a taxonomy - say once what a shared disposition is and list the refs under it, rather than repeating yourself per row. Report both numbers: how many rows you decided, out of how many the release has. A matrix showing twelve rows of a hundred-and-one-entry release reads as complete.
