One-sentence what & when: at the bottom of a read view, or in the Overview's "gaps to review" panel.

```jsx
<GapChips items={["references", "tags"]} onPick={f => editWithFocus(f)} />
<GapChips label="Threats with no mitigation" items={["T-DOS", "T-TOXIC"]} onPick={go} dashed={false} />
```

Nothing here blocks anything — it is a place to see where the model is thin.
