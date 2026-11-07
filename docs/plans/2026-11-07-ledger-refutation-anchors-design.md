# Surface ledger, refutation, grading anchors and buildable requirements

Design, 2026-11-07. Status: built in this branch, on top of the open-questions and evidence change.

## The problem

A Keel report proves one kind of completeness and not the other. Every catalog threat class is considered, so the report looks thorough, but nothing shows that every surface of the system was walked. A fast run that looked at the obvious entry points reads exactly like a deep one.

Three more gaps sit next to it:

- A `high` rests on the assessor alone. Nobody who did not raise it tries to break it.
- Grades drift between reports. Without anchors one assessor's `high` is another's `medium`, and "unlikely" gets written where the truth is "not checked".
- A requirement is a card id. The product team gets a control name with no statement of what must hold, where, or how anyone will know it is done.

And a discard only lived inside one report: nothing stopped the next run from raising again what an earlier one had ruled out, which is the point of recording why a threat does not apply.

## Decisions

### Surface ledger

- The report gets `surfaces`: every entry point, tool, data path, and the files read to establish them, each with where it is and the evidence it was seen in.
- Every row ends with an outcome: the findings, discards or paused branches that cross it, or a note saying why nothing reaches harm through it.
- Finalizing waits for a ledger, and for every row to be walked. Save refuses an outcome that names a branch the report does not have.

The catalog proves every class was considered; the ledger proves every surface was walked. A report needs both.

### Refutation of high findings

- Every finding graded `high` on severity gets a `review` from someone who did not raise it: a fresh subagent with its own brief, or the specialist.
- The reviewer gets the finding, its evidence and the code, not the assessor's trail. It re-reads every cited line, tries to break each link of the chain with a fact, and lists surfaces the ledger missed.
- `stands` and `weakened` are recorded on the finding. A refuted finding is ruled out: it joins `discarded` with `by: review` and the link that broke. There is one list of what was ruled out, and two reasons a thing gets on it.
- A later save whose finding matches anything an earlier report of the same system ruled out, by reachability or in review, gets advice: name the new fact, or drop it.
- Only `high` is required, because a refutation costs a fresh agent per finding and a wrong `high` costs the most: it is what turns into work for a product team. The skill allows a review on any finding.

### Grading anchors

- A reference file gives each level of severity and likelihood an anchor written in terms of harm and access.
- "Not established" is never written as `low`: a fact that decides reachability is an open question, and an unverified control is left out of the grade.
- A control in the path is either defeated (no change to the grade) or weakened (likelihood down one level at most, and the second failure named).
- A finding on a feature that is not live carries both grades: `risk` for the design as it will run, `risk_today` for today's switch. Save refuses `risk_today` on a live finding.

### Requirements a team can build

A catalog card already says what a control holds (`purpose`), where (`locus`) and how it is accepted (`validation`). Most cards have these unwritten, which is catalog work, not report work. A requirement can carry the same three for this system: `invariant`, `enforce_at`, `done_check`. For a catalog control they are optional, and save advises when the card has no `validation`. An ask with no card has nothing else to stand on, so finalizing waits for all three. The hand-off text includes them.

### Legacy threats

A threat that existed before the integration and that the integration did not change is marked `origin: legacy`. It stays in the report with its grade and measures, because the problem is real whoever introduced it; it is only not counted against the integration. The methodology says so in its delta step, and its self-check refuses a threat dropped for having no delta.

### Smaller pieces

- Open questions get `how_to_check`: the exact check that settles them, so whoever answers runs it rather than recalls it.
- One fingerprint (system, threat id, root cause) is one finding; save refuses a duplicate. Findings that share a root cause show it on the card, so one fix visibly closes several.
- A finding backed by a `test` evidence entry is shown as reproduced. The skill asks for a reproduction where one is cheap and safe.

### Skill structure

The library skill had grown to one file of about 2,700 words, half of it field reference needed only at the last step. It is now a ten-step file with three references opened at the step that needs them: report fields, grading anchors, and the reviewer's brief. Every sentence of the old file is present in the new set; a script checked that before the new material was added.

The methodology skill keeps its steps in one file, because every run needs every step. Its description now lists only when to use it, and its corrections section, which mostly repeated the steps, is folded into the steps it corrects.

## Out of this change

- Static publishing of reports and the catalog for teams that keep Keel in their own Git. That is the documentation and adoption change.

## How we will know it worked

Re-run two or three systems with the new skill. Expected:

- every report has a ledger with no unwalked rows;
- every `high` has a review;
- every shipped requirement says what must hold, where, and how to check it;
- no grade reads "unlikely" where the reasoning says "not established".

A report that took minutes should now show its gaps in the ledger instead of looking finished.
