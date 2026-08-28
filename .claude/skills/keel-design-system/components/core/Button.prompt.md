One-sentence what & when: Keel's only button — use `primary` for the single crimson action on a screen, `ghost` for everything else, `bare` for toolbar-style controls.

```jsx
<Button variant="primary" onClick={save}>Save</Button>
<Button size="sm" glyph="＋">New</Button>
<Button variant="primary" disabled>Save</Button>
```

Variants: `primary` (crimson-600 → 700 on hover, white text), `ghost` (navy-100 → navy-200), `bare` (transparent → navy-100). Sizes `md`/`sm`. Disabled is `opacity: .5` only — there is no press state in Keel.
