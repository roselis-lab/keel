One-sentence what & when: each entry of a repeatable array in the edit form, collapsible so a long threat stays scannable.

```jsx
<EditorCard summary="tool · targeted" open={open} hasError onToggle={t} onRemove={rm}>
  <Field label="Component"><Select options={componentEnum} /></Field>
</EditorCard>
```

Collapsed cards must still advertise a hidden error — that is what `hasError` is for.
