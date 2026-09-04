# Contributing to Keel

Thanks for helping build Keel. The most valuable contributions are to the **catalog**: new threats and mitigations, and corrections to existing ones. Code, docs, and tooling contributions are welcome too.

## What belongs in the shared catalog (floor, not ceiling)

Keel's catalog is a **floor**: a small set of GenAI/LLM threat patterns that apply across many systems. Keep that scope in mind:

- **In scope:** a general, recognizable threat pattern or an architectural mitigation that applies beyond one organization.
- **Out of scope (keep in your fork):** threats specific to your stack, and per-organization state such as "not applicable here" or "already mitigated." Those are how *you* tailor a fork; they would only add noise to the shared floor.
- **Prefer extending** an existing threat or mitigation over adding a near-duplicate.

A threat must be **harm-centric**: it anchors to one `harm` (the consequence class), names the `surface` the untrusted influence crosses and the `source` that drives it, describes *how* the system is exploitable as one or more `weaknesses` — each an architectural condition sitting on a named `component`, marked `targeted` (remove it and the attack fails) or `secondary` (it only amplifies) — and states the `reachability` carve-out: the condition under which the threat is not a live path at all, judged on the **un-mitigated** system. A mitigation must be an architectural control authored as a **mitigation card** whose `mitigation_class` (`gating_control`, `detector`, `process`, `evidential_mitigation`, `corrective`) is a switch for how its control mechanism and failure behavior are read.

## `catalog/` and `drafts/`

`catalog/` is a promise: everything in it has been read by a maintainer and is believed correct, well written, and backed by at least one reference. It is being refilled one entry at a time, so it is small on purpose.

`drafts/` holds content that is written but not vouched for — the first, too-fast pass at the catalog. Nothing there is loaded by the app, served over MCP, or checked by `keel validate`. It is source material, and it moves one way: an agent may write into `drafts/`, and only a person moves a file from `drafts/` into `catalog/`. See [drafts/README.md](drafts/README.md).

## The coverage matrix

`catalog/coverage/*.yaml` records, for every source Keel tracks, each entry of a pinned release and one of three states: `covered` (naming the Keel ids that answer it), `out_of_scope` (with the reasoning), or `gap`. Four sources are tracked: the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications, MITRE ATLAS, and Google's SAIF risk map.

Write these source-first. Every entry of the release gets a row whether or not Keel answers it, because that is the only way a gap is visible at all — a matrix built from Keel's side outwards can never show what is missing. A card's "who else names this" view is derived from the same rows, so never copy a framework mapping onto a card: `references` on a card is for evidence (an incident, a paper, a CVE), and the mapping lives here.

`out_of_scope` is the state worth getting right, and the reason the matrix earns any trust. It describes Keel's boundary, never a disagreement with the source, and it is not where "we cover this differently" goes — an entry Keel answers in a shape of its own is `covered`, with a note explaining the shape. Prompt injection is the example: Keel models it as a mechanism carried by `surface` and `source` across many threats rather than as one row of its own. A boundary with no reasoning attached is indistinguishable from an omission, so the schema requires the note. `keel validate` refuses a `covered` entry that names something not in the catalog, since that is not a broken link but a false public claim.

An unfinished import is reported rather than hidden: `source.entry_count` states how large the release is, and a file holding fewer rows than that warns with both numbers.

## Dev setup

```bash
uv sync --extra dev          # or: pip install -e ".[dev]"
```

There is no database and no build step — the server reads `catalog/*.yaml` into memory on start.

## Editing the catalog

`catalog/*.yaml` is the single source of truth (one file per threat, one per mitigation, one per entity under `style_guide/`, one per tracked source under `coverage/`, and one per frozen vocabulary at the top level). Every write goes straight to those files. Two ways to edit:

**A. Edit the YAML directly.** Change or add `catalog/threats/<id>.yaml` or `catalog/mitigations/<id>.yaml`, then validate and test:

```bash
uv run keel validate
uv run pytest
```

**B. Edit through the tools.** Use the MCP write tools (which carry the style guide's authoring bar) or the browse UI; each write patches the YAML directly.

Either way, commit the YAML diff.

## Quality bar

Every content field has an authoring bar in the **style guide** (the `get_style_guide` MCP tool, or the Style Guide tab in the UI). Match it: `weaknesses` should read as conditions an assessor can recognize on an unseen architecture, and `reachability` should state the condition itself rather than restate the field's own label. Every reference carries a `note` saying what that source actually supports. Do not paste marketing or vague prose.

## Before you open a PR

```bash
uv run keel validate   # schema, strict enums, and link integrity of catalog/
uv run ruff check .
uv run pytest
```

All three must pass. CI runs the same checks.

## Reporting issues

Use the issue templates: bug reports, catalog additions, catalog corrections (challenges to existing content are especially welcome), and feature requests.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE). Attribution for catalog and methodology reuse is described in [NOTICE](NOTICE).
