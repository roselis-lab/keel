# Keel UI — review-first redesign + full CRUD + overview

> **For Claude:** REQUIRED SUB-SKILL: superpowers:executing-plans / subagent-driven-development. Front-end tasks have no JS test harness — each ends with a headless smoke check (server serves the page, endpoints resolve, `node --check` on the extracted script) AND a best-practice conformance check against the Design Constraints below. Do NOT ask the user to click-verify; verify against the rules.

**Goal:** Fix the cluttered threat editor (real page-design rules), complete the UI's CRUD (threats incl. `references`, a full Mitigations editor, create/delete for both), and add an Overview page — so the UI is a clean review + complete-fallback surface, while the LLM/MCP stays the primary editor and git stays with the LLM/harness + `gh`.

**Context:** `keel/static/index.html` is one vanilla no-build file. Two screens today (Threats, Style guide). Back-end endpoints already added on this branch: `POST /threats`, `DELETE /threats/{id}`, `POST /mitigations`, `DELETE /mitigations/{id}`, `GET /health/library`, plus the earlier `POST /threats/validate`, `GET /style-guide/coverage`, `GET /schema/{entity}` (incl. `mitigation`), `GET /config`. Store honors `CATALOG_DIR`.

**Tech:** vanilla HTML/CSS/JS, no build, no deps. Back-end Python/FastAPI/pytest (TDD).

---

## Design Constraints (research-backed — every UI task MUST follow these)

Sources: NN/g (cognitive load in forms), GOV.UK Design System, IBM Carbon, Atlassian, Material, W3C WAI, web.dev CLS. The current page fails on three things; fix all three.

**1. Three visual tiers, three DIFFERENT devices** (so section ≠ subsection ≠ item):
- **Section** (Harm, Surface, Source, Weaknesses, Reachability, Mitigations, References, Tags): a semantic `<fieldset>` with a `<legend>` styled as the largest heading; separated by whitespace (section gap visibly larger than field gap) and an optional hairline band/divider. **No card border around a whole section.**
- **Subsection**: a heading one type-step down, no border (rare here).
- **Repeatable item** (each weakness / mitigation-link / reference): an actual **bordered, filled card** with padding, a remove ✕, and an "Add …" button below the stack. The card border is the ONLY heavy container.

**2. Field guidance — kill the noise and the reflow:**
- Keep exactly ONE muted, ~12px, single-line hint under each label (visibly subordinate to the label; reserve its row height so fields align). No placeholder-as-hint.
- Move the verbose style-guide content (Include / Avoid / Example / "use example") OUT of the form column into the **right rail**, shown for the currently focused field. The rail is fixed-width and scrolls independently, so its content changing NEVER reflows the form (web.dev CLS rule). No inline expanding panel in the form flow.

**3. Progressive disclosure:**
- First repeatable card expanded; additional cards render **collapsed to a one-line summary** (e.g. `component · short text`) with expand-on-click. Max one reveal level inside a card.
- Verbose guidance is only shown for the focused field (in the rail), never all at once.

**4. Spacing/typography:** one spacing scale (multiples of 4/8); fixed input height; field-to-field gap ~24px; section-to-section gap ~40–48px (must read as larger). Max 3 type steps (legend > subsection > label). Single readable column for the form (~640–720px).

**5. Right rail = two modes:** `Preview` (default) and `Guidance`. Guidance auto-selects when a field gains focus and shows that field's bar; Preview otherwise. Both live in the same fixed rail; switching modes must not move the form.

**6. Consistency:** the Mitrigations editor and the Style-guide editor reuse these exact rules and helpers. Two screens must not diverge in look.

Anti-checklist: don't give sections/subsections/cards the same weight; don't keep verbose guidance inline where it expands; don't let hints compete with labels; don't nest more than two disclosure levels.

---

## Milestone A — Back-end (mostly done; verify + commit)

### Task A1: Confirm/settle the CRUD + health endpoints
A background agent added `POST/DELETE /threats`, `POST/DELETE /mitigations`, `GET /health/library` and `tests/test_crud_routes.py`. Verify: full `pytest -q` green, `ruff` clean, `keel validate` ok, and — critically — the tests do NOT mutate the real `catalog/` (they must use a temp store). Confirm `git status` shows no `catalog/` changes. Ensure it's committed as one clean commit. If the agent already committed, this task is a review-only pass.

---

## Milestone B — Redesign the threat editor (the core fix)

Rework `editThreat` / `fieldEditor` / `weaknessesEditor` / `mitigationsEditor` and the style-guide bar in `keel/static/index.html` to the Design Constraints. Keep the existing endpoints, validation (validate-on-blur, two channels), and save flow working.

### Task B1: Section tiers + spacing + one-line hints
- Wrap each section in `<fieldset><legend>`; apply the spacing scale (section gap > field gap); render a single muted one-line hint per field (from the style-guide `purpose`); remove the inline expanding guidance panel from the form flow.
- Smoke: node --check; server serves; a threat renders with clear section bands and no inline guidance panel. Conformance: tiers use fieldset/legend (not cards); hint is one muted line.
- Commit: `feat(ui): threat editor — section tiers, spacing, single-line hints`

### Task B2: Right-rail Preview/Guidance (move guidance out of the form)
- Right rail gets two modes: Preview (default) and Guidance. On field focus, the rail switches to Guidance and shows that field's Include/Avoid/Example + "use example" (fed live from `state.style`). Losing focus / on blur returns to Preview (or a small toggle). Nothing in the form reflows when the rail changes.
- Reuse the existing `sgPanelFrom`/`styleField` data; just relocate the render target to the rail.
- Smoke + conformance (no layout shift: the form column is unchanged when focusing fields). Commit: `feat(ui): field guidance moves to the right rail (no reflow)`

### Task B3: Repeatable cards as bordered items + collapse extras
- Weakness and mitigation-link items render as bordered cards; first expanded, the rest collapsed to a one-line summary with expand-on-click; "Add …" below the stack; remove ✕ per card.
- Smoke + conformance (card border is the only heavy container; extras collapsed). Commit: `feat(ui): repeatable items as cards with progressive disclosure`

---

## Milestone C — Complete threat CRUD

### Task C1: References editor
- Add a References section: repeatable cards each with `id` + `url` (url validated as a URL; the schema/`Reference` model is `{id, url}`). Include it in the Save PATCH body (extend the payload; the endpoint's `ThreatUpdate` accepts `references`). Remove the "references deferred" skip.
- Smoke + conformance. Commit: `feat(ui): references editor`

### Task C2: Create / delete a threat
- "＋ New threat" (asks for an id, opens a blank draft, POSTs to `/threats`) and a "Delete" action on a threat (DELETE `/threats/{id}`, with a confirm). Update the rail after.
- Smoke (create + delete round-trip against the sandbox; restore). Commit: `feat(ui): create and delete threats`

---

## Milestone D — Mitigations editor screen (full mitigation-card CRUD)

### Task D1: Mitigations browse + read
- Add a `Mitigations` screen (nav) reusing the three-pane grammar: rail lists mitigations (id + name), read view shows the card (name, class, status, purpose, scope, control_mechanism, failure_behavior, owner/maintainer/locus, telemetry, anti_patterns, validation, faq, and which threats link it).
- Fields/enums come from `GET /schema/mitigation`. Commit: `feat(ui): mitigations browse + read`

### Task D2: Mitigation edit + create/delete (same design rules)
- Edit form built from the mitigation schema, applying the SAME Design Constraints (section tiers, one-line hints, right-rail guidance from the `mitigation` style-guide entity, cards for list fields like validation/faq/anti_patterns). Save via `PATCH /mitigations/{id}`. Create via `POST /mitigations`; delete via `DELETE /mitigations/{id}` (it unlinks from threats — warn in the confirm).
- Smoke + conformance. Commit: `feat(ui): mitigation edit + create/delete`

---

## Milestone E — Overview page

### Task E1: Overview screen
- New `Overview` screen (make it the landing nav). Reads `GET /health/library` (stats + issues: threats_missing_weaknesses/_harm, without_mitigation, dangling_mitigation_links) and `GET /style-guide/coverage`. Renders: the counts, style-guide coverage overall + per entity, and a "gaps to review" list grouped by issue with the affected ids (click an id → open that threat). Soft/never-blocking framing.
- Smoke + conformance. Commit: `feat(ui): overview page (coverage + gaps)`

### Task E2: Nav + polish
- Nav = `Overview · Threats · Mitigations · Style guide`; Overview is default. Ensure all four screens share the layout and the rail behavior. Tidy any leftover (e.g. `esc()` the saved-dialog path).
- Commit: `feat(ui): unify nav across the four screens`

---

## Milestone F — Docs
Update README (the UI is now review-first with full CRUD + overview; git stays with the LLM/harness + gh; note the skill from the next phase). Mark this plan complete. Commit.

---

## Deferred to the next phase (not this plan)
- The **skills** to work with the model (edit + git `branch/commit/push/gh pr create`) — item 5; its own design + TDD validation.
- In-app git sync — explicitly NOT built (competitor norm is to leave git to CLI/CI; our LLM+gh + one-file-per-entry covers it).
