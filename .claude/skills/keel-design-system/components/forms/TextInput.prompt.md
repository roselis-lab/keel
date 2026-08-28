One-sentence what & when: any single-line value in the editor — title, id, reference URL.

```jsx
<TextInput value={t.title} title onChange={e => set("title", e.target.value)} />
<TextInput value={ref.url} mono placeholder="https://…" />
```

Focus is `--crimson-600` border + the 3px `--crimson-50` ring. Never both invalid styling and a focus ring — focus wins.
