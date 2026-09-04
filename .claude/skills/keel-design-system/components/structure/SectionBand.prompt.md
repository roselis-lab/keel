One-sentence what & when: every band on an entity page — read sections and edit fieldsets alike.

```jsx
<SectionBand label="Reachability" sub="when it is NOT a live path">
  <p style={{ color: "var(--text-body-read)" }}>{t.reachability}</p>
</SectionBand>
<SectionBand as="fieldset" label="Weaknesses" count="4">…</SectionBand>
```

Omit the band entirely when the field is unauthored — surface it as a gap chip instead.
