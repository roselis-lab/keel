<!-- Thanks for contributing to Keel. Keep the description short and concrete. -->

## What and why

<!-- What does this change, and why? Link any related issue (e.g. Closes #12). -->

## Type

- [ ] Catalog: new or edited threat / mitigation
- [ ] Catalog: correction to existing content
- [ ] Code / tooling
- [ ] Docs

## Checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run pytest` passes
- [ ] For catalog changes: I edited `catalog/*.yaml` (not the database) and ran `uv run keel seed`
- [ ] For catalog changes: content follows the style guide bar (impact-centric threat, `reachability` carve-outs, mitigation `type`)
- [ ] This belongs in the shared catalog (a general pattern), not org-specific state that should live in a fork
