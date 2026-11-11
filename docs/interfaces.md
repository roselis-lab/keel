# Commands, skills, UI and interfaces

## Which one for which job

| Job | Use |
| --- | --- |
| Assess a system | Your coding agent, with Keel's MCP server and the `assess-genai-with-library` skill |
| Correct and finalize a report, edit the catalog through forms | The local UI: `keel up` |
| Review a catalog change | A pull request on your Git host, with CI running `keel validate` |
| Show the catalog or a report to people who do not run Keel | The read-only site: `keel site`, published with GitHub Pages or GitLab Pages |
| Put a report in Confluence and its fixes in Jira | `keel publish`, run by the assessor with their own token |
| Script against the catalog | The REST API behind the local UI, or the MCP tools |

## Commands

Run each with `uv run` in front, or directly once Keel's environment is active.

| Command | Does |
| --- | --- |
| `keel validate` | Checks the catalog: schema, fixed vocabularies, links between records, id and filename agreement, coverage claims. Prints warnings for unfinished cards; exits non-zero only on errors. |
| `keel validate --strict` | The same, with warnings counted as errors. |
| `keel up` | Starts the local UI and REST API in the background at `http://127.0.0.1:8420/`, or says where it is already running. Safe to run at the start of every session. `UI_PORT` changes the port. |
| `keel down` | Stops it. |
| `keel site --out DIR` | Builds the read-only HTML site of the catalog into `DIR` (default `public`). Options: `--reports DIR` adds final reports, `--include-drafts` adds drafts too, `--title` names the site. See [Publish the read-only site](adopt.md#publish-the-read-only-site). |
| `keel recheck REPORT --repo PATH` | For every line a report quotes, says whether it is still in place, moved (with the new lines) or gone, reading each file at the checkout's HEAD. `--repo NAME=PATH`, repeated, for evidence that names its repository. Lists `command` and `test` evidence without running it. A reassessment starts from what it lists as moved or gone. |
| `keel schema` | Regenerates the JSON Schema files under `schema/`. |
| `keel schema --check` | Fails when those files are stale. CI runs it. |
| `keel export REPORT --out DIR` | Writes a report as a Confluence page, one picture per finding and one Jira ticket text per fix. Sends nothing. |
| `keel publish REPORT` | Pushes the page and the tickets with your own token: `--confluence-space KEY [--parent ID]`, `--jira-project KEY [--security-level NAME] [--issue-type Task]`, `--dry-run`, `--allow-draft`. See [Confluence and Jira](confluence-and-jira.md). |
| `keel style-guide export` | Prints the whole style guide as YAML. |
| `keel style-guide import FILE [--replace]` | Loads a style guide from YAML, merging by default. |
| `keel reports migrate --extension NAME` | Moves every field the report schema does not know, on a report, a finding or a requirement, into that extension's section of the report (`extensions.NAME`), so the report opens again. `--diagrams DIR` also takes `DIR/<system>/<date>.yaml` as the report's `system_diagram` there. `--dry-run` writes nothing. Prints a line per report it changes or cannot change; running it twice changes nothing. See [Extensions](#extensions). |
| `keel` | Runs the MCP server over stdio. Agents start this themselves. |
| `keel --http` | Runs the MCP server over Streamable HTTP on port 8001, loopback only. |
| `docker compose up` | The local UI in a container at `http://localhost:8000/`. Add `--profile mcp` for the HTTP MCP server on `:8001`. |

Settings come from environment variables or `.env`: `CATALOG_DIR` and `REPORTS_DIR` point at other folders, `UI_PORT` moves the UI, `ALLOWED_HOSTS` lists the names the UI answers to, `REPO_URL` adds an "Edit on GitHub" link in the UI. `KEEL_ARCHIFY` points at the Archify skill that draws the system diagram on a report page (it also needs Node on `PATH`).

## Skills

The same set is in `.claude/skills/` (Claude Code reads only its own folder) and `.agents/skills/` (every other agent). A test fails if the two drift, so edit one and copy it to the other.

### Assessing a system

**`assessing-genai-security`** is the model-agnostic methodology: the data-sufficiency gate, the per-threat chain (source, surface, weakness, scenario, business impact, risk, delta) and the two-part output, an auditable analysis trail followed by the final assessment.

**`assess-genai-with-library`** binds that methodology to Keel's MCP: candidate threats, the `reachability` match, then the linked mitigations and whether their `implementations` are actually in place. It finishes by polishing the final assessment through `tighten-text` and `humanizer`, both substance-preserving.

Every report carries a `meta` block recording how the run went: the questions that moved the analysis, the facts the specialist volunteered without being asked, and where they said the reasoning was wrong. That block exists to improve the assessor, so it is filled honestly, including the parts that do not flatter it.

### Working with the model

**`folding-into-the-model`** decides what kind of thing an incoming item is, whether the model already answers it, whether it is one record or part of one, and then writes to the bar. It shows its uncertainty rather than resolving it silently, and asks before changing what an existing entry means.

**`check-style`** judges what was written against the style guide. It applies the bar and does not own it: if a field is wrong and the bar is silent, the fix is to the bar.

See [Authoring](authoring.md) for how the two work together.

## The local UI

<p align="center"><img src="img/ui-preview.svg" alt="Keel's three-pane threat editor: the threat list on the left, a form built from the JSON Schema in the middle, and preview or field guidance on the right" width="900"></p>

One static HTML file, no build step, served at `http://127.0.0.1:8420/` by `keel up`. Six screens: Overview, Threats, Mitigations, Style guide, Coverage and Reports.

The interface is review-first. The fastest way to author is to ask an LLM through the MCP tools; the UI writes files and points you at the file to commit, and it is not a git client. It carries full create, read, update and delete for threats and mitigations as a complete fallback.

**Overview** is the landing screen: counts, style-guide coverage per entity, and a "gaps to review" list with chips that jump straight to the record. Nothing here blocks anything.

**Threats** and **Mitigations** edit one record at a time in three panes: list, editor, live preview. The form is built from a JSON Schema generated from the Pydantic models, never hand-written, so the fields, their order and the dropdowns cannot drift from the code. Each field keeps one short hint; the full guidance lives in the right rail, which flips from Preview to Guidance when a field has focus, so it never pushes the form around. Every change is checked on the server: red blocking errors when the structure is wrong, amber advice that never blocks a save.

**Style guide** edits the authoring guidance itself, with a field tree derived from the model so the guidance cannot describe fields that no longer exist. Orphan guidance is flagged.

**Reports** is where an assessor reads a draft, corrects grades and wording, and presses Finalize.

The UI and the MCP server are two processes over the same files, and each picks up what the other writes without a restart.

### Why it stays on your machine

The API writes your catalog and has no login, so being local is its whole access control. It binds to loopback, answers only to `localhost` and `127.0.0.1`, sends no CORS headers, and refuses a write that comes from another site. The container publishes its ports on the host's loopback for the same reason. To serve it to other machines, put something that authenticates in front of it and add its name to `ALLOWED_HOSTS`. For a shared view, the read-only site is the simpler answer.

## Interfaces

**MCP** is primary: `stdio` for local agents, `--http` for remote clients. Threats and their mitigation links, mitigations, the style guide, coverage rows, search across everything, reports, and library health.

**REST** reads and writes under `/api`: `/api/threats`, `/api/mitigations`, `/api/style-guide`, `/api/coverage`, `/api/reports`, `/api/search`, `/api/schema/{entity}`, `/api/rules`, `/api/vocabulary`, plus `POST /api/threats/validate` behind the editor. `/health` sits outside `/api`.

The MCP tools and the REST writes share one service layer, so every edit lands in `catalog/*.yaml` the same way. The two run as separate processes, and each reloads the catalog when the files change underneath it, so an entry written through one shows up in the other, as does a hand edit or a `git pull`.

Both listen on loopback only. `keel --http` will not bind to any other address unless `MCP_HTTP_ALLOW_REMOTE` is set.

### Extensions

A Python package can add to Keel without Keel knowing it: it declares an entry point in the group `keel.extensions`, and Keel loads it at start. It can check and draw its own data on a report page, serve its own pages and API, add MCP tools and add `keel` commands. The hooks are listed in `keel/extensions.py`. One that fails to load is logged and left out.

A report keeps an extension's data under `extensions.<name>`. Keel stores that section as it is through every save (MCP, the report editor) and does not show it on the read-only site. A report with a section opens and saves on a Keel without that extension; the section is then not checked.

## Roadmap

Per-system state, to mark a threat not applicable for a given deployment or to accept a risk, so known noise can be suppressed without deleting shared knowledge. Until then, that context lives in each report's ruled-out list, or in your copy of the catalog.
