# Overview dashboard redesign — design

Date: 2026-08-26. Branch: threat-model-v2.

## What this covers

The Overview screen is the library's landing dashboard. Today it shows three counts (threats, mitigations, links), style-guide coverage percentages per entity, and four gap categories pulled from `/health/library` (missing weaknesses, missing harm, no linked mitigation, dangling links). The user flagged it as not pretty and not very informative, and pointed at data the product already computes but never surfaces: `catalog_warnings()` (over-graded link strength, missing threat references, unused `nature`), git history (already built per-card, never aggregated), the draft/verified split across the 71 mitigation cards, and how many mitigations have any org `implementation` at all, shared or local.

This redesign adds four sections to the dashboard, wires them to existing or lightly extended backend logic, and rearranges the page into a two-column grid so it stays scannable instead of turning into an endless scroll.

## Backend changes

**Structured catalog warnings.** `catalog_warnings()` in `keel/catalog.py` returns a flat list of human-readable strings, built for `keel validate`'s CLI output. The dashboard needs each warning to carry `entity_type` and `entity_id` so it can render as a clickable chip that jumps to the affected card, the same way the existing gap chips do. The detection logic moves into a new function returning structured records (`{category, entity_type, entity_id, message}`); `catalog_warnings()` becomes a thin formatter over that same data, so `keel validate`'s output is unchanged and the two can never drift apart.

**Recent activity.** `keel/githistory.py` only answers "what changed on this one card" (`history(entity, id)`), scoped to a single file with an allowlisted entity/id pair. A new function reads recent commits across the whole `catalog/` directory (`git log --name-status`, still argument-list only, still never `shell=True`), and maps each changed file back to `{entity_type, entity_id}` by its path under `catalog/threats/` or `catalog/mitigations/`. It degrades the same way the existing history functions do: outside a git repo, or if `git` is missing, it returns `{"available": False, "commits": []}` rather than raising. A new route, `/history/recent?limit=N`, exposes it.

**Draft/verified and implementation coverage.** Both are plain aggregation over data already loaded into `store` — no new I/O. `health_service.check_library_health()` gains two more computed fields: a count of mitigations by `status` (draft vs verified), and a count of mitigations by whether they have zero, only-local, or at-least-one-shared `implementation` entry.

## Layout

Two columns on top, full-width lists below — chosen so the glanceable numbers stay above the fold and the scannable detail lives underneath, without the page becoming one long scroll as it grows from 3 sections to 7.

- Row 1, left column: Counts (unchanged) stacked above a new Draft/verified section — a compact horizontal two-segment bar (verified vs draft), pure CSS, no charting library, with the counts written next to it.
- Row 1, right column: Style-guide coverage (unchanged, keeps its existing colour-banded percentage badges) stacked above a new Implementation coverage section — the same style of horizontal bar, three segments (shared / local-only / none) out of 71.
- Row 2, full width: Gaps to review (unchanged).
- Row 3, full width: new Catalog warnings section, visually matching the existing Gaps cards — grouped by category, each entry a clickable chip.
- Row 4, full width: new Recent activity section — up to 15 commits, each showing message, author, relative date, and a chip for the entity it touched.

This keeps the visual vocabulary to what already exists (`.ov-stat`, `.badge`, `.card`) plus one new primitive (the two/three-segment CSS bar), rather than pulling in a charting library — the middle ground the user asked for between a bare stat grid and a full data-viz dashboard.

## Interactivity

Warnings and Recent activity chips jump to the affected card, reusing the pattern the Gaps chips already use (`overviewOpenThreat`, extended to also handle mitigation ids). Clicking a number in Draft/verified or Implementation coverage switches to the Mitigations screen with the matching status or implementation filter pre-applied — the facet panel already supports filtering by status, so this only means passing an initial filter value through instead of building new filter UI.

## Error handling

`loadOverview()` currently fetches two endpoints with `Promise.all`. With five sources feeding the page, one failure (most likely git being unavailable, e.g. in a non-git checkout) must not blank the whole dashboard. It switches to `Promise.allSettled`; each section renders its own empty state ("git history unavailable", "nothing flagged", "no recent changes") independently of whether the others succeeded, consistent with how the existing Gaps section already shows a clean-state message when there is nothing to report.

## Testing

Backend: unit tests for the new structured-warnings function (same cases the existing `catalog_warnings()` tests already cover, plus asserting each item carries `entity_type`/`entity_id`), tests for `githistory`'s recent-activity function against a temporary git repo (mirroring the existing `history()` test fixtures), and tests for the new draft/verified and implementation-coverage aggregation in `health_service`.

Frontend: there is no JS test harness in this project (Python/pytest only), so verification is manual, through the Browser pane — a screenshot of the redesigned dashboard, a click-through on a warning chip and an activity chip confirming navigation to the right card, and a click on a Draft/verified or Implementation coverage number confirming it lands on Mitigations with the filter applied.
