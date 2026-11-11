# Keel reading app: design rules

The reading app (`web/`, React) is what people open: the assessor, the product team that owns an assessed system, and whoever asks whether the company is compliant. Threats, controls, reports and the style guide are read and edited here. The older single-file editor (`keel/static/index.html`) is still served at bare `/edit`, but nothing in the app links to it. Where the two disagree, this file wins.

## Build and serve

- `cd web && npm ci && npm run build` writes `keel/static/app`, which is committed so `keel up` needs no Node. CI rebuilds and fails if the committed build is stale.
- `npm run dev` serves the app with hot reload and sends `/api` to a running `keel up` on port 8420.
- `keel/main.py` serves `/assets/*` from the build (a missing file is a 404, never the app), bare `/edit` the old editor, every `/edit/…` path it used to own (threats, mitigations, reports, style guide) as a redirect (308) to the same record in the app, and the app's `index.html` for every other path the API did not claim.

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

## The library: threats and controls

The owner's jobs here: find a record by a word he remembers, see what answers a threat and go there and back, add or fix a record without leaving the app. Rules follow MITRE ATT&CK (links both ways, each with its reason; breadcrumbs), Vanta and Notion (search in the list itself; filters by a related gap), and Linear / Notion side peek (the list stays beside the open record).

- **A list is a table with a search box above it.** Search matches as you type (title, id, harm, weak spots and linked control names for threats; name, kind, purpose for controls); `/` puts the cursor in it. Search, filters and sort live in the address, so going back from a record lands on the same narrowed list.
- **A list table gives its first column every spare pixel.** Other columns are `width: 1%` and as wide as their content, never a fixed width. Fixed widths broke the threat title over five lines at tablet width while an empty "Found in" kept 200px. On a phone a row is the title, then one quiet line of facts joined by " · ".
- **A record keeps the list beside it** (from 1024px): a Threats / Controls switch, a search box, the open record highlighted and kept in view. j / k and the Previous / Next pair at the foot step through the list. From 1280px the record's own sections are listed on the right.
- **A link reads the same from both ends.** A threat lists the controls that stop it and those that reduce it, each with its reason; a control opens on "Closes", the threats it answers, with the same reason. Arriving at a control from a threat puts "← that threat" in the breadcrumb.
- **Editing is a page of the app** (`/threats/:id/edit`, `/threats/new`, `/controls/:id/edit`, `/controls/new`, `/reports/new`, `/reports/:system/:date/edit`, `/style-guide/:entity` and `/style-guide/:entity/:field`), laid out under the same headings as the card it edits. Each field: label, the first sentence of its style-guide purpose, the input, and "How to write it" folded. Errors (red) come from the server's own validator as you type, shown once a field is touched or a save is tried; advice (amber) never blocks a save.
- **One save bar, always at the foot:** state (no changes / unsaved / N to fix / saving), Delete with an in-place "for good?", Discard or Close, Save. An edit sends only the fields that changed, so a save rewrites one line of YAML, not the file.
- **A report is saved whole** (the API takes the document), and editing a final report makes it a draft again; the save says so. Finalize asks in place and, when refused, lists the first three gaps and folds the rest.
- **A style-guide editor shows what the author will see** at the top, built from the draft as you type.
- **Where you came from lives in the address** (`/controls/X?from=T-Y`), so the way back survives a reload and a link opened in a new tab.
- **A control's links are written on the threat.** From the control's editor, linking or unlinking a threat is saved at once and says so; everything else waits for Save.

## Responsive

- Laptop and wide: rail, main column (prose capped near 80ch), and an in-page contents column from 1280px.
- Below 1024px the contents column goes; below 760px the rail goes and tables turn into labelled rows (`data-l` on each cell). The top menu scrolls sideways with a fade and keeps the current section in view.
- Check at 375, 1280 and 1440 before calling a page done.
