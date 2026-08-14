# Contributing to Keel

Thanks for helping build Keel. The most valuable contributions are to the **catalog**: new threats and mitigations, and corrections to existing ones. Code, docs, and tooling contributions are welcome too.

## What belongs in the shared catalog (floor, not ceiling)

Keel's catalog is a **floor**: a small set of GenAI/LLM threat patterns that apply across many systems. Keep that scope in mind:

- **In scope:** a general, recognizable threat pattern or an architectural mitigation that applies beyond one organization.
- **Out of scope (keep in your fork):** threats specific to your stack, and per-organization state such as "not applicable here" or "already mitigated." Those are how *you* tailor a fork; they would only add noise to the shared floor.
- **Prefer extending** an existing threat or mitigation over adding a near-duplicate.

A threat must be **impact-centric**: it anchors to one `impact_class`, describes *how* it is exploitable as one or more `vulnerability` patterns, and states `reachability` carve-outs (when it is *not* a live path, judged on the un-mitigated system). A mitigation must be an architectural control with a `type` (`PREVENTIVE_HARD` blocks, `PREVENTIVE_SOFT` only hinders, `DETECTIVE`, `CORRECTIVE`).

## Dev setup

```bash
uv sync --extra dev          # or: pip install -e ".[dev]"
uv run alembic upgrade head  # build the schema
uv run keel seed             # load the catalog into the database
```

## Editing the catalog

The catalog is the source of truth as YAML under `catalog/` (one file per threat, one per mitigation, and one file per entity under `style_guide/`). The database is generated from it. Two ways to edit:

**A. Edit the YAML directly.** Change or add `catalog/threats/<id>.yaml` or `catalog/mitigations/<id>.yaml`, then validate, load, and check:

```bash
uv run keel validate
uv run keel seed
uv run pytest
```

**B. Edit through the tools, then export.** Use the MCP write tools (which carry the style guide's authoring bar) or the browse UI, then write the changes back to YAML:

```bash
uv run keel export
```

Either way, commit the YAML diff. `threat_library.db` is git-ignored, so it stays out of the PR.

## Quality bar

Every content field has an authoring bar in the **style guide** (the `get_style_guide` MCP tool, or the Style Guide tab in the UI). Match it: `vulnerability` items should read as patterns an assessor can recognize on an unseen architecture, and `reachability` should be written as "not applicable if ...". Do not paste marketing or vague prose.

## Before you open a PR

```bash
uv run keel validate   # schema, strict enums, and link integrity of catalog/
uv run ruff check .
uv run pytest
```

All three must pass. CI runs the same checks plus a full build of the database from the catalog.

## Reporting issues

Use the issue templates: bug reports, catalog additions, catalog corrections (challenges to existing content are especially welcome), and feature requests.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE). Attribution for catalog and methodology reuse is described in [NOTICE](NOTICE).
