One-sentence what & when: the app's only top-level navigation, pinned to the top of the left rail.

```jsx
<ScreenTabs value={screen} onChange={setScreen}
  screens={[["overview","Overview"],["threats","Threats"],["style","Style guide"]]} />
```

Equal-width flex tabs. The switch is instantaneous — no transition.
