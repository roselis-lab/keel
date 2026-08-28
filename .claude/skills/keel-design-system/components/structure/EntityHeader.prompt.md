One-sentence what & when: the top of any entity page — threat, mitigation card, report.

```jsx
<EntityHeader glyph="T" title="Unauthorized or destructive tool action" id="T-TOOL-ABUSE"
  badges={<><Badge tone="harm">code-execution</Badge><Badge tone="type">agent-environment</Badge></>}
  actions={<Button variant="primary">Edit</Button>} />
```

Never put an SVG or emoji in `glyph` — one uppercase letter.
