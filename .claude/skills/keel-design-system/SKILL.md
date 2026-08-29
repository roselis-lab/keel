---
name: keel-design
description: Use this skill to generate well-branded interfaces and assets for Keel, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for protoyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Quick orientation

Keel is a framework for building and running your own living GenAI/LLM threat model. Its one UI product is a five-screen authoring app (Overview, Threats, Mitigations, Style guide, Reports) served as a single static HTML file.

Non-negotiables, all documented in `readme.md`:

- **Two hues.** Navy is structure and text; crimson is the *only* accent and means exactly selected / primary action / danger. Amber advises, green passes. Never decorative colour.
- **No webfonts.** OS UI stack for prose, OS mono for anything that is an identifier. Mono is a semantic, not a style.
- **No icon set, no emoji, no SVG icons.** A handful of Unicode glyphs (`« » ▾ ▸ ＋ × ⓘ ·`), plus letters-in-tiles and CSS dots. The full inventory is in readme.md → Iconography.
- **Hairlines, not shadows.** Only the toast and the saved-dialog cast one. No blur, no backdrop-filter, no translucency.
- **Almost no motion.** `.12s` hover on background and border-color, one `.2s` toast rise. No custom easing, no press states.
- **Review-first.** Every entity reads before it edits, and both wear the same section band. Empty fields are omitted and re-surfaced as gap chips. Red errors block a save; amber advice never does.
- **Sentence case everywhere.** Buttons are verbs. Toasts are past tense. Ids and enum values are quoted verbatim and lowercase.
- **No logo exists.** Render "Keel" as plain type wherever a mark would go. Never draw one.

## Where the product has moved past this system

The kit was extracted from `keel/static/index.html` and describes it as it stood. Five things have since changed in the product; when they disagree, **`index.html` wins** and the note below says why.

- **Section headings are a real tier, not the eyebrow.** `readme.md` says every section wears an 11px uppercase eyebrow. That put section headings a step *below* the 14px prose they introduce, so the screens read as one flat block of text. Section headings (`h3.slabel`, `.detail fieldset > legend.slabel`) are now 15px / 600, sentence case, navy-900. The eyebrow survives only where it labels a single field or group: facet keys, sub-labels inside a repeatable card, the rail list label, the finding chain's `<dt>`.
- **Severity has three bands, not four.** `critical` is gone from `keel/schemas/report.py` and from the tokens. An organisation's risk policy is written against three bands, and a fourth level only ever meant "high, but really". `high` now takes the solid crimson fill that `critical` had, and it is the only solid fill on a finding — likelihood is graded on the same ramp but drawn as an outline (`.sev.quiet`), so one card never shows two solid crimson blocks.
- **Primary navigation is a top bar, not a strip in the rail.** Five text tabs stretched across a 320px rail read as a cramped segmented control and pushed the rail's own header into a second squeezed row. The tabs also now survive collapsing the rail.
- **navy-400 is not a text colour.** It measures 2.62:1 on white. It stays in the ramp for rules, dots and the low severity spine; text that used it moved to navy-500, which was itself darkened to `#636e88` so the quiet tier clears 4.5:1 on all four Keel surfaces. `--green-700` was added as green's text-only step, mirroring `--amber-700`. Badges are 11px, not 10.
- **Prose has a measure.** Body copy caps at `var(--measure)` (74ch). The editor pane is `1fr` and runs to the full width of a large display.
- **The type ramp is referenced, not retyped.** Every `font-size` and `line-height` in `index.html` is `var(--fs-*)` / `var(--lh-*)`; there is not one raw value outside `:root`. A ramp only declared in `:root` is a suggestion — the app had 117 raw sizes against 6 token uses, and eight line heights against four tokens. Line heights are now exactly five: `--lh-1`, `--lh-tight` 1.35, `--lh-base` 1.55, `--lh-prose` 1.65. Form controls inherit type (`button, input, select, textarea`), because without that any control missing an explicit size falls through to the browser's 13.333px, which is not on the ramp and cannot be reached from it.

## Where things are

- `styles.css` — link this one file; it imports every token file.
- `tokens/semantic.css` — author against these aliases (`--text-body`, `--surface-section`, `--accent`, `--status-advice`), not the raw ramps.
- `components/` — 30 primitives in five groups (`core`, `forms`, `structure`, `feedback`, `data`), each with a `.d.ts` props contract and a `.prompt.md` usage note.
- `ui_kits/authoring-ui/` — the five real screens, click-through. Read this before recreating any Keel view.
- `guidelines/` — foundation specimen cards.
- `assets/` — the three flat vector diagrams that exist. The app itself ships zero images.
