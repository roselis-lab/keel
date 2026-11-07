# Keel reading app: design rules

The reading app (`web/`, React) is what people open: the assessor, the product team that owns an assessed system, and whoever asks whether the company is compliant. The older library editor (`keel/static/index.html`) is served under `/edit` and still follows `.agents/skills/keel-design-system`. Where the two disagree on a reading page, this file wins.

## Build and serve

- `cd web && npm ci && npm run build` writes `keel/static/app`, which is committed so `keel up` needs no Node. CI rebuilds and fails if the committed build is stale.
- `npm run dev` serves the app with hot reload and sends `/api` to a running `keel up` on port 8420.
- `keel/main.py` serves `/assets/*` from the build (a missing file is a 404, never the app), `/edit` and `/edit/*` the editor, and the app's `index.html` for every other path the API did not claim.

## Look: Signal in Graphite

Hazard-label conventions on graphite paper. The owner chose the palette on 7 Nov 2026.

- **Colour means risk and nothing else.** `--hi #C42B1C` high, `--md #B26A00` medium, `--lo #2A63A8` low, `--ok #2E6B4F` met / in place. Structure is graphite: `--paper #F2F2EF`, `--card #FFF`, `--inset #E5E5E0`, `--rule #CBCBC4`, `--ink #151718`, `--ink-2 #43464A`, `--ink-3 #62666B`, top bar `--shell #23272B`. No brand accent.
- **Type.** Barlow for text, Barlow Condensed uppercase for headings. Barlow has no Cyrillic, so Fira Sans / Fira Sans Condensed load their Cyrillic subset only and Russian reports read in the same voice. Self-hosted through `@fontsource`; no font CDN.
- **Every page head** sits under a 6px ink rule. Section heads have a 2px ink rule under them.
- **Severity is a shape and a word** (diamond high, triangle medium, ring low), never colour alone. The one solid colour block is the hazard label for severity; likelihood sits beside it as text. Severity and likelihood are never folded into one grade.

## Content rules

- **Titles lead; IDs follow.** A threat or finding is named by its title. The ID is small grey text at the end of the meta line, there for whoever matches it against YAML.
- **Every page answers its reader's first question in its first line.** Report: how many risks, how many high, how many fixes close the high ones. Compliance: how many entries are not met.
- **Work first, method folded.** A report opens on "Fix these first", then risks, then all fixes. How it was assessed (waiting, ruled out, surfaces, questions, evidence) is folded at the foot.
- **One view per page.** There is no audience switch. The local app is the assessor's full view; the product team gets the export ("Share with the team": Confluence page and one Jira ticket per fix, a single-file page, or a link).
- **Empty is said once.** A card with nothing written says what is missing in one line and links to the editor, instead of rendering empty panels.
- **Compliance is computed, not stored.** `keel/services/compliance_service.py` works it out from coverage and the latest report on every request. Each coverage source says what it is (`kind`: regulation, standard or best practice). Compliance shows regulations and standards first and best practice apart, so a gap against a threat list never reads as a breach; Coverage groups the library's sources the same way.

## Responsive

- Laptop and wide: rail, main column (prose capped near 80ch), and an in-page contents column from 1280px.
- Below 1024px the contents column goes; below 760px the rail goes and tables turn into labelled rows (`data-l` on each cell). The top menu scrolls sideways with a fade and keeps the current section in view.
- Check at 375, 1280 and 1440 before calling a page done.
