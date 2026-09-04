# Keel

**A framework for building and running your own living GenAI/LLM threat model.** It ships with a working reference model and an assessor that runs against real systems.

[![CI](https://github.com/roselis-lab/keel/actions/workflows/ci.yml/badge.svg)](https://github.com/roselis-lab/keel/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A keel is the single load-bearing member that keeps a hull upright and on course with the least material. That is the goal here too: the smallest opinionated structure that holds a GenAI threat model together and keeps an assessment on course.

<p align="center"><img src="docs/img/ui-preview.svg" alt="Keel's review-first UI: the three-pane threat editor" width="860"></p>

## The problem

The public GenAI threat corpora, OWASP LLM Top 10, MITRE ATLAS, and CSA MAESTRO, are references you read. They are taxonomies, adversary knowledge bases, and layered methodologies. None of them is a model you can run against a specific system, and none adapts to your organization without a large manual lift. So every team re-derives the same threats from scratch, in prose, inconsistently, and ends up with a document that ages on a wiki instead of a model that takes part in review.

Keel is the operational layer that is missing: a compact, opinionated representation of GenAI threats, a reference model already authored in it, and an assessor that walks a real system against it. All of it is editable, so a team can grow it into their own model.

## What Keel is (three layers)

| Layer | What it is | Role |
| --- | --- | --- |
| **1. Reference model** | 13 threats, 71 mitigations, 96 links, authored in the schema | The seed content: a floor to start from, not the product |
| **2. The framework** | the threat structure (`harm`, `surface`/`source`, `weaknesses`, and `reachability`), the mitigation-card model (class as a switch), a hard authoring style guide, and the machinery to extend it (MCP + REST + browse/edit UI over plain YAML) | What a team adopts and grows into its own model |
| **3. The assessor** | skills that turn the static model into a repeatable pass over a real system (data-sufficiency gate, per-threat chain, delta, two-part output) | What makes the model runnable: read versus run |

The reference model is deliberately small: the catalog is a floor, not a ceiling. Keel's value is the shape and the assessor, not a claim to enumerate every GenAI threat.

## The model

<p align="center"><img src="docs/img/threat-spine.svg" alt="How a threat is assembled: source and surface reach a weakness at a component, the threat rests on it and leads to a harm, ruled out by reachability and addressed by mitigations and implementations" width="860"></p>

Four entities, nothing more:

| Entity | Fields |
| --- | --- |
| **Threat** | `id`, `title`, `harm` (the consequence class, strict enum), `surface[]` (which trust boundary the untrusted influence crosses, enum), `source[]` (who or what drives it, enum), `weaknesses[]` (the predisposing conditions it rests on; see below), `reachability` (carve-outs: *when it is NOT a live path*, judged un-mitigated), `mitigations[]` (links to mitigation cards; see below), `references[]` (`{id, url}` into public catalogs), `tags[]` |
| **Weakness** (embedded in a threat) | `component` (which owned part it sits on, enum), `text` (the architectural condition: cause + where + defect), `nature` (`targeted` \| `secondary`) |
| **MitigationLink** (embedded in a threat) | `id` of the mitigation card, `strength` (`gating` \| `soft`), `rationale` (why it addresses this threat) |
| **Mitigation** (card) | `id`, `name`, `mitigation_class` (a switch: sets how the rest is read), `status`, `purpose`, `scope`, `control_mechanism`, `failure_behavior`, `implementations` (how an org realizes the control; ships empty), plus owner, telemetry, anti-patterns, validation, and FAQ |

Enums:
- `Threat.harm`: `wrong-decision` · `data-exposed` · `code-execution` · `downtime` · `reputation-legal`
- `Threat.surface`: `user-agent` · `agent-agent` · `agent-environment`
- `Threat.source`: `external-attacker` · `internal` · `hallucination` · `error` · `accident` · `training-data`
- `Weakness.component`: `model` · `tool` · `downstream` · `memory` · `knowledge-base` · `identity-store`
- `Weakness.nature`: `targeted` (the attack exploits it directly) · `secondary` (it only amplifies)
- `MitigationLink.strength`: `gating` (an architectural control that blocks the threat) · `soft` (only lowers likelihood)
- `Mitigation.mitigation_class`: `gating_control` · `detector` · `process` · `evidential_mitigation` · `corrective`
- `Mitigation.status`: `draft` · `verified`

A threat rests on one or more weaknesses at the components you own; `surface` and `source` say how untrusted influence reaches them; `harm` is the consequence if it fires; `reachability` is the rule-out gate, used when the path is not live or the asset is not material, judged on the un-mitigated architecture. A technique such as prompt injection is a mechanism, not a threat: it lives in `source` and `references`, never as a threat or weakness identity.

Design principle: **methodology lives in the assessor's prompt, the model stays lean.** Per-system assessment output (actor, scenario, impact, and so on) is ephemeral and is not stored here.

## Get started

Keel is used two ways: to *assess* a system, and to *grow* a shared model with your team. Both start from a local clone.

### Install

```bash
git clone https://github.com/roselis-lab/keel.git
cd keel
uv sync                # install Keel (uses uv; `pip install -e .` works too)
uv run keel validate   # optional: confirm the catalog is valid
```

For the assessment path, point your agent at the repo's `.mcp.json`. It launches Keel over stdio and exposes the tools as `mcp__keel__*`; Claude Code picks it up automatically, so there is no separate server to start.

To open the browse UI (and REST), run the server:

```bash
uv run uvicorn keel.main:app     # UI + REST at http://localhost:8000/
# or: docker compose up          # same UI; add --profile mcp for the HTTP MCP transport on :8001
```

There is no database: Keel reads `catalog/*.yaml` into memory on start, and every write goes straight back to those files as a diff.

### Assess a system

Ask your agent (any agent that has the `.claude/skills/` and the MCP): *"Assess the GenAI security of \<describe your system\>."*

The `assess-genai-with-library` skill walks your system against the catalog: it matches weaknesses, rules out unreachable paths, and checks which mitigations you already have. You get a two-part output: an auditable analysis trail, then a final risk assessment that ties findings to your architecture, separates the controls you have from the gaps, and reports a delta against MITRE ATLAS.

<p align="center"><img src="docs/img/assessment-flow.svg" alt="How an assessment runs: your system to candidate threats to reachability filter to mitigations and implementations to risk to the two-part assessment" width="860"></p>

### Grow the model with your team

Edit the model through the MCP write tools (guided by the style guide), the browse UI (`http://localhost:8000/`, see [Install](#install)), or by editing the YAML by hand. The catalog is a floor: add what your stack needs, adjust cards and rationale, record how your org realizes a control on the mitigation's `implementations` (they ship empty), and prune what does not apply.

The model lives in one shared repo, so every change is a readable YAML diff and ships as a pull request, like any code change. Ask your agent to do it ("commit this and open a PR"), or by hand:

```bash
git checkout -b add-tool-poisoning        # branch; never edit on main
git add catalog/                          # your YAML change
git commit -m "Add threat: tool description poisoning"
git push -u origin add-tool-poisoning
gh pr create --fill                       # open the PR
```

CI runs `keel validate` on every pull request (schema, vocabulary, link integrity, plus advisory warnings), so a broken or off-standard change is caught before a teammate reviews and merges. Everyone works off the same model, and it grows with your systems.

**Roadmap (not yet built):** per-system state to mark a threat *not applicable* for a given deployment or *accept* a risk, so you can suppress known noise without deleting the shared knowledge. Until then, you express that context by editing or pruning the model directly.

## Skills

Keel ships as skills under `.claude/skills/`, in two groups: running an assessment, and working with the model. A deterministic check, `keel validate`, backs both (schema, vocabulary, link integrity, plus advisory warnings).

**Assessing a system**
- **`assessing-genai-security`** is the calibrated, model-agnostic methodology: the data-sufficiency gate, the per-threat chain (source, surface, weakness, scenario, business impact, risk, delta), and the two-part output (analysis trail plus final assessment).
- **`assess-genai-with-library`** binds that methodology to Keel's MCP: candidate threats, a `reachability` match on the target system, then mitigations and whether their `implementations` are actually in place. It polishes the final assessment through `tighten-text` (concision) and `humanizer` (natural voice). Both are substance-preserving.

**Working with the model**
- **`folding-into-the-model`** is the authoring path, and it starts by finding out whether there is anything to author. Given a subject or a piece of incoming external material (an OWASP or ATLAS update, a CVE, an advisory), it decides what kind of thing it is and whether the model already answers it, on the threat side and the mitigation side alike. A covered item ends there, as a row in the coverage matrix. A confirmed gap goes on through a research gate, the test for whether it is one record or part of one, and the per-field bar, surfacing the judgment calls and asking before any consequential change rather than deciding silently.
- **`check-style`** judges what was written against the style guide: the per-field bar, and the record-level checks no single field can carry. This is the content review the deterministic `keel validate` cannot do, and it runs on every entry before the work is reported as done.

## Authoring UI

The browse UI (started in [Install](#install)) is a single static HTML file with no build step, served at `http://localhost:8000/`. A switcher at the top moves between four screens: Overview, Threats, Mitigations, and Style guide.

The interface is review-first. The fastest way to author the model is to ask an LLM to do it through the MCP tools (it drafts to the style guide and writes the YAML for you), and your agent or plain git commits and opens the pull request. The UI writes files and points you to the file to commit; it is not a git client. So the UI's main jobs are reviewing the model at a glance and hands-on edits when you want them; it carries the full create/read/update/delete for both threats and mitigations as a complete fallback.

**Overview** is the landing screen: the counts (threats, mitigations, links), style-guide coverage overall and per entity, and a "gaps to review" list (threats missing a weakness or a harm, threats with no mitigation, dangling links), each with clickable chips that jump straight to the threat. Nothing here blocks anything; it is a place to see where the model is thin.

**Threats** edits one threat at a time in a three-pane layout: the list on the left, the editor in the middle, a live preview on the right. The editor builds its form from the JSON Schema, so the fields, their order, and the fixed-vocabulary dropdowns always match the model. Each section is a clear band; weaknesses, mitigation links, and references show as cards you can add, edit, remove, and collapse. Each field keeps one quiet one-line hint, and the full "how to write this" guidance (what to include, what to avoid, an example you can drop in) lives in the right rail, which flips from Preview to Guidance when a field has focus, so guidance never pushes the form around. Every change is checked on the server through `POST /threats/validate`, which returns two kinds of feedback: red blocking errors when the structure is wrong (a value outside a fixed vocabulary, a missing required field, a bad reference URL) and amber advice that never blocks a save (for example, a threat whose mitigations are all soft). You can create a new threat or delete one, and a read-only YAML view shows exactly what will be written to disk.

**Mitigations** does the same for the mitigation cards, in the same layout and with the same rules: browse, read, edit every field, and create or delete a card. Deleting a mitigation unlinks it from any threats that referenced it.

**Style guide** edits the authoring guidance itself. The left rail is a field tree derived from the model, each field carrying a coverage badge, so the guidance can't drift from the fields it describes; fields with guidance but no matching model field are flagged as orphans. The center pane edits a field's slots (purpose, what to include, what to avoid, examples), and the right pane shows precisely what an author sees while you edit that same guidance.

The form and its dropdowns read a JSON Schema generated from the Pydantic models, never hand-written, so it cannot drift from the code. `keel schema` regenerates the files under `schema/`, `keel schema --check` fails when they are stale (CI runs this as a gate), and `GET /schema/{entity}` serves them to the browser.

## Why not just OWASP, ATLAS, or MAESTRO

Keel builds on all three and reuses their framing. They give you a shared language and stop there, which leaves two problems standing.

**A threat model is an encyclopedia, not an engine.** It is read, not run. Nothing in it answers the only question that matters in front of a real system: is this reachable here at all?

**And it is someone else's encyclopedia.** It was not written about your architecture. Taking it as it stands does not fit; editing it to fit turns it into your own encyclopedia within a quarter - just as dead, and now wrong as well.

The second problem is what makes the first one hard. An engine over somebody's list is easy. What is hard is a list you can rewrite for yourself that does not rot while you do it. Each framework also has its own blind spot.

| Framework | Blind spot |
| --- | --- |
| **OWASP LLM Top 10** | One ranked list that mixes different kinds of thing: mechanisms (Prompt Injection becomes a threat only once it reaches a real asset through an agent's privileges), consequence classes (Sensitive Information Disclosure), generic software risk (Supply Chain), and teaching traps (System Prompt Leakage wrongly treats the system prompt as a security boundary). A good coverage checklist, a poor threat model. |
| **MITRE ATLAS** | Adversary-side, and a catalogue rather than a procedure. It tells you what has been done to systems like yours; it cannot tell you whether any of it is reachable in yours. A companion to a threat model, not a replacement. |
| **CSA MAESTRO** | An architectural map you read, with no rule for deciding what applies to the system in front of you. It is also overkill for a single-agent, single-tool setup. |

Keel works a different axis. Everything in it serves one of those two problems.

**Against the encyclopedia.** Every threat carries a `reachability` - the condition under which it is not a live path in a given system - so the model can be run against an architecture rather than read. The assessor walks it and returns findings with a delta against the last run, and a finding the catalog did not have is recorded as such rather than quietly absorbed. That is what separates framework literacy from a working practice.

**Against it being someone else's.** The model is YAML in git and forks. `implementations` is a layer of its own: the shared card defines the control and how to accept it, your implementation records how you built it, and the two move on different clocks - which is also what lets an assessment ask whether a control is in place *here* rather than whether it exists in general. The style guide, the review skill and the record-level rules are what keep a fork from decaying into a private mess, because a model nobody can edit safely is one nobody edits.

It also separates what OWASP conflates: a mechanism becomes a finding only once it reaches a real asset. And it stays lean, so a single-agent setup does not pay for a full layered methodology.

## Interfaces

- **MCP** (primary): `stdio` for local Claude Code, `--http` for remote clients. Tools cover threats CRUD plus mitigation links, mitigations CRUD, the style guide, and health/stats.
- **REST** for browsing and editing the model: reads (`/threats`, `/threats/{id}`, `/mitigations`, `/mitigations/{id}`, `/style-guide`, `/style-guide/coverage`, `/schema/{entity}`, `/health`) plus the write endpoints that back the browse/edit UI (`PATCH /threats/{id}`, threat-mitigation links, `PATCH /style-guide/{entity}/{field}`, and `POST /threats/validate`). The MCP tools and the REST writes share one service layer, so every edit lands in `catalog/*.yaml`.

## Development

Two checks, for two different things:

- **`keel validate`** checks the *catalog content*, your threats and mitigations, against the schemas: strict enums, link integrity, id/filename agreement, plus advisory warnings (an over-graded `gating` link, empty references, an unused field). This is the content gate a team relies on when growing the model.
- **`pytest`** is the *code* test suite, for anyone modifying Keel itself (schema generation, the REST/MCP endpoints and services, CRUD, the lints):

```bash
pip install -e ".[dev]"
pytest
```

CI runs both on every pull request.

## License

Keel is licensed under the [Apache License 2.0](LICENSE), covering the code, the threat catalog (`catalog/`), the assessment skills, and the docs. Attribution is requested when reusing the catalog or the methodology. See [NOTICE](NOTICE).

The bundled `humanizer` skill is third-party work by Siqi Chen under the MIT License.
