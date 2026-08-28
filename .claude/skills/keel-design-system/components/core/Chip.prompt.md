One-sentence what & when: a filter chip inside a facet group, or a mono jump-chip that navigates to an entity id.

```jsx
<Chip selected onClick={toggle}>data-exposed</Chip>
<Chip variant="jump" onClick={() => go("T-DOS")}>T-DOS</Chip>
```

Facets are OR within a group and AND across groups — the chip only renders state, the parent owns the set.
