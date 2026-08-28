# Keel Design System

The design system for **Keel** — a framework for building and running your own living GenAI/LLM threat model. Everything here is lifted from the real product, not invented: the palette, the type ramp, the spacing rhythm and every component pattern come out of Keel's own authoring UI.

---

## 1. Sources

| Source | Path | What was taken from it |
| --- | --- | --- |
| Keel codebase (mounted local folder, read-only) | `keel/` | Everything below |
| **The authoring UI — the single design ground truth** | `keel/keel/static/index.html` (3,436 lines: `:root` tokens, the full stylesheet, and the vanilla-JS render functions for all five screens) | Palette, type ramp, spacing, radii, every component, all five screens |
| Product copy | `keel/README.md` (176 lines) | Positioning, tone, vocabulary, the three-layer story |
| Model schema + vocabularies | `keel/catalog/style_guide/*.yaml`, `keel/schema/*.schema.json`, `keel/keel/schemas/*.py` | Enums (harm, surface, source, component, nature, strength, mitigation_class, status) |
| Reference catalog | `keel/catalog/threats/*.yaml` (13), `keel/catalog/mitigations/CTRL-*.yaml` (71) | Real content for every screen and card |
| Assessment reports | `keel/reports/checkout-agent/{2026-05-10,2026-08-26}.yaml` | The report screen's data shape and real findings |
| Design plans (written before the screens were built) | `keel/docs/plans/2026-08-17-keel-authoring-ui-design.md`, `2026-08-18-keel-ui-review-first.md`, `2026-08-26-assessment-reports-design.md`, `2026-08-26-overview-dashboard-design.md` | Intent behind the review-first layout and the newer Overview / Reports screens |
| Diagrams (copied into `assets/`) | `keel/docs/img/{ui-preview,threat-spine,assessment-flow}.svg` | The only brand imagery that exists |
| Public repo | `https://github.com/roselis-lab/keel` — Apache 2.0 | — |

**No logo exists in the sources.** There is no mark, favicon, or wordmark file anywhere in the repo — the product renders its own name as plain type (`<h1>Keel · Threats</h1>`, 15px/700/`-.01em`). This design system does the same, and never draws one. See [Iconography](#5-iconography).

**No webfonts exist in the sources.** The product uses the host OS UI stack. Nothing was substituted — see [Type](#type).

---

## 2. Product context

Keel is an operational layer, not a taxonomy. OWASP LLM Top 10, MITRE ATLAS and CSA MAESTRO are references you *read*; Keel is a model you *run* against a specific system, and edit as your systems change. Three layers:

1. **Reference model** — 13 threats, 71 mitigations, 96 links, already authored in the schema. A floor, not a ceiling.
2. **The framework** — the threat structure (`harm`, `surface`/`source`, `weaknesses`, `reachability`), the mitigation-card model, a hard authoring style guide, and the machinery to extend it (MCP + REST + a browse/edit UI over plain YAML).
3. **The assessor** — skills that walk a real system against the model and emit a two-part output: an auditable analysis trail, then a final risk assessment.

There is no database. The catalog is `catalog/*.yaml`; every write goes back to those files as a readable git diff and ships as a pull request.

### The surfaces this design system covers

Keel has exactly **one UI product**: the authoring UI — a single static HTML file, no build step, served at `localhost:8000/`. It is one app with five screens, so this design system ships **one UI kit** with those five screens rather than several kits.

| Screen | Job |
| --- | --- |
| **Overview** | Landing. Counts, style-guide coverage, "gaps to review" chips that jump to the entity, recent commits. Nothing here blocks anything. |
| **Threats** | Three-pane single-entity editor: filterable list → read/edit form → live preview. Server-validated on every change. |
| **Mitigations** | The same three panes and the same rules, for the 71 `CTRL-*` cards. |
| **Style guide** | Edits the authoring guidance itself. The rail is a field tree with coverage badges; the right pane is a live author preview — the one screen where the third pane earns its column. |
| **Reports** | Assessment output per system, over time: findings ranked by risk, requirement checklists, the assessor dialogue, and a delta against the previous run. |

The **MCP server** and **REST API** are the primary write paths and have no UI. The UI is a review-and-fallback surface — which is why it is *review-first*.

### Governing design principle: review-first

From `docs/plans/2026-08-18-keel-ui-review-first.md`. The fastest way to author the model is to ask an LLM to do it through the MCP tools. So the UI's main job is **reading the model at a glance**, with full CRUD as a complete fallback. Practically:

- Every entity opens in a **read view** first — document-like, per-section surfaces, empty fields omitted — and only becomes a form when you press Edit.
- The read view and the edit form wear the **same block framing** (tint fill, `--border2` hairline, `--r-10`, `--pad-section`), so toggling Edit never makes the eye lose its place.
- **Empty is information.** Unauthored fields are omitted from the read view and re-surfaced as clickable "gaps" chips that jump straight into edit with that field focused.
- **Two feedback channels, never one:** red errors *block* (a value outside a fixed vocabulary, a missing required field); amber advice *never* blocks a save (e.g. a threat whose mitigations are all soft).

---

## 3. Content fundamentals

Keel's copy is written by security engineers for security engineers. It is dense, declarative, and unafraid of a long sentence when the sentence is load-bearing.

### Voice

**Declarative and definitional.** State what a thing *is*, in present tense, without hedging. The README's own opening is the model:

> "A keel is the single load-bearing member that keeps a hull upright and on course with the least material. That is the goal here too: the smallest opinionated structure that holds a GenAI threat model together."

**Second person for instruction, never first.** The docs address *you* ("Ask your agent to do it", "point your agent at the repo's `.mcp.json`") and never say "we" or "I". The product itself is the third-person subject: "Keel reads `catalog/*.yaml` into memory on start."

**Opinionated, with the reasoning attached.** Keel takes positions and immediately shows its work: "A technique such as prompt injection is a mechanism, not a threat: it lives in `source` and `references`, never as a threat or weakness identity." The colon-then-justification shape is everywhere.

**Names its own limits.** "The reference model is deliberately small: the catalog is a floor, not a ceiling." "Roadmap (not yet built): per-system state…" Never overclaims.

### UI copy

- **Sentence case everywhere** for labels, buttons and headings: `New`, `Clear all`, `Filters`, `Select a threat from the list.`, `Gaps to review`. Never Title Case.
- **UPPERCASE + `.08em` tracking is a typographic device, not a copy device** — section labels are authored in sentence case and uppercased by CSS (`text-transform: uppercase`). Keep the source string sentence case.
- **Empty states are one short imperative sentence, ending in a period**: "Select a threat from the list." Filter emptiness is two words: "No matches."
- **Counts are bare and tabular**, no words: `9 / 13`.
- **Validation messages name the field and the rule**, never apologise. Errors are structural facts; advice is a judgement with its reason: *"all mitigations on this threat are soft — nothing gates it."*
- **Buttons are verbs**, one or two words: `Edit`, `Save`, `Delete`, `＋ New`, `Clear all`, `view change`.
- **Toasts are past tense and terse**: "Saved.", "Nothing to save."

### Model prose (the style guide's own rules)

The catalog's authored fields have a house style enforced by `catalog/style_guide/*.yaml` and reviewed by the `check-style` skill:

- **Weakness `text`** is *cause + where + defect*, as one architectural condition — not an attack narrative. Real example: "A reachable tool performs destructive/irreversible or privileged operations (delete, admin, exec, persistent side effects), and the call is initiated by the model with no out-of-model authorization on the action itself."
- **`reachability`** always opens with the same three words — **"NOT applicable if"** — and describes when the path is *not* live, judged on the un-mitigated architecture: "NOT applicable if the reachable tools have no operations with real consequences (read-only, no side effects)…"
- **Mitigation `rationale`** is one line saying *why this control addresses this threat*, starting with the mechanism: "An allowlist of permitted tools limits exposure of destructive operations to only those tools the agent actually needs."
- **Report `scenario`** is a single concrete sentence in the present tense, told as something that happens to a person: "A shopper talks the agent into refunding an order that was never returned; the refund tool fires on model judgement alone and the money leaves before anyone reviews it."
- **Risk `reasoning`** is a comma-chained list of the facts that set the grade: "irreversible money movement, reachable anonymously, and the only thing standing in the way is model judgement."
- **Ids are the vocabulary.** `T-TOOL-ABUSE`, `CTRL-IRREVERSIBLE-ACTION-GUARD`, `agent-environment`, `needs_implementation`. Render them in mono, never prettify them into prose, never Title Case them.

### Absolutes

- **No emoji. Anywhere.** Not in the UI, not in the docs, not in the catalog. The only non-alphanumeric glyphs are functional (see [Iconography](#5-iconography)).
- **One `--amber-700` (#8f6410) was added** as a text-only step: the source's `--amber` (#e0a021) on `--amber-50` fails contrast, and medium-severity text needs to be readable. It is never a fill.
- **No exclamation marks, no marketing adjectives** ("powerful", "seamless", "revolutionary"). The closest the README gets to a boast is "the operational layer that is missing".
- **Lowercase enum values, always** — `wrong-decision`, `needs_implementation`. Hyphens in the model vocabulary, underscores in report status fields; both are quoted verbatim in the UI.
- **Em dashes are used** for the reasoning aside, and heavily — they are part of the house voice, not a tic to remove.

---

## 4. Visual foundations

Keel looks like a professional review tool: a cool navy-on-off-white document surface, one crimson accent, hairlines instead of shadows, and almost no motion. It sits comfortably next to a terminal and a GitHub diff — that is the target register.

### Colour

**Severity is the exception to the one-accent rule — read this first.** On the Reports screen the assessor's whole job is ranking, and crimson cannot mean *selected*, *primary action*, *danger* **and** *critical* at once: if the Edit button is as loud as a critical finding, nothing reads as critical. So severity gets its own **weight ramp**, and it outranks every other use of crimson:

| Level | Treatment | Spine |
| --- | --- | --- |
| **critical** | solid `--crimson-700` fill, white text, 700 | `--crimson-700` |
| **high** | `--crimson-50` wash, `--crimson-700` text, `--crimson-200` border, 700 | `--crimson-600` |
| **medium** | `--amber-50` wash, `--amber-700` text, 600 | `--amber` |
| **low** | `--navy-100` wash, `--navy-600` text, 500 | `--navy-400` |

Three rules follow, and they are load-bearing:

1. **Critical owns the only solid crimson fill on a report screen.** Nothing else may take one.
2. **Classification is neutral.** `harm`, `surface`, `source`, `mitigation_class` and `complexity` are *facts about* a finding, not *grades of* it — render them as neutral `type`/`soft` badges (`--classify-bg`/`--classify-fg`). This is a deliberate departure from the source's `.badge.harm { background: var(--crimson-600) }`, which made every rail row shout.
3. **Low is navy, not green.** Green means *covered / closed*, which is a different axis; a low-severity finding is still an open finding. Grading a finding green would read as "handled".

A ranked list also carries a **4px severity spine** on the left edge of each finding card, so the ordering is legible without reading a word. That is the one place the left-accent border generalises beyond the saved-dialog, and it is functional, not decorative.

**Elsewhere, two hues carry the entire product.** Navy is structure (all text, all chrome, all dividers). Crimson is the *single* accent and it means exactly three things: **selected**, **primary action**, **danger/blocking**. It is never used decoratively. Amber and green are semantic only — amber is non-blocking advice, green is verified/covered/added.

- Background `--bg #f4f6fb` (a cool off-white, never pure white), panels `#fff`, section bands `--tint #f6f8fc`.
- Text runs down the navy ramp by role: `--navy-900` values and headings → `--navy-700` prose → `--navy-500` meta → `--navy-400` placeholders and ids.
- **Selection is a wash plus a rail accent**, not a fill: `background: var(--crimson-50)` + `box-shadow: inset 3px 0 0 var(--crimson-600)`.
- **Diff colours are deliberately not Keel's palette** — they are GitHub's (`#e6ffec` / `#ffeef0` rows, greener/redder gutters). The diff view is quoting another tool's convention on purpose, so a reviewer reads it instantly.
- Max two background colours are ever in play on one screen: the app `--bg` and the panel white, with `--tint` as the band inside them.

### Type

**No webfonts.** The product is one static HTML file with no build step and uses the host OS stack: `-apple-system, "Segoe UI", Roboto, sans-serif`, with `ui-monospace, "SFMono-Regular", monospace` for ids, diffs and field names. **This is not a gap to fill** — it is the correct read for a local dev tool. Nothing has been substituted from Google Fonts, and no font files exist to request.

- Base is `14px / 1.55`. The ramp is narrow and dense: 10, 11, 12, 13, 14, 15, then jumps to 19/20 for entity titles and 24/28 for dashboard numbers. Nothing between 15 and 19 exists.
- **The eyebrow is the signature type treatment**: `11px`, `700`, `uppercase`, `letter-spacing: .08em`, `--navy-700`, no rule underneath. Every section in the app wears one.
- **Mono is a semantic, not a style.** Anything that is an identifier is mono — ids, enum values, field names in the style-guide tree, commit shas, YAML, diffs. Prose is never mono.
- **Every number is `font-variant-numeric: tabular-nums`** — counts, coverage percentages, stat tiles, diff line gutters.
- Tracking tightens on large type (`-.01em` titles, `-.02em` numbers) and opens on uppercase (`.05em`–`.08em`).

### Spacing and layout

One scale, multiples of 4: `4 / 8 / 12 / 16 / 24`, plus three named rhythm tokens — `--field-gap: 24px`, `--section-gap: 44px`, `--input-h: 38px`.

- The app is **one CSS grid, full viewport height**: `grid-template-columns: var(--rail-w) 1fr var(--preview-w)`. It does not scroll as a page; each pane scrolls independently (`overflow-y: auto`, `min-height: 0`).
- **Both side tracks are user-controlled.** The rail collapses to a 44px strip that keeps only the expand affordance (`body.rail-collapsed`). The preview is drag-resized via a 9px fixed hit-strip sitting over the seam, and collapses to `0px` on screens that don't earn it (`body.no-preview`) — Threats and Mitigations read and edit on one surface, so there is nothing for a third pane to duplicate.
- Editor pane padding is `30px 40px`. Rail rows are `10px 15px`. Section bands are `12px 14px`. Cards are `13px 15px`.
- **Fixed elements**: only the resizer, the toast (`bottom: 20px; right: 22px`), and the saved-dialog (same corner, `z-index: 60`).
- Dashboard content uses `.ov-grid2` — a plain `1fr 1fr` grid that collapses to one column at `900px`. That single media query is the only responsive rule in the product; it is a desktop tool.

### Borders, cards and surfaces

**Hairlines do all the work.** Two line weights, and which one you use says where you are: `--border #dfe3ec` on pane edges, control borders and free-standing cards; `--border2 #eef1f7` for dividers *inside* a pane and for the band border on a tint surface.

- **A section band** = `--tint` fill + `1px --border2` + `--r-10` + `12px 14px`. Read view (`.readsec`) and edit form (`fieldset`) use it identically — that is the review-first promise made in CSS.
- **A card on a band** = white fill + `1px --border` + `--r-10` + `13px 15px`. So depth is expressed by *inverting* fill against the band, not by a shadow.
- **A repeatable editor card** (`.ecard`, for weaknesses / mitigation links) = tint fill + `--border` + `--r-10`, collapsible, with a mono summary line. Its border is the *only* heavy container inside a form.
- Radii: `4px` hard badge · `6px` icon hit-area and inline chip · `8px` button, input, banner, diff wrapper · `9px` rail search field · `10px` card, band, toast, tile · `20px` pill chip · `50%` status dot.
- **Left-border accents are functional and rationed**: the green `4px` on the saved-dialog, the `2px navy-200` on `ul.plain` items, and the `4px` severity spine on a ranked finding card. Nothing else. Do not generalise this into a decorative pattern.

### Shadows and transparency

Elevation is **almost entirely absent** — this is a hairline UI. Only genuinely floating layers cast one:

- Toast: `0 8px 24px rgba(20,30,60,.2)`.
- Saved dialog: `0 10px 30px rgba(20,30,60,.18)`.
- Focus ring: `box-shadow: 0 0 0 3px var(--crimson-50)` plus `border-color: --crimson-600`. A wash, not a glow.
- Rail selection: `inset 3px 0 0 var(--crimson-600)`.

**No blur, no backdrop-filter, no translucent overlays anywhere.** Both shadow colours are a navy-tinted black (`rgba(20,30,60,…)`), never neutral. The only opacity use is `opacity: .5` on a disabled primary button.

### Motion

Motion is functional and short, and nothing moves that the user did not cause.

- `transition: background .12s, border-color .12s` on hoverable rows and cards. That is the entire hover vocabulary.
- The toast is the only entrance: `opacity .2s, transform .2s` with an 8px rise (`translateY(8px) → 0`).
- The diff resizer accent fades in over `.12s`.
- **No custom easing curves are declared** — the browser default is used throughout. No bounces, no springs, no scroll animation, no skeleton shimmer, no page transitions. A pane switch is instantaneous.

### Interaction states

- **Hover, on a neutral surface** → fill with `--navy-100`. Rows, commit rows, icon buttons, the facets bar.
- **Hover, on something already accented, or on a jump target** → fill `--crimson-50`, text `--crimson-700`, border `--crimson-200`. Gap chips, jump cards, ov-chips, facet chips.
- **Hover, on a filled primary** → darken to `--crimson-700`. On a ghost button → step `--navy-100` up to `--navy-200`.
- **Hover, on a link-ish control** → `--crimson-700` + `text-decoration: underline`.
- **Selected** → `--crimson-50` wash + the `inset 3px` crimson rail accent, and the hover state is *suppressed* so it doesn't flicker.
- **Focus (form control)** → `--crimson-600` border + the `3px --crimson-50` ring; the rail search field additionally goes from `--tint` to white.
- **Active/selected chip** → solid `--crimson-600` fill, white text, matching border.
- **Disabled** → `opacity: .5`, nothing else.
- **There are no press/`:active` states in the product.** Nothing shrinks, nothing translates on click.

### Imagery

There are exactly three images in the whole codebase: `ui-preview.svg`, `threat-spine.svg`, `assessment-flow.svg` (copied to `assets/`). All three are **flat vector explanatory diagrams** — boxes, labels and arrows in the same navy/crimson/white palette, no gradients, no photography, no illustration style, no texture, no grain. They live centred in the README at `width: 860`, never in the app.

The app ships **zero images**. No full-bleed hero, no background pattern, no empty-state art. An empty state is one line of `--navy-400` text at `margin-top: 22vh`. Do not add imagery to a Keel screen.

---

## 5. Iconography

**Keel has no icon library.** No icon font, no SVG sprite, no PNG icons, no Lucide/Heroicons dependency — the whole app is one HTML file with zero external requests.

Icons are **Unicode glyphs typed directly into the markup**, and there are only a handful. This is the complete inventory found in the source:

| Glyph | Codepoint | Where | Meaning |
| --- | --- | --- | --- |
| `«` / `»` | U+00AB / U+00BB | `.rail-toggle` | Collapse / expand the left rail |
| `▾` / `▸` | U+25BE / U+25B8 | `.fx-caret`, history head | Expanded / collapsed disclosure |
| `＋` | U+FF0B (fullwidth plus) | `＋ New` button | Create. Fullwidth, so it optically matches 13px UI text |
| `×` | U+00D7 | `.cardx` | Remove a repeatable card |
| `ⓘ` | U+24D8, via CSS `content: "\24D8"` | `.fguide > summary::before` | Inline field guidance |
| `·` | U+00B7 | `Keel · Threats` | Separator in the product title |
| `+` / `-` | ASCII | diff content cells | Diff sign, kept in the text and preserved with `white-space: pre` |

Everything else that reads as an icon is **not an icon**:

- **Status is a coloured dot**, drawn in CSS: `content: ""` + `8px` square + `border-radius: 50%`, filled `--crimson-600` (error) or `--amber` (advice), hung off a section label with `margin-left: 8px`.
- **The entity glyph is a letter in a tile**: `.dicon` is a `42×42`, `--r-10`, `--crimson-600` square holding one 20px white character. It is type, not artwork.
- **Severity, coverage, class and status are all badges** — a word in a coloured pill. Keel says the word rather than drawing a symbol for it.

**Rules for this design system:** use the glyphs above verbatim. Do **not** introduce an icon set, do not hand-draw SVG icons, do not substitute a CDN icon library, and never use emoji. If a new affordance needs a symbol, prefer a text label or a badge; if a glyph is unavoidable, take it from the Unicode geometric/arrow blocks already in use.

---

## 6. Intentional additions

The source is a single vanilla-JS HTML file, so it defines *patterns* rather than exported components. Every component in `components/` is a direct extraction of a pattern that exists in `index.html` — same class, same values. Three are wrappers with no single source class, added because the extraction needed a boundary:

- **`Field`** — wraps the `label + .sg-hint + control + .fld-msg` stack that `renderField()` builds inline for every form field. Same markup, given a name.
- **`SectionBand`** — the `.readsec` / `fieldset.slabel` band, which is literally the same surface in two tags. One component, a `variant` prop.
- **`RiskBadge`** — the report screen grades severity/likelihood in prose plus badge classes; this pins the `critical|high|medium|low` weight ramp (see Colour) and exports `SEVERITY_SPINE` for the finding card's left edge, so the ranking treatment cannot drift.

Nothing else was invented. There is no Avatar, Tooltip, Tabs-as-navigation, Accordion, Modal, Breadcrumb-with-dropdown or Pagination component, because Keel has none.

---

## 7. Index

**Root**
- `styles.css` — the global entry point. `@import` lines only.
- `readme.md` — this file.
- `SKILL.md` — Agent Skills front-matter wrapper, for use in Claude Code.
- `thumbnail.html` — the project tile.

**`tokens/`** — `colors.css`, `typography.css`, `spacing.css`, `radii.css`, `elevation.css`, `motion.css`, `layout.css`, `semantic.css`. Author against `semantic.css`.

**`assets/`** — `ui-preview.svg`, `threat-spine.svg`, `assessment-flow.svg`. The only imagery that exists. No logo (none in source).

**`guidelines/`** — foundation specimen cards (Colors, Type, Spacing, Brand groups) shown in the Design System tab.

**`components/`**
| Group | Components |
| --- | --- |
| `core/` | `Button`, `IconButton`, `Badge`, `Chip`, `Dot` |
| `forms/` | `Field`, `TextInput`, `TextArea`, `Select`, `CheckSet`, `SearchInput` |
| `structure/` | `SectionBand`, `Card`, `EditorCard`, `EntityHeader`, `Breadcrumb`, `ScreenTabs`, `RailRow` |
| `feedback/` | `Toast`, `SavedDialog`, `ErrorSummary`, `WarnBanner`, `EmptyState` |
| `data/` | `StatTile`, `CoverageBar`, `SplitBar`, `FacetPanel`, `GapChips`, `DiffView`, `RiskBadge` |

**`ui_kits/authoring-ui/`** — the five real screens: `Overview`, `Threats`, `Mitigations`, `StyleGuide`, `Reports`, wired click-through in `index.html`.

---

## 8. Caveats

- **No logo and no webfonts exist in the source.** Both are correct absences, not omissions to fix. Brand name renders as plain type; type is the OS UI stack.
- The product's colour and spacing values are quoted exactly, including the non-4-multiples (`9px` search radius, `7px 13px` button padding, `38px` control height, `44px` collapsed rail). Do not snap them to a grid.
- Keel's UI is **desktop-only by design**. One media query exists. Do not add responsive breakpoints when composing screens.
