One-sentence what & when: grades a report finding so a ranked list reads at a glance.

```jsx
<RiskBadge level="critical" prefix="severity" />
<RiskBadge level="low" prefix="likelihood" />
```

**The severity spine** — the 4px left edge that makes a ranked list legible without reading. The colour lives in the tokens, so take it from there rather than from a JS map:

```jsx
<div style={{ borderLeft: "4px solid var(--sev-" + f.severity + "-spine)" }}>…</div>
// or, equivalently:
<SeveritySpine level={f.severity}>…</SeveritySpine>
```

**Severity is the only coloured thing on a finding.** Harm, surface, source and complexity are facts about the finding, not grades of it — render them as `<Badge tone="type">`. Critical owns the solid crimson fill; if anything else on the screen is solid crimson, critical stops reading as critical.

Rank findings critical → high → medium → low. Levels come verbatim from the report YAML.
