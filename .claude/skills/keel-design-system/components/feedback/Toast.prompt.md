One-sentence what & when: transient confirmation of an action that already happened.

```jsx
<Toast message="Saved." show={visible} />
<Toast message="Validation failed." tone="error" show={visible} />
```

Never use a toast for anything the user must read or act on — that is `SavedDialog` or `ErrorSummary`.
