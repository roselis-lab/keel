One-sentence what & when: the rail's text filter, directly under the rail header and above the facet panel.

```jsx
<SearchInput placeholder="Filter threats…" value={q} onChange={e => setQ(e.target.value)} />
```

It is 9px radius (not 8) and tint-filled at rest — the only control in Keel that changes background on focus. Search matches id, title, weakness text and reachability.
