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

## Where things are

- `styles.css` — link this one file; it imports every token file.
- `tokens/semantic.css` — author against these aliases (`--text-body`, `--surface-section`, `--accent`, `--status-advice`), not the raw ramps.
- `components/` — 30 primitives in five groups (`core`, `forms`, `structure`, `feedback`, `data`), each with a `.d.ts` props contract and a `.prompt.md` usage note.
- `ui_kits/authoring-ui/` — the five real screens, click-through. Read this before recreating any Keel view.
- `guidelines/` — foundation specimen cards.
- `assets/` — the three flat vector diagrams that exist. The app itself ships zero images.
