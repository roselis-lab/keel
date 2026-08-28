One-sentence what & when: the faceted filter under the rail search on the Threats, Mitigations and Style-guide screens.

```jsx
<FacetPanel open={open} onOpen={setOpen} activeCount={2} selected={sel} onToggle={toggle} onClear={clear}
  groups={[{ key: "harm", label: "Harm", options: harmEnum }, { key: "surface", label: "Surface", options: surfaceEnum }]} />
```

Semantics are fixed: OR within a group, AND across groups. It stays collapsed by default — the rail is only 320px.
