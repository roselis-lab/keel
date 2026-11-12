# Against OWASP, ATLAS and MAESTRO

Keel builds on all three and reuses their framing. The coverage table below is how it says so.

They give you a shared language and stop there, which leaves both of the problems in [Why Keel is built this way](why-keel.md#two-problems) standing.

| | Against the first problem: is it reachable here? | Against the second: can I make it mine? |
| --- | --- | --- |
| **OWASP LLM Top 10** | A ranked list that mixes kinds: a mechanism (Prompt Injection, which becomes a threat only once it reaches a real asset through an agent's privileges), a consequence class (Sensitive Information Disclosure), generic software risk (Supply Chain), and a teaching trap (System Prompt Leakage treats the system prompt as a security boundary). Nothing in it decides applicability. | Prose, not records. There is no slot anywhere in it for your architecture, so adapting it means rewriting it. |
| **MITRE ATLAS** | Adversary-side and a catalogue rather than a procedure. It tells you what has been done to systems like yours; it cannot tell you whether any of it is reachable in yours. | Machine-readable and genuinely reusable, which is why all 129 of its techniques are decided in the table below. It carries its own mitigations, but no slot for the one you actually built. |
| **CSA MAESTRO** | An architectural map you read, with no rule for deciding what applies to the system in front of you. Overkill for a single-agent, single-tool setup. | A methodology, so a fork is a document. |

Keel's answer to the first problem is `reachability` on every threat and an assessor that walks it, returning findings marked as from the catalog or not.

Its answer to the second is that the model is YAML in git, `implementations` is a layer of its own so the shared card and your build move on different clocks, and the style guide, the record-level rules and the review skill are what keep a fork from decaying.

It also separates what OWASP conflates: a mechanism becomes a finding only once it reaches a real asset. And it stays small, so a single-agent setup does not pay for a layered methodology.

## Coverage

Counts as of 12 November 2026. The site's coverage page and `get_coverage` give the live rows.

Each pinned release is checked against its publisher every Monday by the [coverage freshness workflow](../.github/workflows/coverage-freshness.yml). A source that moved on gets one GitHub issue saying what changed - for ATLAS, which techniques are new - and the matrix stays as it is until someone maps the new release. How each publisher is asked is written at the top of [scripts/coverage_freshness.py](../scripts/coverage_freshness.py).


Every entry of a pinned release gets a row whether or not Keel answers it. A matrix built outwards from Keel's own content could only ever show what Keel already has, never what is missing.

| Source | Rows | Covered | Out of scope, with reasoning | Gap |
| --- | ---: | ---: | ---: | ---: |
| OWASP Top 10 for LLM Applications 2025 | 10 | 10 | 0 | 0 |
| OWASP Top 10 for Agentic Applications 2026 | 10 | 10 | 0 | 0 |
| OWASP MCP Top 10 v0.1 (beta) | 10 | 10 | 0 | 0 |
| MITRE ATLAS 2026.10 | 129 | 80 | 24 | 25 |
| Google SAIF risk map | 15 | 9 | 4 | 2 |
| **Total** | **174** | **119** | **28** | **27** |

ATLAS rows carry ATLAS's own maturity for each technique: 80 Realized (used by a threat actor in a real-world incident), 40 Demonstrated (red team exercise or demonstration on a realistic system), 9 Feasible (research only). The coverage page filters on it, so "seen in real attacks" and "shown only in research or an exercise" can be read apart. The OWASP lists and SAIF publish nothing comparable, so their rows carry none; a label written by hand would be a guess presented as the source's.

A row is one of three things, and the second is not a polite way of saying the third. `covered` names the records that answer it, sometimes in a shape of its own, which the note explains. `out_of_scope` carries the reasoning for why Keel deliberately does not answer it. `gap` is an admission.

`get_coverage` returns the live rows. Check it before concluding something is missing: both of the first two read like omissions if you only search the catalog.
