# Keel

**A framework for building and running your own living GenAI/LLM threat model.** It ships with a working reference model and an assessor that runs against real systems.

[![CI](https://github.com/roselis-lab/keel/actions/workflows/ci.yml/badge.svg)](https://github.com/roselis-lab/keel/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A keel is the single load-bearing member that keeps a hull upright and on course with the least material. That is the goal here too: the smallest opinionated structure that holds a GenAI threat model together and keeps an assessment on course.

## The problem

The public GenAI threat corpora, OWASP LLM Top 10, MITRE ATLAS, and CSA MAESTRO, are references you read. They are taxonomies, adversary knowledge bases, and layered methodologies. None of them is a model you can run against a specific system, and none adapts to your organization without a large manual lift. So every team re-derives the same threats from scratch, in prose, inconsistently, and ends up with a document that ages on a wiki instead of a model that takes part in review.

Keel is the operational layer that is missing: a compact, opinionated representation of GenAI threats, a reference model already authored in it, and an assessor that walks a real system against it. All of it is editable, so a team can grow it into their own model.

## What Keel is (three layers)

| Layer | What it is | Role |
| --- | --- | --- |
| **1. Reference model** | 13 impact-centric threats, 71 mitigations, 96 links, authored in the facet schema | The seed content: a floor to start from, not the product |
| **2. The framework** | the facet representation (`impact_class` + `vulnerability` + `reachability`), the mitigation taxonomy (HARD/SOFT), a hard authoring style guide, and the machinery to extend it (MCP + REST + DB + browse/edit UI) | What a team adopts and grows into its own model |
| **3. The assessor** | skills that turn the static model into a repeatable pass over a real system (data-sufficiency gate, per-threat chain, delta, two-part output) | What makes the model runnable: read versus run |

The reference model is deliberately small: the catalog is a floor, not a ceiling. Keel's value is the shape and the assessor, not a claim to enumerate every GenAI threat.

## Why not just OWASP, ATLAS, or MAESTRO

Keel builds on all three and reuses their framing; the assessment reports its findings as a delta against MITRE ATLAS. They give you a shared language and stop there. A working practice needs more: it has to be lean enough to actually run, produce checkable evidence, and live in one shared place a team can grow with its systems. Each framework also has its own blind spot.

| Framework | Blind spot |
| --- | --- |
| **OWASP LLM Top 10** | One ranked list that mixes different kinds of thing: mechanisms (Prompt Injection becomes a threat only once it reaches a real asset through an agent's privileges), consequence classes (Sensitive Information Disclosure), generic software risk (Supply Chain), and teaching traps (System Prompt Leakage wrongly treats the system prompt as a security boundary). A good coverage checklist, a poor threat model. |
| **MITRE ATLAS** | Adversary-side. It describes what the attacker does, not where in your architecture a control goes or who owns it. A companion to a threat model, not a replacement. |
| **CSA MAESTRO** | Without CI/CD rules, control owners, and proof of implementation it stays an architectural map, not an enforcement mechanism. It is also overkill for a single-agent, single-tool setup. |

Keel works a different axis from the frameworks above. It makes the language operable, lean, and shared.

- It stays lean. The facet model carries only what is live (the consequence, the mechanism, and whether it is reachable), and the catalog is a floor, so you skip the overhead of a full layered methodology on a single-agent setup. It also separates what OWASP conflates: a mechanism becomes a finding only once it reaches a real asset.
- It is operable. The assessor walks the model against a real system and returns findings, which is what separates framework literacy from a working practice.
- It insists on evidence. The data-sufficiency gate and the rule that "model behavior is not a mitigation" stop an assessment from claiming a control works without proof; a SOFT control that only hinders leaves the threat open.
- It centralizes. One shared model, queried over MCP, gives every team the same definitions, so the same threats get written once and reused.
- It is built to grow. Each team extends and prunes it into its own living model, carrying its edits forward as its systems change. Per-organization state (mark a threat not applicable, a mitigation already implemented) is on the roadmap.

## The model

Four entities, nothing more:

| Entity | Fields |
| --- | --- |
| **Threat** | `id`, `title`, `description`, `impact_class` (asset/damage anchor, strict enum), `vulnerability[]` (prose patterns of *how* it's exploitable, the recognition anchor), `reachability` (carve-outs: *when it is NOT a live path*, judged un-mitigated), `tags[]` |
| **Mitigation** | `id`, `title`, `description`, `type`, `requirement_level`, `implementations[]` |
| **ThreatMitigation** | link `threat_id` ↔ `mitigation_id` with `rationale` |
| **StyleGuideField** | authoring methodology per content field; auto-synced from model columns |

Enums:
- `Threat.impact_class`: `decision-integrity` · `data-confidentiality` · `infrastructure-execution` · `resource-availability` · `reputation-compliance` · `recon-exposure`
- `Mitigation.type`: `PREVENTIVE_HARD` (blocks) · `PREVENTIVE_SOFT` (hinders) · `DETECTIVE` · `CORRECTIVE`
- `Mitigation.requirement_level`: `MANDATORY` · `RECOMMENDED`

The catalog is impact-centric: a threat is an impact (the asset under fire), with cause, surface, and predisposing weakness woven into the `vulnerability` patterns; `reachability` carries the "when does this actually apply" judgement, assessed on the un-mitigated system.

Design principle: **methodology lives in the assessor's prompt, the model stays lean.** Per-system assessment output (actor, scenario, impact, and so on) is ephemeral and is not stored here.

## Interfaces

- **MCP** (primary): `stdio` for local Claude Code, `--http` for remote clients. Tools cover threats CRUD plus mitigation links, mitigations CRUD, the style guide, and health/stats.
- **REST** (read-only) for browsing the model: `/threats`, `/threats/{id}`, `/mitigations`, `/mitigations/{id}`, `/style-guide`, `/health`. All writes go through MCP.

## Assessment skills

The assessor ships as skills under `.claude/skills/`:

- **`assessing-genai-security`** is the calibrated, model-agnostic methodology: the data-sufficiency gate, the per-threat chain (source, surface, vulnerability, scenario, business impact, risk, delta), and the two-part output (analysis trail plus final assessment).
- **`assess-genai-with-library`** binds that methodology to Keel's MCP (candidate threats, then a `reachability` match on the target system, then mitigations), and polishes the final assessment through `tighten-text` (concision, de-bullet) and `humanizer` (natural expert voice). Both are substance-preserving.

## Run

Keel is an MCP server — for any agent or MCP client — plus a browse UI. It builds its database from `catalog/` on first start, so there are no setup steps.

One command (needs the Docker daemon) serves the UI at `http://localhost:8000/`; add `--profile mcp` for the HTTP MCP transport on `:8001`:

```bash
docker compose up
```

Or let your agent launch it over stdio: `.mcp.json` in this repo is a ready-to-use example for MCP clients (it exposes the tools as `mcp__keel__*`). Nothing to seed — the server loads the catalog itself on first run.

<details>
<summary><b>Run from source / develop Keel</b></summary>

Uses `uv` (pinned in `uv.lock`); `uv run` handles the virtualenv and `PATH` for you:

```bash
uv sync
uv run uvicorn keel.main:app     # browse UI + REST at http://localhost:8000/
uv run keel                      # stdio MCP        (uv run keel --http → HTTP MCP on :8001)
uv run keel validate             # check catalog    (uv run keel export → write the DB back to catalog/)
```

The SQLite database builds itself from `catalog/` on first run. For a long-lived Postgres instance, `uv run alembic upgrade head` manages the schema instead. Without `uv`, `pip install -e .` installs the same `keel` console script, or run it as `python -m keel …`.
</details>

The browse UI (single static file, no build step) shows threats, mitigations, and the style guide, cross-linked. It supports inline editing through REST endpoints that share the service layer with the MCP write tools: MCP is the style-guide-guided authoring path, the UI is the raw counterpart.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite includes a health check on the library (`tests/test_health.py`): it runs the stat counts and confirms that `check_library_health` flags content and integrity gaps, such as a threat missing its `vulnerability` or `impact_class`, a threat with no mitigation, or a dangling mitigation link. The same integrity check runs at runtime through the `check_library_health` and `get_stats` MCP tools; the REST `/health` endpoint is a simple liveness probe.

## Make it yours

Keel ships with a curated English reference model: 13 impact-centric threats and 71 mitigations (96 links). The content is the source of truth as reviewable YAML under `catalog/` (one file per threat and per mitigation, and one file per entity under `style_guide/`); `threat_library.db` is a generated artifact that `keel seed` builds from it, so content changes land as readable diffs in pull requests instead of a binary blob. `keel validate` checks the YAML against the schemas (strict enums, link integrity) before it touches the database, and runs in CI. It is meant to be forked and grown into your organization's model:

- Add threats and mitigations for your stack through the MCP write tools (guided by the style guide's authoring bar) or the browse UI, then run `keel export` to write the changes back to `catalog/*.yaml` for review.
- Adjust tags, implementations, and threat-to-mitigation rationale to match how your teams reason.
- Drop what does not apply: the catalog is a floor, so shrinking it to a sharper model tuned to your context is the point.

**Roadmap (not yet built):** per-organization state, so an org can mark a threat *not applicable* or a mitigation *already implemented* and suppress known noise without deleting the shared knowledge. For now you express that context by editing or pruning the model directly.

## License

Keel is licensed under the [Apache License 2.0](LICENSE), covering the code, the threat catalog (`catalog/`), the assessment skills, and the docs. Attribution is requested when reusing the catalog or the methodology — see [NOTICE](NOTICE).

The bundled `humanizer` skill is third-party work by Siqi Chen under the MIT License.
