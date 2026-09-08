# Skills, UI and interfaces

## Skills

Under `.claude/skills/`, in two groups.

### Assessing a system

**`assessing-genai-security`** is the model-agnostic methodology: the data-sufficiency gate, the per-threat chain (source, surface, weakness, scenario, business impact, risk, delta) and the two-part output, an auditable analysis trail followed by the final assessment.

**`assess-genai-with-library`** binds that methodology to Keel's MCP: candidate threats, the `reachability` match, then the linked mitigations and whether their `implementations` are actually in place. It finishes by polishing the final assessment through `tighten-text` and `humanizer`, both substance-preserving.

Every report carries a `meta` block recording how the run went: the questions that moved the analysis, the facts the specialist volunteered without being asked, and where they said the reasoning was wrong. That block exists to improve the assessor, so it is filled honestly, including the parts that do not flatter it.

### Working with the model

**`folding-into-the-model`** decides what kind of thing an incoming item is, whether the model already answers it, whether it is one record or part of one, and then writes to the bar. It shows its uncertainty rather than resolving it silently, and asks before changing what an existing entry means.

**`check-style`** judges what was written against the style guide. It applies the bar and does not own it: if a field is wrong and the bar is silent, the fix is to the bar.

See [Authoring](authoring.md) for how the two work together.

## The UI

<p align="center"><img src="img/ui-preview.svg" alt="Keel's three-pane threat editor: the threat list on the left, a form built from the JSON Schema in the middle, and preview or field guidance on the right" width="900"></p>

One static HTML file, no build step, served at `http://localhost:8000/`. Six screens: Overview, Threats, Mitigations, Style guide, Coverage and Reports.

The interface is review-first. The fastest way to author is to ask an LLM through the MCP tools; the UI writes files and points you at the file to commit, and it is not a git client. It carries full create, read, update and delete for threats and mitigations as a complete fallback.

**Overview** is the landing screen: counts, style-guide coverage per entity, and a "gaps to review" list with chips that jump straight to the record. Nothing here blocks anything.

**Threats** and **Mitigations** edit one record at a time in three panes: list, editor, live preview. The form is built from a JSON Schema generated from the Pydantic models, never hand-written, so the fields, their order and the dropdowns cannot drift from the code. Each field keeps one short hint; the full guidance lives in the right rail, which flips from Preview to Guidance when a field has focus, so it never pushes the form around. Every change is checked on the server: red blocking errors when the structure is wrong, amber advice that never blocks a save.

**Style guide** edits the authoring guidance itself, with a field tree derived from the model so the guidance cannot describe fields that no longer exist. Orphan guidance is flagged.

`keel schema` regenerates the files under `schema/`, and `keel schema --check` fails when they are stale. CI runs it as a gate.

## Interfaces

**MCP** is primary: `stdio` for local Claude Code, `--http` for remote clients. Threats and their mitigation links, mitigations, the style guide, coverage rows, search across everything, reports, and library health.

**REST** reads and writes over `/threats`, `/mitigations`, `/style-guide`, `/coverage`, `/reports`, `/search`, `/schema/{entity}`, `/rules`, `/vocabulary`, `/health`, plus `POST /threats/validate` behind the editor.

The MCP tools and the REST writes share one service layer, so every edit lands in `catalog/*.yaml` the same way.

## Roadmap

Per-system state, to mark a threat not applicable for a given deployment or to accept a risk, so known noise can be suppressed without deleting shared knowledge. Until then, that context is expressed by editing or pruning your fork.
