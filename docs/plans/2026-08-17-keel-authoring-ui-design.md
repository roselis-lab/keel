# Keel authoring UI — design

Date: 2026-08-17. Branch: threat-model-v2.

## What this covers

Three pieces of work, designed together because they share one surface:

1. Publish a JSON Schema generated from the models (powers the browser forms, IDE autocomplete, and stays in lockstep with the model).
2. Rebuild the browse/edit screen as schema-driven forms with the style-guide bar shown inline as you write.
3. Build a style-guide editor — the screen where a maintainer edits the authoring standard itself.

The goal behind all three is the one the user named: Keel lives as a Git repository people contribute to, so the model must stay homogeneous and held to the same standard by everyone. The design keeps the guidance next to the writing, keeps structure and guidance as two separate channels, and keeps the whole thing forkable (clone-and-run, no build step).

## Research basis

The design is not invented; every load-bearing choice copies a tool that does this well. The closest analogs, and what each settled:

- AWS Threat Composer (the closest analog — guided authoring of a threat). Structured fields compose into a live readable statement; you can start from any field; per-field examples plus a "give me an example" button kill the blank page; an Insights panel nudges on coverage (threats with no mitigation, unprioritized) rather than blocking. Built on the AWS CloudScape design system, whose attribute-editor gives the repeatable-row pattern (a card per row, remove in the corner, an Add button under the group).
- Semgrep Editor/Playground. Three horizontal panes — a library rail, the rule editor, and a test/results pane. The editor toggles between a guided Structure view and raw YAML, and the two stay in sync. Each rule element carries a small status badge (a match count) right on the row. Save/share live in a top menu.
- Elastic detection-rules + Kibana. The same rules exist as raw files (git, pull requests, CI checks) and as a GUI wizard; even the as-code path does not hand-write files (Elastic calls that "error-prone and tedious") and instead prompts field by field. Kibana's Rule Preview is a resizable panel beside the form that shows what the rule would catch, at any step, before saving, with a colour change when the preview goes stale.
- GOV.UK design system. Field order is label, then hint, then input, then error — hint above the field, not below it as fine print. Text columns stay around two-thirds width for readability. Errors appear twice, worded identically: a summary at the top and inline at the field. No asterisks for required fields.
- Sanity and Vale. Blocking errors and non-blocking advice are two separate channels — errors stop you, style advice only nudges. Vale is the model for surfacing a written style guide as live, per-item hints.
- Backstage / Threat Dragon / Threagile. File-backed tools delegate approval to Git pull requests with required checks and code-owner review, rather than building a bespoke in-app approval queue. Backstage's template editor is the precedent for "edit the definition on one side, preview the resulting form on the other."

## Stack decision

Plain vanilla JavaScript, no build step, forms hand-rolled from the schema.

Reasoning as the product decision: Keel's pitch is clone-it-and-run for security teams who fork it, and a build toolchain (React, a form library, npm) fights that. The entity set is tiny and fixed — threat, weakness, mitigation-link, mitigation — so a form library is more machinery than the problem needs. The one real cost, writing the field rendering ourselves, is small at this size and keeps the repo openable by a security team with no front-end background. This is deliberately not the React/RJSF path the analogs use, because their scale and audience differ from ours.

## Shared shape

Both screens use the same three panes, left to right: a list to pick from, the thing you are editing in the middle, and a live preview on the right. Learn it once, use it in both places.

Two views of the same entry, kept in sync: a guided form and the raw YAML, toggled at the top. Nobody is forced to hand-edit raw structure, and nobody is prevented from seeing the exact file and diff before a pull request.

Two feedback channels, never mixed:

- Structure (blocking). Checked against the JSON Schema. Missing required field, a value outside a frozen vocabulary, a mitigation id that does not resolve. Shown red, and it blocks save.
- Guidance (advice). Fetched live from the style-guide service. "This title looks like a technique, not an outcome." Shown amber next to the field, and it never blocks save. The deep read stays with the check-style skill (an LLM judging prose against the guide), not something the browser tries to decide.

## Screen 1 — browse and edit a threat

Left pane, the library rail: a searchable, filterable list of threats. Filter by the frozen vocabularies (harm, surface, source, component) and by tag. Click to open in the middle; a New threat button starts a blank one, offering a worked example as a starting point.

Middle pane, the form: one field per row in schema order — title, harm, surface, source, weaknesses, reachability, mitigations, references, tags. Frozen-vocabulary fields render as dropdowns or checkbox sets straight from the schema enums, so an invalid value cannot be typed. Free-text fields are plain text areas kept to a readable width. Weaknesses and mitigations are repeatable cards — a card per row with remove in the corner and an Add button beneath the group (the CloudScape attribute-editor pattern).

The style-guide bar is the point of the screen. Each field shows a one-line hint above the input at all times. Focusing the field expands its full bar beside the input — purpose, what to include, what to avoid, an example with a "use example" button — and collapses it when you move on. This is GOV.UK's rule: guidance before you type, not fine print after. The bar's content is fetched live from the style-guide service, so it is always the current standard and never a hardcoded copy that drifts.

Each row carries a status badge, the way Semgrep marks each rule element: green valid, amber style advice, red blocking. On save failure, a summary at the top lists the blocking errors in the same words as the inline messages, and focus moves to it.

Validation fires on blur with a short debounce, never on every keystroke.

Right pane, the live preview: as fields fill, it renders the threat the way a person reads it — the title, the one-line harm, the weaknesses as plain sentences, which mitigations are gating versus soft, and the "not applicable if" carve-out. Below it, an Insights strip nudges softly: no references yet, no gating mitigation, and similar — copied from Threat Composer's Insights, never blocking.

The raw-YAML toggle swaps the form for the raw file for that threat, editable, same validation. Edit in either; they are the same data underneath.

Save writes the YAML patch to the file (what the store already does), then surfaces the next step: commit and open a pull request, with an Edit on GitHub link as the alternative.

## Screen 2 — edit the style guide

Same three panes, so nothing new to learn.

Left pane: the entity-and-field tree, generated from the schema so it can never drift from the model. Each field shows a coverage badge. A field whose schema entry was removed but still has guidance shows as an orphan to clean up; a new field with no guidance shows 0% so it cannot hide.

Middle pane: the bar's slots for the selected field as editable fields — purpose, include, avoid, example, and the optional instructions.

Right pane: a live preview of exactly what an author will see when they focus that field on screen 1, plus that field's coverage. This is Backstage's "edit the definition, preview the resulting form" applied to us, so the person writing the standard sees the result immediately.

Save is the same pull-request handoff as screen 1.

## Task 1 — the JSON Schema plumbing

One generated file per entity — schema/threat.schema.json, schema/mitigation.schema.json, and the style-guide shape — produced straight from the Pydantic models with model_json_schema(). Generated, never hand-written, so it cannot drift from the model. A small command (keel schema) writes them; CI checks they are up to date.

It earns its place three ways:

- The browser forms read it to know the fields, types, what is required, and the frozen vocabularies. Because those vocabularies are fixed lists in the model, they arrive as enums and become the dropdowns automatically, so the form matches the model for free.
- Hand-editing the YAML gets autocomplete and inline errors in the editor through a one-line schema header, for the fork-and-hand-edit crowd.
- CI keeps using keel validate (Pydantic, which is stricter) as the real gate; the JSON Schema is the browser and editor surface. Same source, so they cannot diverge.

The split runs through the whole design: JSON Schema carries structure and blocking errors; the style-guide service carries guidance and advice. That is the same two channels the edit screen shows — red blocks, amber nudges.

## Contribution and review

Keel is a Git repository people contribute to, so the honest path is local-first plus a pull request, not a hosted content system.

The loop: clone or pull, run Keel locally, edit in the UI (which writes YAML patches) or hand-edit the YAML, then commit and open a pull request. Every override or dismissal keeps a required reason field — a rule the threat-modeling tools all follow.

Review happens on GitHub: a required check runs keel validate on the pull request, and a code owner approves. No bespoke approval queue.

## Anti-patterns to avoid (called out by the research)

- Errors that flash mid-typing. Validate on blur, debounced.
- A blank page with no example or purpose. Never show an empty field with no hint and no example.
- The same error worded two different ways, or free text where a fixed list belongs. Keep summary and inline identical; make invalid states unconstructable where a dropdown can.

## Build order

1. JSON Schema generation and the keel schema command, plus the CI freshness check.
2. Screen 1 (browse and edit) against the schema, with the style-guide bar, two feedback channels, live preview, and the raw-YAML toggle.
3. Screen 2 (style-guide editor) reusing screen 1's parts.
4. The save-to-pull-request handoff and the Edit on GitHub link.
