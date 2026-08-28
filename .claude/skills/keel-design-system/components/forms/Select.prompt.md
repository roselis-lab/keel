One-sentence what & when: any single-value enum field — `harm`, `nature`, `strength`, `mitigation_class`, `status`.

```jsx
<Select value={t.harm} options={harmEnum} placeholder="— select —" onChange={e => set(e.target.value)} />
```

A value outside the vocabulary is a red blocking error, not amber advice.
