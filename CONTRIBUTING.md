# Contributing to Keel

Thanks for helping build Keel. The most valuable contributions are to the **catalog**: new threats and mitigations, and corrections to existing ones. Code, docs, and tooling contributions are welcome too.

## What belongs in the shared catalog (floor, not ceiling)

Keel's catalog is a **floor**: a small set of GenAI/LLM threat patterns that apply across many systems. Keep that scope in mind:

- **In scope:** a general, recognizable threat pattern or an architectural mitigation that applies beyond one organization.
- **Out of scope (keep in your fork):** threats specific to your stack, and per-organization state such as "not applicable here" or "already mitigated." Those are how *you* tailor a fork; they would only add noise to the shared floor.
- **Prefer extending** an existing threat or mitigation over adding a near-duplicate.

A threat must be **harm-centric**: it anchors to one `harm` (the consequence class), names the `surface` the untrusted influence crosses and the `source` that drives it, describes *how* the system is exploitable as one or more `weaknesses` — each an architectural condition sitting on a named `component`, marked `targeted` (remove it and the attack fails) or `secondary` (it only amplifies) — and states `reachability` carve-outs, written as "not applicable if ...", judged on the **un-mitigated** system. A mitigation must be an architectural control authored as a **mitigation card** whose `mitigation_class` (`gating_control`, `detector`, `process`, `evidential_mitigation`, `corrective`) is a switch for how its control mechanism and failure behavior are read.

## Dev setup

```bash
uv sync --extra dev          # or: pip install -e ".[dev]"
```

There is no database and no build step — the server reads `catalog/*.yaml` into memory on start.

## Editing the catalog

`catalog/*.yaml` is the single source of truth (one file per threat, one per mitigation, and one file per entity under `style_guide/`). Every write goes straight to those files. Two ways to edit:

**A. Edit the YAML directly.** Change or add `catalog/threats/<id>.yaml` or `catalog/mitigations/<id>.yaml`, then validate and test:

```bash
uv run keel validate
uv run pytest
```

**B. Edit through the tools.** Use the MCP write tools (which carry the style guide's authoring bar) or the browse UI; each write patches the YAML directly.

Either way, commit the YAML diff.

## Quality bar

Every content field has an authoring bar in the **style guide** (the `get_style_guide` MCP tool, or the Style Guide tab in the UI). Match it: `weaknesses` should read as conditions an assessor can recognize on an unseen architecture, and `reachability` should be written as "not applicable if ...". Do not paste marketing or vague prose.

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
