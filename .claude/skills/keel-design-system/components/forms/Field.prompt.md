One-sentence what & when: wraps every form control with its label, its single hint line and its validation channel.

```jsx
<Field label="Reachability" hint="When is this NOT a live path?" advice="No carve-out authored yet.">
  <TextArea rows={4} value={v} onChange={set} />
</Field>
```

Space fields `--field-gap` (24px) apart. Never show an error and advice at once — error wins.
