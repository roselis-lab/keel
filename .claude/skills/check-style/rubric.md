# Review procedure — check content against the style guide

**The authoring rules are NOT in this file.** They live in the **style guide** (the single, forkable source of truth). This file is only *how to apply* them, plus the few cross-field invariants that no single field's bar can express. Re-encoding field rules here would create a second source of truth that drifts from the style guide.

---

## A. Per-field — check each field against its style-guide bar

For the threat under review:

1. Fetch the bar: `get_style_guide(entity_type="threat")` (and for the sub-entities `weakness`, `mitigation_link`). Each field returns `purpose`, `content_requirements`, `avoid`, `examples`.
2. For each field that has content, rate **PASS / MINOR / FAIL** against *its own bar* — nothing invented here.
3. If a field's content is wrong but the bar is **silent** on the rule, flag the **bar** (a style-guide gap), not the entry. The fix then is to the style guide, not the threat.

Output line:
```
THREAT_ID | field | PASS/MINOR/FAIL | current | expected (per bar) | reason
```

The rules you'll be applying (weakness = architectural condition, `reachability` = "NOT applicable if…", `nature` targeted/secondary, `strength` gating/soft, avoid a technique or consequence in `weakness`, etc.) are authored **into the style guide** — that is where to read and, if wrong, edit them.

---

## B. Judgement invariants — checked here (no single field's bar can hold them)

These need reading the whole threat and judging coherence — they cannot be a per-field bar:

1. **Reachability ↔ weaknesses coherence.** Closing any `targeted` weakness should make a `reachability` carve-out fire. If it doesn't, the weakness/reachability pair is incoherent.
2. **Source completeness.** If the threat is real without an attacker, `source` must include the non-attacker cause (`hallucination` / `error` / `accident`).

*(The deterministic invariants — ≥1 `gating` for a blockable threat, and "no technique as `title`/`weakness`/`harm`" — are lints and live in `uv run keel validate`, not here.)*

End with the threat's verdict: **PASS** (all per-field PASS + both invariants hold) or **FAIL** (any critical, or ≥2 major).
