# UI kit — Keel authoring UI

A recreation of Keel's real browse/edit UI, read from `keel/keel/static/index.html` (the single static file the product serves at `localhost:8000/`). Not a storybook: `index.html` opens on the Overview and the five screens are click-through.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The app. Loads `styles.css`, `_ds_bundle.js`, then each screen. |
| `data.js` | Faithful slices of the real `catalog/*.yaml` and `reports/checkout-agent/2026-08-26.yaml`. No network. |
| `shell.jsx` | `AppShell` (the rail/editor/preview grid), `RailHeader`, `Prose`, `PanelCard`. |
| `OverviewScreen.jsx` | Counts, style-guide coverage, mitigation status, recent commits, gaps to review. |
| `ThreatsScreen.jsx` | Rail + faceted filter, the read view, and the edit form with both validation channels. |
| `MitigationsScreen.jsx` | The same three panes for the 71 `CTRL-*` cards, plus the reverse "Addresses" index. |
| `StyleGuideScreen.jsx` | Field tree with coverage badges, the slot editor, and the live author preview. |
| `ReportsScreen.jsx` | Assessment findings ranked by severity, requirement checklists, discarded threats, assessor dialogue. |
| `app.jsx` | State and wiring. |

## What is real and clickable

- **Screen switching** across all five screens; the rail collapses to a 44px strip on every one.
- **Threats**: text filter (matches id, title, weakness text, reachability), the faceted filter (OR within a group, AND across groups, with a crimson count badge and Clear all), select a threat, read it, press **Edit**, change fields, watch the amber advice recompute, **Save** → the saved-dialog names the YAML file to commit. Changes persist in session.
- **Gap chips** at the foot of a read view jump into edit with that field focused — try `T-METADATA-LEAK`, which has no reachability and no mitigations.
- **"view change"** on the provenance line reveals the unified diff inline.
- **Cross-navigation**: a mitigation link jumps to its card; the card's "Addresses" list jumps back. `T-DOS` carries a deliberately **dangling link** (`CTRL-LEGACY-GUARD`) so the dangling-link state is visible.
- **Style guide**: pick a field, edit its slots, and the right rail shows exactly what an author sees. This is the one screen where the third pane earns its column — everywhere else it collapses to `0px`.
- **Reports**: findings are ranked critical → low and expand to the full chain (source, asset, vulnerability, risk reasoning, requirements, delta).

## Deliberately omitted

- Real HTTP. The product reads `/schema/{entity}`, `/threats`, `/mitigations`, `/style-guide/coverage`, `/health/library`, `/history/*` and `/reports/*`; here those payloads are inlined in `data.js`.
- The **drag-resizable preview divider** (a 9px fixed hit-strip on the main|preview seam). The width token is honoured; the drag is not wired.
- Mitigation **editing** and the YAML source view. The read view and the reverse index are complete; the form is the same `Field`/`SectionBand` composition as the threats editor.
- Delete confirmation flows — the buttons flash an explanatory toast instead.
