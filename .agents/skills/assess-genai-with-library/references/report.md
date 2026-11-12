# Report fields

What each field of a saved report holds. Open it when you fill the report at step 10, and at step 3 for the ledger. The schema behind `save_report` refuses what breaks the rules marked *refused*; finalizing waits on what is marked *blocks finalize*.

The tools check what a plain file write cannot: that the report parses, that its grades are on the allowed scale, and that every `mitigation_id` and catalog threat id it names actually exists. A plausible id that resolves to nothing reads as real support and is refused.

## Header

`assessor` comes from `git config user.name` and `user.email`, written as `Name <email>`, the person accountable for the judgments, never the agent. `date` is today. `system_id` and `system_description` come from the identification step.

`extensions` holds data an installed extension keeps, under its name. Leave it as you found it when you save.

## Findings

Per finding: `id` (the catalog threat id, or a new `T-*` id you coin for something the catalog lacks), `from_catalog`, `scenario`, `source` (`who` / `motive` / `access`), `asset`, `attack_surface`, `vulnerability`, `exploitation_complexity`, `harm`, `risk` (`likelihood` / `severity` / `reasoning`), `risk_today`, `delta`, `origin`, `deployment`, `root_cause`, `evidence`, `review`, `requirements`, `ignored_mitigations`.

- `attack_surface` stays empty only when the weakness has no channel (a standing credential); never name one the path does not cross.
- `origin` places the threat against the state before the integration: `new` (it did not exist), `changed` (it existed, and the integration changed its chain; `delta` says what), `legacy` (it existed and the integration changed nothing in it). A legacy threat is kept, graded and given measures like any other; it is only not counted against the integration. No delta is never a reason to drop a threat.
- `deployment` says what is switched on today (`live`, `pilot`, `off`, `not_deployed`); grade the design as it will run, not today's switch.
- `risk_today`: only when `deployment` is not `live`. The grade with today's switch, beside `risk` for the design as it will run, so the risk owner sees both "low now" and "high at launch" (*refused* on a live finding).
- `root_cause` is a short stable slug for the defect, the same across re-assessments and across systems that share it. With `system_id` and `id` it is the finding's fingerprint, and two findings of one report with the same fingerprint are one finding (*refused*). Findings that share a `root_cause` are shown together with the fix that closes them.
- `harm`, `attack_surface` and `source.who` are the catalog's own vocabularies, quote them verbatim.
- `source.motive` and `source.access` answer the methodology's source step for either kind of source: for an attacker, the goal and the real access to the surface; for a source without one (`model-mistake`, `model-overeager`, `error`, `accident`), what triggers it in this system and the permissions it acts with. A source without an attacker still has a trigger, so `motive` is never just "none".
- `likelihood`, `severity` and `exploitation_complexity` are each **low | medium | high**; there is no fourth level. How to pick: [grading.md](grading.md).
- `review`: who tried to refute the finding (`by`), the `verdict` (`stands`, `weakened`), and a `note` of what they checked. Required on every finding with `severity: high` (*blocks finalize*). A refuted finding is not a finding: it moves to `discarded` with `by: review`.

**`risk.reasoning` must be a sentence that stands on its own.** It is pasted straight into a ticket with no label in front of it, so "irreversible money movement, reachable anonymously" fails and "The money movement is irreversible and the path is reachable anonymously" works.

## Requirements

Each requirement is either a catalog control (`mitigation_id` set, `description` omitted) or an ad hoc ask (`mitigation_id: null`, `description` required). **Never invent a `mitigation_id`.** If the library has no card for a control this system clearly needs, that is a wanted outcome, not a gap in your answer: leave `mitigation_id` empty and write the ask in `description`, in one or two sentences, as if proposing it to the library, those are collected on the Overview as what the library is missing. A plausible-looking id that resolves to nothing reads as a cataloged control and is refused on save.

`coverage_status` is `needs_implementation`, `already_covered` or `partial`; the last two **require** a `coverage_note` saying what covers it here, and `needs_implementation` must not carry one. Leave `included` out, it defaults to shipping everything except what is already covered, and the specialist decides the rest. A control linked in the catalog but wrong for this system goes in `ignored_mitigations` with the reason, not into `requirements`.

A requirement that ships (`included`, and not `already_covered`) is something a product team has to build and someone has to accept. Three things make it buildable:

- `invariant`: what must always hold once it is built, in one sentence about this system ("the agent's token cannot push to a protected branch").
- `enforce_at`: the narrowest place it is enforced, the last point the system still trusts before the harm (the CI runner's token scope, not the model's prompt).
- `done_check`: how to tell it is done, best as a test that fails today and passes after the fix, so the gap cannot come back unnoticed.

A catalog card already holds them in general terms: `purpose`, `locus` and `validation`. For a catalog control, fill these fields only with what is specific to this system; save tells you when the card has no `validation`, and then `done_check` here is the only acceptance anyone has, and the card is worth filling. An ask with no card has nothing else to stand on, so it carries all three (*blocks finalize*).

## Discards and paused branches

`discarded` is id + `by` + reason (+ `root_cause` and the `evidence` ids it rests on), never the full chain. By `reachability` (the default): the reason is the threat's `reachability` condition holding here, shown by a fact. By `review`: a reviewer broke a graded finding, and the reason says which link of the chain does not hold, with the fact. A small consequence is not a discard: that threat is live and graded low. Discards stay in the report so the next assessment of this system does not re-derive them; save tells you when a finding matches one from an earlier report, and `delta` then names the new fact.

## Open questions

A question is not a note for later. Each one goes into `open_questions`: `id` (`Q1`, `Q2`…), `question`, `asks_for` (`fact`, or `access` when you know where the fact is and lack the right or the document), `looked_in` (where you looked first and why it did not settle it), `needed_for` (the branch and the step), and `how_to_check`: the exact check that settles it, so the person answering can run it rather than recall it ("list who has write access to the knowledge-base space", a query, a command, a setting to open). A candidate whose grade or discard depends on it goes into `paused` with `waiting_on` and a `note` of what is established so far: no grade, no requirements, no discard.

## Surfaces

The ledger of step 3. Each entry: `id` (`S1`, `S2`…), `kind` (`entry`, `tool`, `data`, `file`), `name`, `where` (the endpoint, tool name, path or flow), `evidence` (where you saw it), and `outcome`: the ids of the findings, discards or paused branches that cross it, or `none` with a `note` saying why nothing reaches harm through it. A surface with no outcome and no note is a surface nobody walked (*blocks finalize*). `found_by: review` marks a surface the reviewer added.

## Evidence

Adapted from lesslop (github.com/slovozaslovo/lesslop, MIT): every claim about the system is either backed by something you checked in this session, or it is not a claim you may grade on. Recalled, "standard", "obvious" and "the code probably" are not checked. If checking is cheap, check now; do not offer to check later.

The proof goes in the report's `evidence` list, not into the prose. Each entry: `id` (1, 2…), `kind` (`read`, `command`, `test`), a verbatim `quote` of the lines or the output, and for a read the `commit`, `path` and `lines` of the exact place (not a file, not a branch), and `repo`, a short name of the repository, when the system spans more than one; for a command or test, the `command`. A `test` entry is a reproduction: the path was run, not only read. A `url` is optional and strict: https, on a host in `evidence_hosts`, containing the commit, anchored at the lines, no query string. Anything else is refused on save, because a link is model output and a planted one can carry data out.

In the prose, a claim carries one marker, `[3]`, and the finding lists the ids it rests on in `evidence`. Keep the sentence readable: one marker per claim, no paths or quotes inline. A finding with no evidence cannot be finalized. A grade-deciding claim you could not check is an open question, not an unmarked sentence.

A stored organisation fact the specialist confirmed in this run (skill step 2) is cited like evidence: write its `ref`, `org:<file>#<fact-id>`, next to the claim, and if it rests on code, copy that code entry into `evidence` as a `read` of your own, checked now. A `ref` that names no stored fact is said back on save. **If a threat is ruled out because of a stored fact, the `discarded` reason names that fact by its `ref`**: a discard that rests on an organisation's word has to say whose word, so that the day the fact stops holding, the discards it carried can be found.

## `meta`, how the run went

This block does not describe the system; it exists so the assessor itself can be improved, and it is the only feedback anyone will get. Fill it honestly, including the parts that make you look bad, a flattering `meta` is worthless.

- `started_at` from step 1, `finished_at` at write time.
- `questions`, the exchanges that actually moved the analysis: what you asked, what came back, what it changed. Not a transcript, and not questions whose answers changed nothing.
- `volunteered`, **facts the specialist gave you that you never asked for.** This is the most valuable line in the report. A question you asked is one the skill already knows to ask; a fact you had to be handed is a hole in the skill, and writing it down is what closes it. If the specialist said "by the way, X" and X mattered, it goes here. Say what would have been wrong without it.
- `critique`, where the specialist told you your reasoning was wrong, in their words, not softened. If a grade moved because you were pushed, that belongs here as well as in `questions`.

Leave a list empty rather than padding it. An empty `volunteered` on a run where the specialist genuinely volunteered nothing is a real signal; an invented entry destroys the only measurement there is.
