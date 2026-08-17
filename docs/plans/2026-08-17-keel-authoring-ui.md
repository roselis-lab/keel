# Keel authoring UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the schema-driven browse/edit screen and the style-guide editor described in the design doc, backed by a JSON Schema generated from the Pydantic models and one server-side validator that feeds two feedback channels (blocking structure errors vs. non-blocking advice).

**Architecture:** The Pydantic models stay the single source of truth. A generator turns them into JSON Schema files under `schema/`, checked fresh in CI. A single `POST /threats/validate` endpoint runs Pydantic (structure errors) plus the existing lints (advice), so the browser never re-implements validation. The UI is one vanilla, no-build `index.html` with two screens sharing a three-pane layout (list / editor / live preview); it reads the JSON Schema to render fields and the frozen-vocabulary dropdowns, and the style-guide service for the inline guidance bars. Saves write YAML patches (the store already does this) and then prompt the user to open a pull request.

**Tech Stack:** Python 3.14, Pydantic v2, FastAPI, PyYAML, pytest (back end, TDD). Vanilla HTML/CSS/JavaScript, no build step, no new runtime dependency (front end, manual verification — there is no JS test harness and adding one would break clone-and-run).

**Design doc:** `docs/plans/2026-08-17-keel-authoring-ui-design.md`

---

## Conventions for the executor

- Run back-end tests with the project venv: `.venv/Scripts/python -m pytest -q` (Windows) and `ruff check keel tests` before each commit.
- Every back-end task is test-first: write the failing test, watch it fail, implement, watch it pass, commit.
- Front-end tasks have no automated test. Each ends with a **Verify** block: exact steps to run the app (`.venv/Scripts/python -m uvicorn keel.main:app --port 8000`), what to click, and what you must see. Do not commit a front-end task until its Verify block passes.
- Keep prose values one line (no hard wrapping) to match the repo's YAML style.
- Commit after every task with the message shown.

---

## Milestone 1 — JSON Schema from the models

### Task 1: Generate the JSON Schema in memory

**Files:**
- Create: `keel/schema_export.py`
- Test: `tests/test_schema_export.py`

**Step 1: Write the failing test**

```python
# tests/test_schema_export.py
from keel.schema_export import build_schemas


def test_threat_schema_has_frozen_vocab_enums():
    schemas = build_schemas()
    threat = schemas["threat"]
    assert threat["properties"]["harm"]["enum"] == [
        "wrong-decision", "data-exposed", "code-execution", "downtime", "reputation-legal",
    ]
    assert "title" in threat["required"]
    # weaknesses must carry its sub-schema so the UI can render the repeatable card
    assert threat["properties"]["weaknesses"]["type"] == "array"


def test_build_schemas_covers_all_entities():
    schemas = build_schemas()
    assert set(schemas) == {"threat", "mitigation", "weakness", "mitigation_link"}
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_schema_export.py -q`
Expected: FAIL (`ModuleNotFoundError: keel.schema_export`).

**Step 3: Write minimal implementation**

```python
# keel/schema_export.py
"""Generate JSON Schema from the Pydantic models — the single structural source the
browser forms and IDE autocomplete read. Generated, never hand-written, so it cannot
drift from the models."""
from __future__ import annotations

from typing import Any

from keel.schemas.mitigation import MitigationCreate
from keel.schemas.threat import MitigationLink, ThreatCreate, Weakness


def build_schemas() -> dict[str, dict[str, Any]]:
    """Return {entity: json_schema} for every authorable entity."""
    return {
        "threat": ThreatCreate.model_json_schema(),
        "mitigation": MitigationCreate.model_json_schema(),
        "weakness": Weakness.model_json_schema(),
        "mitigation_link": MitigationLink.model_json_schema(),
    }
```

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_schema_export.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/schema_export.py tests/test_schema_export.py
git commit -m "feat: generate JSON Schema from the models"
```

---

### Task 2: Write the schema files to disk with a stable serialization

**Files:**
- Modify: `keel/schema_export.py`
- Test: `tests/test_schema_export.py`

**Step 1: Write the failing test**

```python
def test_write_and_check_roundtrip(tmp_path):
    from keel.schema_export import write_schemas, schemas_are_fresh
    out = tmp_path / "schema"
    write_schemas(out)
    assert (out / "threat.schema.json").is_file()
    assert schemas_are_fresh(out) is True
    # a stale file is detected
    (out / "threat.schema.json").write_text("{}", encoding="utf-8")
    assert schemas_are_fresh(out) is False
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_schema_export.py -q`
Expected: FAIL (`ImportError: cannot import name 'write_schemas'`).

**Step 3: Write minimal implementation** (append to `keel/schema_export.py`)

```python
import json
from pathlib import Path

DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _serialize(schemas: dict[str, Any]) -> dict[str, str]:
    """entity -> file text. Sorted keys + trailing newline for stable diffs."""
    return {
        entity: json.dumps(schema, indent=2, sort_keys=True) + "\n"
        for entity, schema in schemas.items()
    }


def write_schemas(out_dir: Path = DEFAULT_SCHEMA_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for entity, text in _serialize(build_schemas()).items():
        (out_dir / f"{entity}.schema.json").write_text(text, encoding="utf-8")


def schemas_are_fresh(out_dir: Path = DEFAULT_SCHEMA_DIR) -> bool:
    """True when the on-disk files match what the models would generate right now."""
    for entity, text in _serialize(build_schemas()).items():
        path = out_dir / f"{entity}.schema.json"
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            return False
    return True
```

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_schema_export.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/schema_export.py tests/test_schema_export.py
git commit -m "feat: write JSON Schema files with a stable, diffable serialization"
```

---

### Task 3: Wire `keel schema` and `keel schema --check` into the CLI

**Files:**
- Modify: `keel/mcp/server.py:99-116` (the `main()` arg dispatch)
- Test: `tests/test_schema_cli.py`

**Step 1: Write the failing test**

```python
# tests/test_schema_cli.py
import subprocess
import sys


def test_schema_check_passes_after_write(tmp_path):
    # writing then checking in the same dir must succeed
    from keel.schema_export import write_schemas, schemas_are_fresh
    write_schemas(tmp_path)
    assert schemas_are_fresh(tmp_path)


def test_cli_schema_check_exit_code():
    # the committed schema/ must be fresh, so --check exits 0
    r = subprocess.run(
        [sys.executable, "-m", "keel", "schema", "--check"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_schema_cli.py -q`
Expected: FAIL (the second test fails — `schema` subcommand not handled, and `schema/` not committed yet).

**Step 3: Write minimal implementation** (in `keel/mcp/server.py`, extend `main()`)

```python
    if args and args[0] == "schema":
        from keel.schema_export import DEFAULT_SCHEMA_DIR, schemas_are_fresh, write_schemas

        if "--check" in args:
            if schemas_are_fresh():
                print("Schema files are fresh.", file=sys.stderr)
            else:
                print("Schema files are stale — run `keel schema`.", file=sys.stderr)
                raise SystemExit(1)
        else:
            write_schemas()
            print(f"Wrote JSON Schema to {DEFAULT_SCHEMA_DIR}", file=sys.stderr)
        return
```

Place this branch before the `validate` branch. Then generate the files once:
`.venv/Scripts/python -m keel schema`

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_schema_cli.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/mcp/server.py tests/test_schema_cli.py schema/
git commit -m "feat: keel schema command; commit generated schema files"
```

---

### Task 4: Serve the schema over HTTP and add the CI freshness gate

**Files:**
- Modify: `keel/routes/library.py` (add a schema route)
- Modify: `.github/workflows/ci.yml` (add `keel schema --check`)
- Test: `tests/test_schema_route.py`

**Step 1: Write the failing test**

```python
# tests/test_schema_route.py
from fastapi.testclient import TestClient

from keel.main import app


def test_schema_endpoint_returns_threat_schema():
    client = TestClient(app)
    r = client.get("/schema/threat")
    assert r.status_code == 200
    assert r.json()["properties"]["harm"]["enum"][0] == "wrong-decision"


def test_schema_endpoint_unknown_entity_404():
    client = TestClient(app)
    assert TestClient(app).get("/schema/nope").status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_schema_route.py -q`
Expected: FAIL (404 for `/schema/threat`).

**Step 3: Write minimal implementation** (append to `keel/routes/library.py`)

```python
from keel.schema_export import build_schemas


@router.get("/schema/{entity}")
async def get_schema(entity: str):
    schemas = build_schemas()
    if entity not in schemas:
        raise HTTPException(status_code=404, detail=f"unknown entity {entity!r}")
    return schemas[entity]
```

Then add to `.github/workflows/ci.yml`, in the same job that runs `keel validate`, a step before it:

```yaml
      - name: Check generated schema is fresh
        run: python -m keel schema --check
```

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_schema_route.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/routes/library.py .github/workflows/ci.yml tests/test_schema_route.py
git commit -m "feat: serve schema over HTTP; gate schema freshness in CI"
```

---

## Milestone 2 — One validator, two channels

### Task 5: Extract the threat lints into a reusable function

**Files:**
- Modify: `keel/catalog.py:102-112` (move the lint block into a function; call it from `validate_catalog`)
- Test: `tests/test_lints.py`

**Step 1: Write the failing test**

```python
# tests/test_lints.py
from keel.schemas.threat import Threat
from keel.catalog import lint_threat


def _threat(**over):
    base = dict(
        id="T-X", title="Sensitive data disclosure", harm="data-exposed",
        weaknesses=[{"component": "tool", "text": "returns raw records with no scoping"}],
        reachability="NOT applicable if the model sees no secrets",
        mitigations=[{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood"}],
    )
    base.update(over)
    return Threat(**base)


def test_lint_flags_all_soft():
    msgs = lint_threat(_threat())
    assert any("no `gating` mitigation" in m for m in msgs)


def test_lint_flags_technique_title():
    msgs = lint_threat(_threat(title="Prompt injection"))
    assert any("technique" in m for m in msgs)


def test_lint_clean_threat_has_no_advice():
    t = _threat(mitigations=[{"id": "CTRL-DLP", "strength": "gating", "rationale": "blocks"}])
    assert lint_threat(t) == []
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_lints.py -q`
Expected: FAIL (`ImportError: cannot import name 'lint_threat'`).

**Step 3: Write minimal implementation**

Add to `keel/catalog.py`:

```python
def lint_threat(threat: Threat) -> list[str]:
    """Non-blocking advice for one threat (no gating control; a technique used as identity).
    These are the 'amber' nudges the authoring UI shows; they never block a save."""
    out: list[str] = []
    if threat.mitigations and not any(m.strength == "gating" for m in threat.mitigations):
        out.append("no `gating` mitigation (all soft) — no architectural closure")
    for tw in _TECHNIQUE_WORDS:
        if tw in threat.title.lower():
            out.append(f"technique {tw!r} used as the threat title — belongs in source/references")
        elif any(tw in w.text.lower() and len(w.text) < 40 for w in threat.weaknesses):
            out.append(f"technique {tw!r} used as a weakness identity — belongs in source/references")
    return out
```

Then replace the inline Lint A / Lint B block in `validate_catalog` with:

```python
        for msg in lint_threat(threat):
            errors.append(f"{rel}: {msg}")
```

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_lints.py tests/test_catalog.py -q`
Expected: PASS (existing catalog tests still green — same messages, now routed through `lint_threat`).

**Step 5: Commit**

```bash
git add keel/catalog.py tests/test_lints.py
git commit -m "refactor: extract lint_threat for reuse by the validate endpoint"
```

---

### Task 6: `POST /threats/validate` — structure errors and advice in one response

**Files:**
- Modify: `keel/routes/library.py`
- Test: `tests/test_validate_route.py`

**Step 1: Write the failing test**

```python
# tests/test_validate_route.py
from fastapi.testclient import TestClient

from keel.main import app

client = TestClient(app)

GOOD = {
    "id": "T-TMP", "title": "Sensitive data disclosure", "harm": "data-exposed",
    "weaknesses": [{"component": "tool", "text": "returns raw records with no scoping"}],
    "reachability": "NOT applicable if the model sees no secrets",
    "mitigations": [{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood"}],
}


def test_validate_returns_advice_not_error_for_all_soft():
    r = client.post("/threats/validate", json=GOOD)
    body = r.json()
    assert body["ok"] is True                 # structurally valid
    assert any("gating" in a["msg"] for a in body["advice"])


def test_validate_returns_structure_error_for_bad_harm():
    bad = {**GOOD, "harm": "oops"}
    body = client.post("/threats/validate", json=bad).json()
    assert body["ok"] is False
    assert any(e["field"] == "harm" for e in body["errors"])
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_validate_route.py -q`
Expected: FAIL (404 — route missing).

**Step 3: Write minimal implementation** (append to `keel/routes/library.py`)

```python
from pydantic import ValidationError

from keel.catalog import lint_threat
from keel.schemas.threat import Threat


@router.post("/threats/validate")
async def validate_threat(payload: dict = Body(...)):
    """One validator, two channels: Pydantic gives blocking structure errors; lint_threat
    gives non-blocking advice. The browser renders these into its red and amber channels."""
    try:
        threat = Threat(**payload)
    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        return {"ok": False, "errors": errors, "advice": []}
    advice = [{"field": "", "msg": m} for m in lint_threat(threat)]
    return {"ok": True, "errors": [], "advice": advice}
```

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_validate_route.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/routes/library.py tests/test_validate_route.py
git commit -m "feat: POST /threats/validate returns structure errors and advice"
```

---

### Task 7: Expose style-guide coverage for the editor's badges

**Files:**
- Modify: `keel/routes/library.py` (add a coverage route; `style_guide_service.get_coverage` already exists)
- Test: `tests/test_coverage_route.py`

**Step 1: Write the failing test**

```python
# tests/test_coverage_route.py
from fastapi.testclient import TestClient

from keel.main import app


def test_coverage_route_shape():
    r = TestClient(app).get("/style-guide/coverage")
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["overall"] <= 100
    assert any(e["entity_type"] == "threat" for e in body["entities"])
```

**Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_coverage_route.py -q`
Expected: FAIL (404).

**Step 3: Write minimal implementation** (append to `keel/routes/library.py`)

```python
@router.get("/style-guide/coverage")
async def style_guide_coverage():
    return (await style_guide_service.get_coverage()).model_dump()
```

Note: register this route **above** the existing `/style-guide/{entity_type}/{field_name}` patch route is unnecessary (different method + path), but confirm `/style-guide/coverage` is not shadowed by any `GET /style-guide/{...}` — there is none, so order does not matter.

**Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_coverage_route.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add keel/routes/library.py tests/test_coverage_route.py
git commit -m "feat: expose style-guide coverage for the editor badges"
```

---

## Milestone 3 — Screen 1: browse and edit a threat (front end)

> No JS test harness. Each task ends with a Verify block. Start the app with
> `.venv/Scripts/python -m uvicorn keel.main:app --port 8000` and open http://localhost:8000.
> The current `keel/static/index.html` still targets the OLD threat fields and is a full
> rebuild, not a patch. **Rewrite it from scratch** to the new design: keep the color
> variables, the `api()`/`toast()` helpers, and the list-editor helpers that still apply;
> drop everything tied to the old threat fields (description/impact_class/vulnerability).
> The tasks below build the new file section by section — treat Task 8 as starting a fresh
> file and each later task as adding to it.

### Task 8: Three-pane layout shell and schema/style-guide bootstrap

**Files:**
- Rewrite: `keel/static/index.html` (fresh file; port over only the color variables and the `api()`/`toast()`/list-editor helpers)

**Do:**
- Set the body grid to three columns: library rail, editor, preview (e.g. `grid-template-columns: 320px 1fr 360px`). Keep the existing color variables.
- On boot, in `load()`, also fetch `/schema/threat`, `/schema/weakness`, `/schema/mitigation_link`, and `/style-guide`; store them on `state.schema` and `state.style`.
- Add a right-hand `<section id="preview">` pane, empty for now.

**Verify:**
- Reload the page. You see three columns; the left list still populates with threats; no console errors; `state.schema.threat` is defined (check via devtools console `window.state?.schema` if state is exposed, else add a temporary `console.log`).

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): three-pane shell; fetch schema + style guide on boot"
```

---

### Task 9: Render the threat form from the schema (fields, order, dropdowns)

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Replace `editThreat()` so it builds fields by walking the new schema order: title, harm, surface, source, weaknesses, reachability, mitigations, references, tags.
- For a field whose schema node has an `enum` (harm), render a `<select>` from that enum. For an array-of-enum (surface, source), render a checkbox set from the enum. Read the enums from `state.schema.threat` (resolve `$defs`/`$ref` where Pydantic nests them — for surface/source the enum sits under the array `items`).
- Free-text (title, reachability) → text/textarea. Tags → comma-separated input (keep existing behavior).
- Do NOT build weaknesses/mitigations yet (next tasks) — render placeholders.
- Update `renderThreat()` (read view) to show the new fields instead of description/impact_class/vulnerability.

**Verify:**
- Select a threat, click Edit. Harm is a dropdown pre-selected to the threat's value; surface and source are checkbox sets with the right boxes ticked; title and reachability are editable. The read view shows harm/surface/source/reachability, no leftover "description/vulnerability" sections.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): schema-driven threat form with vocabulary dropdowns"
```

---

### Task 10: Weaknesses as repeatable cards (CloudScape attribute-editor pattern)

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Render each weakness as a card: `component` dropdown (from `state.schema.weakness` enum), `text` textarea, `nature` dropdown (targeted/secondary), and a remove ✕ in the corner.
- An `+ Add weakness` button below the group appends a blank weakness `{component: <first enum>, text: "", nature: "targeted"}` to the draft.
- Wire edits into `state.draft.weaknesses`.

**Verify:**
- In edit mode, each existing weakness shows as a card with the component pre-selected. Add a weakness → a blank card appears. Remove one → it disappears. The draft reflects changes (Save comes in Task 13).

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): weaknesses as repeatable cards"
```

---

### Task 11: Mitigation links as cards (strength + rationale), reusing link/unlink

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Render each linked mitigation as a card: mitigation id + name (from `state.mitById`), a `strength` dropdown (gating/soft from `state.schema.mitigation_link` enum), a `rationale` textarea, and an Unlink button.
- Keep the existing "Link a mitigation" picker; when linking, send `strength` (default `gating`) and empty `rationale` to the existing `PUT /threats/{id}/mitigations/{mid}` (already accepts `strength` + `rationale`).
- Strength and rationale save via the same PUT on blur/change.

**Verify:**
- Linked mitigations show with a strength dropdown and rationale. Change strength → persists (reload confirms). Link and unlink still work.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): mitigation-link cards with strength + rationale"
```

---

### Task 12: Inline style-guide bar (one-line hint always; full bar on focus)

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- For each field, render the one-line hint from `state.style.entities.<entity>.fields.<field>.purpose` above the input.
- On focus of a field, expand a guidance panel beside/under it showing that field's `content_requirements` (Include), `avoid` (Avoid), and first `examples` entry with a **use example** button that writes the example into the field. Collapse on blur.
- Map form fields to style-guide entities: threat-level fields → `threat`; weakness card fields → `weakness`; mitigation-link fields → `mitigation_link`.

**Verify:**
- Focus the title field → its guidance panel appears with Include/Avoid/Example; click "use example" → the example text lands in the field; blur → the panel collapses. The one-line hint stays visible at all times.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): inline style-guide bar with focus-to-expand and use-example"
```

---

### Task 13: Two feedback channels via /threats/validate; save on blur

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Add a debounced (~300ms) `validateDraft()` that POSTs the assembled draft to `/threats/validate` on blur of any field (never per keystroke).
- Render `errors` (red) both as a summary strip at the top of the editor and inline next to the field named by `error.field` (match on the field path; weaknesses come back as `weaknesses.0.text` etc.). Render `advice` (amber) only inline / in the Insights strip — never in the summary, never blocking.
- Keep the row status badge idea: green when a field has no error/advice, amber if advice, red if error.
- Save (the existing PATCH) stays available regardless of advice; block Save only when `errors` is non-empty, and on a failed server PATCH map its Pydantic error back into the same red channel.

**Verify:**
- Set harm to a valid value but leave all mitigations soft → an amber "no gating mitigation" advice appears inline/Insights, and Save is still enabled. Temporarily clear the title → a red error appears in the summary and at the field, and Save is disabled. Fix it → red clears.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): structure-error and advice channels; validate on blur"
```

---

### Task 14: Live preview pane + Insights strip

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- In `#preview`, render the assembled threat as a person reads it: title, one-line harm, surface/source, weaknesses as sentences, mitigations grouped gating vs soft (counts), and the reachability carve-out. Update on the same debounced change as validation.
- Below it, an Insights strip listing the current `advice` items (no references yet; no gating mitigation) — soft, never blocking.

**Verify:**
- Edit a field → the preview updates within ~300ms. The Insights strip mirrors the advice from Task 13. Removing all references shows a "no references yet" insight.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): live preview pane and insights strip"
```

---

### Task 15: Raw-YAML toggle

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Add a `[Structure | YAML]` toggle in the editor header. YAML view shows the current threat as YAML text in a `<textarea>`. Generate YAML client-side from the draft with a tiny serializer (the fields are simple scalars/lists — a minimal emitter is fine; do not add a YAML library).
- On switching back to Structure, parse is not required: the source of truth stays the structured draft; YAML view is read-and-edit-as-text that, on Save from YAML view, is sent to a new lightweight path — to keep scope small, in this task make YAML view **read-only** (a faithful preview of exactly what will be written), with Save disabled in YAML view. (Editable raw-YAML round-trip is deferred; note this in the Insights/README.)

**Verify:**
- Toggle to YAML → you see the threat rendered as YAML matching the on-disk file order (id, title, harm, surface, source, weaknesses, reachability, mitigations, references, tags). Toggle back → the form is intact.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): read-only raw-YAML view of the current threat"
```

---

### Task 16: Save → pull-request handoff

**Files:**
- Modify: `keel/static/index.html`
- Modify: `keel/config.py` (add an optional `repo_url` setting for the Edit-on-GitHub link)

**Do:**
- After a successful Save, show a toast/dialog: "Saved to catalog/threats/<id>.yaml — commit and open a pull request." If `repo_url` is set, include an "Edit on GitHub" link to `<repo_url>/edit/main/catalog/threats/<id>.yaml`.
- Expose `repo_url` from the server (e.g. a `GET /config` returning `{repo_url}`) or inline it into the page; keep it optional (link hidden when unset).

**Verify:**
- Save a threat → the confirmation appears and names the exact file. With `KEEL_REPO_URL` set in `.env`, the GitHub link points at that file's edit page.

**Commit:**
```bash
git add keel/static/index.html keel/config.py
git commit -m "feat(ui): save-to-pull-request handoff with optional Edit on GitHub"
```

---

## Milestone 4 — Screen 2: the style-guide editor (front end)

### Task 17: Field tree from the schema with coverage badges

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Replace the current flat Style Guide tab with the three-pane editor. Left rail: entity → field tree built from `state.schema` (threat/weakness/mitigation_link/mitigation), each field showing its coverage badge from `/style-guide/coverage`. Mark orphan fields (present in `/style-guide` but not in the schema) distinctly.
- Selecting a field opens its bar editor in the center (Task 18).

**Verify:**
- Open the Style Guide screen → the left shows entities and their fields, each with a coverage percent; a field with no guidance reads 0%; no field is missing that the schema has.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): style-guide field tree from schema with coverage badges"
```

---

### Task 18: Bar editor + live "what an author sees" preview

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Center pane: edit the selected field's slots — purpose, content_requirements (Include), avoid, examples, instructions — reusing the existing list editors. Save via the existing `PATCH /style-guide/{entity}/{field}`.
- Right pane: render the exact author-facing guidance panel from Task 12 using the in-progress draft, so the maintainer sees precisely what an author will see. Show the field's slot count (e.g. 4/5).

**Verify:**
- Edit a field's Avoid list → the right-hand author preview updates live to match. Save → reload shows the change persisted and the coverage badge updates.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): style-guide bar editor with live author preview"
```

---

### Task 19: Style-guide save → pull-request handoff

**Files:**
- Modify: `keel/static/index.html`

**Do:**
- Mirror Task 16 for style-guide saves: after a successful field save, confirm the exact file (`catalog/style_guide/<entity>.yaml`) and offer the Edit-on-GitHub link when `repo_url` is set.

**Verify:**
- Save a style-guide field → the confirmation names `catalog/style_guide/<entity>.yaml`; the GitHub link (if configured) points at it.

**Commit:**
```bash
git add keel/static/index.html
git commit -m "feat(ui): style-guide save-to-pull-request handoff"
```

---

## Milestone 5 — Close-out

### Task 20: Full green + docs

**Files:**
- Modify: `README.md` (document the two screens, `keel schema`, the save→PR flow, and the deferred editable-YAML round-trip)
- Modify: `docs/plans/2026-08-17-keel-authoring-ui.md` (tick off tasks)

**Do:**
- Run the whole suite and linters: `.venv/Scripts/python -m pytest -q` and `ruff check keel tests` and `.venv/Scripts/python -m keel validate` and `.venv/Scripts/python -m keel schema --check` — all green.
- Manually walk both screens end to end once more.
- Update the README.

**Commit:**
```bash
git add README.md docs/plans/2026-08-17-keel-authoring-ui.md
git commit -m "docs: document the authoring UI and schema workflow"
```

---

## Deferred (not in this plan)

- Editable raw-YAML round-trip (parse YAML back into the draft) — Task 15 ships read-only YAML first.
- Creating a brand-new threat from the UI (this plan edits existing threats; New-threat can reuse the same form with an empty draft and a chosen id, as a fast follow).
- `test-model` regression skill and the assess-skill rewrite to the new model (separate track).
- Client-side JSON Schema validation library — deliberately omitted; the server `/threats/validate` is the single validator.
