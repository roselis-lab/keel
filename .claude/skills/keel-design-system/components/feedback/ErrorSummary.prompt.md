One-sentence what & when: above an edit form, listing every blocking error or every piece of amber advice.

```jsx
<ErrorSummary title="2 problems block this save" items={["harm: 'rce' is outside the vocabulary", "weaknesses: at least one required"]} />
<ErrorSummary tone="advice" title="1 thing worth a look" items={["all mitigations are soft — nothing gates this threat"]} />
```

Render both when both exist: errors first, advice second.
