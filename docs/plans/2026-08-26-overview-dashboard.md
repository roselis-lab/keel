# Overview Dashboard Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add four sections to the Overview dashboard (catalog warnings, recent git activity, draft/verified split, implementation coverage) and reflow the page into a two-column grid, per `docs/plans/2026-08-26-overview-dashboard-design.md`.

**Architecture:** Three small backend additions (a structured version of the existing `catalog_warnings()`, a whole-catalog `recent_activity()` git function mirroring the existing per-file `history()`, and two new aggregate counts in `health_service`), each with its own route, feeding a reworked `overviewHtml()`/`loadOverview()` in the existing vanilla-JS frontend. No new dependencies, no build step, no charting library — two new CSS-only bar components reuse the existing design tokens.

**Tech Stack:** FastAPI + Pydantic (backend), vanilla JS + hand-rolled CSS (frontend), pytest (backend tests), manual Browser-pane verification (frontend — no JS test harness in this repo).

---

### Task 1: Structured catalog warnings

**Files:**
- Modify: `keel/catalog.py:145-204` (the `catalog_warnings` function)
- Test: `tests/test_catalog_warnings.py`

**Context:** `catalog_warnings()` returns a flat `list[str]`, built only for `keel validate`'s CLI output. The dashboard needs each warning to carry which entity it's about, so a chip can jump to that card. The fix: pull the detection loop into `catalog_warnings_structured()`, which returns `list[dict]`; `catalog_warnings()` becomes a one-line formatter over it, so its output (and every existing test asserting exact string content) does not change.

**Step 1: Write the failing tests**

Add to `tests/test_catalog_warnings.py`:

```python
def test_structured_warnings_carry_entity_refs():
    from keel.catalog import catalog_warnings_structured

    items = catalog_warnings_structured()
    over_graded = [w for w in items if w["category"] == "over_graded_strength"]
    assert over_graded, items
    hit = next(w for w in over_graded if w["entity_id"] == "T-CRED-THEFT")
    assert hit["entity_type"] == "threat"
    assert "CTRL-AUDIT-LOGGING" in hit["message"]

    missing_refs = [w for w in items if w["category"] == "missing_references"]
    assert len(missing_refs) == 13, missing_refs
    assert all(w["entity_type"] == "threat" and w["entity_id"] for w in missing_refs)

    unused_nature = [w for w in items if w["category"] == "unused_nature"]
    assert len(unused_nature) == 1, unused_nature
    assert unused_nature[0]["entity_type"] is None
    assert unused_nature[0]["entity_id"] is None


def test_catalog_warnings_strings_match_structured_messages():
    """catalog_warnings() must stay a pure projection of the structured data —
    same messages, same order, nothing lost in the format-string round trip."""
    from keel.catalog import catalog_warnings_structured

    assert catalog_warnings() == [w["message"] for w in catalog_warnings_structured()]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_catalog_warnings.py -v`
Expected: the two new tests FAIL with `ImportError` or `AttributeError` (`catalog_warnings_structured` does not exist yet); the pre-existing tests in this file still PASS.

**Step 3: Write the implementation**

Replace the body of `catalog_warnings` in `keel/catalog.py` (currently lines 145–204) with:

```python
def catalog_warnings_structured(catalog_dir: Path = DEFAULT_CATALOG_DIR) -> list[dict[str, str | None]]:
    """Advisory quality checks over the catalog (NOT errors) — structured form.

    Each item is `{"category", "entity_type", "entity_id", "message"}`. `entity_type`/
    `entity_id` are `None` for a library-wide finding with no single owning entity
    (e.g. the unused-`nature` check). See `catalog_warnings()` for the CLI-facing
    string form and the check descriptions.
    """
    warnings: list[dict[str, str | None]] = []
    if not catalog_dir.exists():
        return warnings

    mit_class: dict[str, str] = {}
    for path in sorted((catalog_dir / "mitigations").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(rec, dict) and rec.get("id"):
            mit_class[rec["id"]] = rec.get("mitigation_class")

    any_secondary = False
    for path in sorted((catalog_dir / "threats").glob("*.yaml")):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(rec, dict):
            continue
        tid = rec.get("id") or path.stem

        for link in rec.get("mitigations") or []:
            if not isinstance(link, dict) or link.get("strength") != "gating":
                continue
            mid = link.get("id")
            cls = mit_class.get(mid)
            if cls is not None and cls != "gating_control":
                warnings.append({
                    "category": "over_graded_strength",
                    "entity_type": "threat",
                    "entity_id": tid,
                    "message": (
                        f"{tid} -> {mid}: strength 'gating' but mitigation_class is '{cls}' "
                        "— a non-gating control should not back a gating link"
                    ),
                })

        if not (rec.get("references") or []):
            warnings.append({
                "category": "missing_references",
                "entity_type": "threat",
                "entity_id": tid,
                "message": f"{tid}: no references (provenance) — map to CWE/CAPEC/OWASP-LLM/ATLAS",
            })

        for w in rec.get("weaknesses") or []:
            if isinstance(w, dict) and w.get("nature") == "secondary":
                any_secondary = True

    if not any_secondary:
        warnings.append({
            "category": "unused_nature",
            "entity_type": None,
            "entity_id": None,
            "message": (
                "no weakness is marked 'secondary' — the nature field may be unused "
                "(every weakness is 'targeted')"
            ),
        })

    return warnings


def catalog_warnings(catalog_dir: Path = DEFAULT_CATALOG_DIR) -> list[str]:
    """Advisory quality checks over the catalog (NOT errors). These surface soft problems —
    over-graded links, missing provenance, an unused vocabulary — without failing CI. Runs
    read-only over the raw YAML (same load path as `validate_catalog`). Returns human-readable
    warnings; an empty list means nothing to nudge on.

    Checks:
      1. Over-graded link strength: a `gating` link whose target control is not a
         `gating_control` (a detector/process/advisory control does not architecturally block).
      2. Missing references: a threat with no `references` (provenance) to map to prior art.
      3. Unused `nature`: no weakness anywhere is marked `secondary` (the field may be dead).
    """
    return [w["message"] for w in catalog_warnings_structured(catalog_dir)]
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_catalog_warnings.py tests/test_catalog.py -v`
Expected: all PASS, including the pre-existing exact-string assertions.

**Step 5: Commit**

```bash
git add keel/catalog.py tests/test_catalog_warnings.py
git commit -m "refactor(catalog): structured catalog_warnings for dashboard chips"
```

---

### Task 2: Recent-activity git function + route

**Files:**
- Modify: `keel/githistory.py`
- Modify: `keel/routes/library.py:191-216` (Git history section)
- Test: `tests/test_history.py`

**Context:** `history(entity, id)` only answers "what changed on this one file." The dashboard needs a cross-catalog activity feed. This follows the exact same safety model: `_run()` (argument-list subprocess, never a shell), graceful `{"available": False}` degradation, no new imports needed (`re` and `Path` are already imported in this file).

**Step 1: Write the failing tests**

Add to `tests/test_history.py` (inside the existing `pytestmark`-skipped block, so it only runs where the repo fixture applies):

```python
def test_recent_activity_lists_commits_with_entities():
    set_store(None)
    result = githistory.recent_activity(limit=5)
    assert result["available"] is True
    assert 1 <= len(result["commits"]) <= 5
    for c in result["commits"]:
        assert c["sha"] and c["author"] and c["date"] and c["message"]
        assert c["entities"], c  # every returned commit touched at least one tracked entity
        for e in c["entities"]:
            assert e["entity_type"] in ("threats", "mitigations")
            assert e["entity_id"]


def test_recent_activity_respects_limit():
    set_store(None)
    result = githistory.recent_activity(limit=1)
    assert len(result["commits"]) == 1


def test_route_recent_activity_ok():
    set_store(None)
    client = TestClient(app)
    r = client.get("/history/recent?limit=3")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert len(body["commits"]) <= 3
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_history.py -v`
Expected: the three new tests FAIL (`AttributeError: module 'keel.githistory' has no attribute 'recent_activity'`, then a 404 for the route test). Pre-existing tests still PASS (or all SKIP if this machine has no git — that's an existing, accepted condition for this file).

**Step 3: Write the implementation**

Add to `keel/githistory.py`, after `history()` and before `diff()`:

```python
_ENTITY_PATH_RE = re.compile(r"^(?:.*/)?(threats|mitigations)/([A-Za-z0-9._-]+)\.yaml$")


def recent_activity(limit: int = 20) -> dict:
    """Recent commits across the whole catalog (both threats/ and mitigations/), newest
    first. Each commit is `{"sha", "author", "date", "message", "entities": [...]}`, where
    `entities` is `[{"entity_type", "entity_id"}, ...]` for every tracked file the commit
    touched (a commit that touched only non-catalog files is skipped and does not count
    against `limit`).

    Unavailable (git missing, catalog not inside a git repo) → `{"available": False,
    "commits": []}`. `limit` bounds commits RETURNED, not commits scanned — a quiet
    catalog section deep in history beyond the internal scan buffer may return fewer
    than `limit` even if more exist; this is a soft recency feed, not a full log.
    """
    catalog_dir = get_store().dir
    proc = _run(["git", "-C", str(catalog_dir), "rev-parse", "--show-toplevel"])
    if proc is None:
        return {"available": False, "commits": []}
    repo_root = proc.stdout.strip()
    if not repo_root:
        return {"available": False, "commits": []}

    try:
        catalog_relpath = Path(catalog_dir).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return {"available": False, "commits": []}

    limit = max(limit, 1)
    proc = _run([
        "git", "-C", repo_root, "log",
        f"--format=__COMMIT__{_FORMAT}", "--name-status",
        "-n", str(limit * 5),  # buffer: not every commit touches threats/mitigations
        "--", f"{catalog_relpath}/threats", f"{catalog_relpath}/mitigations",
    ])
    if proc is None:
        return {"available": False, "commits": []}

    commits: list[dict] = []
    current: dict | None = None

    def _flush():
        if current and current["entities"] and len(commits) < limit:
            commits.append(current)

    for line in proc.stdout.splitlines():
        if line.startswith("__COMMIT__"):
            _flush()
            if len(commits) >= limit:
                current = None
                break
            meta = _parse_meta(line[len("__COMMIT__"):])
            current = {**meta, "entities": []}
            continue
        if not line.strip() or current is None:
            continue
        path = line.split("\t")[-1]  # "--name-status": "<status>\t<path>" (renames: 2 paths, last wins)
        m = _ENTITY_PATH_RE.match(path)
        if m:
            current["entities"].append({"entity_type": m.group(1), "entity_id": m.group(2)})
    _flush()

    return {"available": True, "commits": commits}
```

Add the route in `keel/routes/library.py`, in the "Git history" section (near line 192), before `entry_history`:

```python
@router.get("/history/recent")
async def recent_history(limit: int = Query(default=20, ge=1, le=100)):
    """Recent commits across the whole catalog. Always 200; `available: False` when
    git is unavailable or the catalog isn't inside a git repo."""
    return githistory.recent_activity(limit=limit)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_history.py -v`
Expected: all PASS (or all SKIP together, same as before, on a machine without git/repo).

**Step 5: Commit**

```bash
git add keel/githistory.py keel/routes/library.py tests/test_history.py
git commit -m "feat(history): whole-catalog recent-activity feed + /history/recent route"
```

---

### Task 3: Draft/verified and implementation-coverage counts

**Files:**
- Modify: `keel/services/health_service.py`
- Test: `tests/test_health.py`

**Context:** Pure aggregation over `store.mitigations`, already loaded in memory — no new I/O, no new route (folds into the existing `/health/library` response).

**Step 1: Write the failing test**

Add to `tests/test_health.py`:

```python
@pytest.mark.asyncio
async def test_health_reports_mitigation_status_and_coverage_counts(store):
    store.mitigations["CTRL-A"] = {
        "id": "CTRL-A", "name": "A", "mitigation_class": "gating_control", "status": "draft",
        "implementations": [],
    }
    store.mitigations["CTRL-B"] = {
        "id": "CTRL-B", "name": "B", "mitigation_class": "gating_control", "status": "verified",
        "implementations": [{"title": "t", "description": "d", "coverage": "local"}],
    }
    store.mitigations["CTRL-C"] = {
        "id": "CTRL-C", "name": "C", "mitigation_class": "gating_control", "status": "draft",
        "implementations": [
            {"title": "t1", "description": "d1", "coverage": "local"},
            {"title": "t2", "description": "d2", "coverage": "shared", "covers": "everything"},
        ],
    }
    result = await check_library_health()
    assert result["mitigation_status_counts"] == {"draft": 2, "verified": 1, "unset": 0}
    assert result["implementation_coverage_counts"] == {"shared": 1, "local_only": 1, "none": 1}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_health.py -v`
Expected: FAIL with `KeyError: 'mitigation_status_counts'`.

**Step 3: Write the implementation**

In `keel/services/health_service.py`, inside `check_library_health()`, after the existing `issues = {...}` block and before the `coverage = await get_coverage()` line, add:

```python
    mitigations = list(store.mitigations.values())
    status_counts = {"draft": 0, "verified": 0, "unset": 0}
    for m in mitigations:
        status_counts[m.get("status") if m.get("status") in ("draft", "verified") else "unset"] += 1

    impl_counts = {"shared": 0, "local_only": 0, "none": 0}
    for m in mitigations:
        impls = m.get("implementations") or []
        if not impls:
            impl_counts["none"] += 1
        elif any(i.get("coverage") == "shared" for i in impls):
            impl_counts["shared"] += 1
        else:
            impl_counts["local_only"] += 1
```

And add the two keys to the function's final `return` dict:

```python
    return {
        "success": True,
        "stats": await get_stats(),
        "style_guide_coverage": coverage.overall,
        "issues": issues,
        "issue_count": sum(len(v) for v in issues.values()),
        "mitigation_status_counts": status_counts,
        "implementation_coverage_counts": impl_counts,
    }
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_health.py -v`
Expected: PASS.

**Step 5: Run the full backend suite before touching the frontend**

Run: `python -m pytest -q`
Expected: all PASS (this closes out every backend change in the plan).

**Step 6: Commit**

```bash
git add keel/services/health_service.py tests/test_health.py
git commit -m "feat(health): mitigation status + implementation coverage counts"
```

---

### Task 4: Frontend — CSS for the new sections

**Files:**
- Modify: `keel/static/index.html` (CSS block, near the existing `/* ------ overview screen ------ */` rules around line 380–404)

**Step 1: Add the bar component and grid CSS**

Insert after the existing `.ov-clean` rules (after line 404):

```css
  .ov-grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
  @media (max-width: 900px) { .ov-grid2 { grid-template-columns: 1fr; } }
  .ov-bar { display: flex; height: 10px; border-radius: 6px; overflow: hidden; background: var(--navy-100); margin: 8px 0 6px; }
  .ov-bar-seg { height: 100%; }
  .ov-bar-seg.verified, .ov-bar-seg.shared { background: var(--green); }
  .ov-bar-seg.draft, .ov-bar-seg.local { background: var(--amber); }
  .ov-bar-seg.unset, .ov-bar-seg.none { background: var(--navy-300); }
  .ov-bar-legend { display: flex; gap: 14px; font-size: 12px; color: var(--navy-500); flex-wrap: wrap; }
  .ov-bar-legend .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
  .ov-activity-row { display: flex; align-items: baseline; gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--border2); font-size: 13px; flex-wrap: wrap; }
  .ov-activity-row:last-child { border-bottom: none; }
  .ov-activity-msg { color: var(--navy-800); }
  .ov-activity-meta { color: var(--navy-500); font-size: 12px; }
```

Check that `--navy-300` and `--navy-100` are already defined as CSS variables (they are used elsewhere, e.g. `.badge.soft` uses `--navy-100`); if `--navy-300` is not defined in the `:root`/theme block, add it there matching the existing navy scale step, or substitute the closest existing token (check the `:root` variable block near the top of the `<style>` section before assuming — do not invent a new token casually).

**Step 2: No test for this step (pure CSS) — visually verified in Task 7**

**Step 3: Commit**

```bash
git add keel/static/index.html
git commit -m "style(overview): CSS for two-column grid and coverage bars"
```

---

### Task 5: Frontend — data loading (allSettled across five sources)

**Files:**
- Modify: `keel/static/index.html`, `loadOverview()` (around line 1885–1895)

**Step 1: Replace `loadOverview()`**

```javascript
async function loadOverview() {
  const [h, cov, warn, act] = await Promise.allSettled([
    j("/health/library"), j("/style-guide/coverage"), j("/health/warnings"), j("/history/recent?limit=15"),
  ]);
  state.health = h.status === "fulfilled" ? h.value : (state.health || { stats: {}, issues: {}, issue_count: 0 });
  state.coverage = cov.status === "fulfilled" ? cov.value : state.coverage;
  state.warnings = warn.status === "fulfilled" ? warn.value.warnings : [];
  state.recentActivity = act.status === "fulfilled" ? act.value : { available: false, commits: [] };
  if (h.status === "rejected") toast(h.reason && h.reason.message || "Failed to load health", true);
  if (state.screen === "overview") { renderOverviewMain(); renderOverviewRight(); }
}
```

This needs a new backend route, `/health/warnings`, that Task 1's `catalog_warnings_structured()` does not yet expose over HTTP.

**Step 2: Add the missing route**

In `keel/routes/library.py`, in the "Health / overview" section (near line 150), add after `health_library()`:

```python
@router.get("/health/warnings")
async def health_warnings():
    """Structured advisory warnings (over-graded links, missing references, unused
    vocabulary) — the same checks `keel validate` runs, in dashboard-friendly form."""
    return await health_service.get_catalog_warnings()
```

And in `keel/services/health_service.py`, add:

```python
async def get_catalog_warnings() -> dict[str, Any]:
    """Structured advisory warnings for the dashboard (see `keel.catalog.catalog_warnings_structured`)."""
    from keel.catalog import catalog_warnings_structured

    return {"warnings": catalog_warnings_structured(get_store().dir)}
```

This needs `get_store` imported in `health_service.py` — it already is (`from keel.store import get_store`, used inside `get_stats`/`check_library_health` via the module-level `store = get_store()` pattern — check the top of the file and reuse the existing import rather than adding a second one).

**Step 3: Backend test for the new route**

Add to `tests/test_health.py`:

```python
def test_route_health_warnings_ok():
    from fastapi.testclient import TestClient
    from keel.main import app

    client = TestClient(app)
    r = client.get("/health/warnings")
    assert r.status_code == 200
    assert isinstance(r.json()["warnings"], list)
```

Run: `python -m pytest tests/test_health.py -v` — expect PASS.

**Step 4: Add `state.warnings` / `state.recentActivity` to the initial state object**

Find the `state` object initialization (near line 449, alongside `mitFacets`) and add two keys: `warnings: [], recentActivity: { available: false, commits: [] },`.

**Step 5: Commit**

```bash
git add keel/static/index.html keel/routes/library.py keel/services/health_service.py tests/test_health.py
git commit -m "feat(overview): wire warnings + recent-activity data with Promise.allSettled"
```

---

### Task 6: Frontend — layout (two-column grid + two new sections)

**Files:**
- Modify: `keel/static/index.html`, `overviewHtml()` (currently lines 1925–1979) and `OV_GAP_GROUPS` area (1916–1923)

**Step 1: Add a warning-category label table next to `OV_GAP_GROUPS`**

```javascript
const OV_WARNING_LABELS = {
  over_graded_strength: "Over-graded links",
  missing_references: "Missing references",
  unused_nature: "Unused vocabulary",
};
```

**Step 2: Rewrite `overviewHtml()`**

Replace the function body (keep the existing `stat`, `counts`, `overall`/`covRows`/`coverage`, `chip`, `gapCards`, `gaps` local variables — they are unchanged) and add, before the final `return`:

```javascript
  const bar = (segments, legendItems) => {
    const total = segments.reduce((s, x) => s + x.n, 0) || 1;
    const segHtml = segments.map(s => `<div class="ov-bar-seg ${s.cls}" style="width:${(100 * s.n / total).toFixed(1)}%"></div>`).join("");
    const legend = legendItems.map(l => `<span><span class="dot" style="background:var(${l.color})"></span>${esc(l.label)}: ${l.n}</span>`).join("");
    return `<div class="ov-bar">${segHtml}</div><div class="ov-bar-legend">${legend}</div>`;
  };

  const sc = (h.mitigation_status_counts) || { draft: 0, verified: 0, unset: 0 };
  const draftVerified = `<div class="card">
    ${bar(
      [{ n: sc.verified, cls: "verified" }, { n: sc.draft, cls: "draft" }, { n: sc.unset, cls: "unset" }],
      [{ label: "verified", n: sc.verified, color: "--green" }, { label: "draft", n: sc.draft, color: "--amber" }, { label: "unset", n: sc.unset, color: "--navy-300" }]
    )}
  </div>`;

  const ic = (h.implementation_coverage_counts) || { shared: 0, local_only: 0, none: 0 };
  const implCoverage = `<div class="card">
    ${bar(
      [{ n: ic.shared, cls: "shared" }, { n: ic.local_only, cls: "local" }, { n: ic.none, cls: "none" }],
      [{ label: "shared", n: ic.shared, color: "--green" }, { label: "local only", n: ic.local_only, color: "--amber" }, { label: "none", n: ic.none, color: "--navy-300" }]
    )}
  </div>`;

  const warnChip = w => w.entity_id
    ? `<span class="ov-chip" data-warn-entity="${esc(w.entity_type)}" data-warn-id="${esc(w.entity_id)}" title="Open ${esc(w.entity_id)}">${esc(w.entity_id)}</span>`
    : "";
  const warningsByCat = {};
  for (const w of (state.warnings || [])) (warningsByCat[w.category] || (warningsByCat[w.category] = [])).push(w);
  const warningCards = Object.entries(OV_WARNING_LABELS).map(([cat, label]) => {
    const items = warningsByCat[cat] || [];
    if (!items.length) return "";
    return `<div class="card ov-gap-group">
      <div class="ov-gap-head"><span class="gname">${esc(label)}</span><span class="badge soft">${items.length}</span></div>
      <div class="ov-chips">${items.map(warnChip).join("")}</div>
    </div>`;
  }).join("");
  const warningsSection = (state.warnings || []).length
    ? warningCards
    : `<div class="ov-clean"><span class="ok-i">✓</span><p><b>Nothing flagged.</b> No advisory warnings across the catalog.</p></div>`;

  const act = state.recentActivity || { available: false, commits: [] };
  const activityRows = act.available && act.commits.length
    ? act.commits.map(c => `<div class="ov-activity-row">
        <span class="ov-activity-msg">${esc(c.message)}</span>
        <span class="ov-activity-meta">${esc(c.author)} · ${esc((c.date || "").slice(0, 10))}</span>
        ${(c.entities || []).map(e => `<span class="ov-chip" data-warn-entity="${esc(e.entity_type)}" data-warn-id="${esc(e.entity_id)}">${esc(e.entity_id)}</span>`).join("")}
      </div>`).join("")
    : `<p class="placeholder">${act.available ? "No recent changes." : "Git history unavailable."}</p>`;

  return `<div class="detail">
    <div class="dhead">
      <div class="dicon" style="background:var(--navy-700)">◈</div>
      <div class="dtitle">
        <h2>Library overview</h2>
        <div class="did">A snapshot to review — nothing here blocks a save.</div>
      </div>
    </div>
    <div class="ov-grid2">
      <div>
        <section><h3 class="slabel">Counts</h3>${counts}</section>
        <section><h3 class="slabel">Draft / verified</h3>${draftVerified}</section>
      </div>
      <div>
        <section><h3 class="slabel">Style-guide coverage</h3>${coverage}</section>
        <section><h3 class="slabel">Implementation coverage</h3>${implCoverage}</section>
      </div>
    </div>
    <section><h3 class="slabel">Gaps to review${h.issue_count ? ` <span class="sub">— ${h.issue_count} across the library</span>` : ""}</h3>${gaps}</section>
    <section><h3 class="slabel">Catalog warnings${(state.warnings||[]).length ? ` <span class="sub">— ${(state.warnings||[]).length} across the library</span>` : ""}</h3>${warningsSection}</section>
    <section><h3 class="slabel">Recent activity</h3>${activityRows}</section>
  </div>`;
```

Note this reuses the `.ov-chip`/`data-*` pattern from the existing gap chips but with different data attributes (`data-warn-entity`/`data-warn-id`) so Task 7's click wiring can tell warning/activity chips apart from gap chips (which only ever point at threats and use `data-threat`).

**Step 3: No automated test (this is presentation-only HTML string building) — verified in Task 8**

**Step 4: Commit**

```bash
git add keel/static/index.html
git commit -m "feat(overview): two-column layout + catalog-warnings and recent-activity sections"
```

---

### Task 7: Frontend — interactivity (chip click-through, filtered navigation)

**Files:**
- Modify: `keel/static/index.html`, `wireOverview()` (near line 1981), `overviewOpenThreat()` (near line 1986), `mitFacetValues()`/`mitFacetDefs()` (near lines 2260–2302)

**Step 1: Extend `wireOverview()` to wire the new chips and stat clicks**

```javascript
function wireOverview() {
  document.querySelectorAll(".ov-chip[data-threat]").forEach(c => c.onclick = () => overviewOpenThreat(c.dataset.threat));
  document.querySelectorAll(".ov-chip[data-warn-entity]").forEach(c => c.onclick = () => overviewOpenEntity(c.dataset.warnEntity, c.dataset.warnId));
  document.querySelectorAll("[data-ov-filter]").forEach(el => el.onclick = () => overviewOpenMitigationsFiltered(el.dataset.ovFilter, el.dataset.ovValue));
}

// Open either a threat or a mitigation from a warning/activity chip.
function overviewOpenEntity(entityType, id) {
  if (entityType === "mitigations" || entityType === "mitigation") { switchScreen("mitigations"); selectMit(id); return; }
  overviewOpenThreat(id);
}

// Jump to Mitigations with one facet value pre-selected (status, or implementations).
function overviewOpenMitigationsFiltered(facetKey, value) {
  state.mitFacets[facetKey].clear();
  state.mitFacets[facetKey].add(value);
  switchScreen("mitigations");
}
```

**Step 2: Make the Draft/verified and Implementation coverage numbers clickable**

In the `bar()` helper written in Task 6, legend spans need `data-ov-filter`/`data-ov-value` attributes. Update the legend-building line inside `bar()`:

```javascript
    const legend = legendItems.map(l => `<span ${l.filterKey ? `data-ov-filter="${esc(l.filterKey)}" data-ov-value="${esc(l.filterValue)}" style="cursor:pointer"` : ""}><span class="dot" style="background:var(${l.color})"></span>${esc(l.label)}: ${l.n}</span>`).join("");
```

And pass `filterKey`/`filterValue` from the two call sites in `overviewHtml()`:

```javascript
      [{ label: "verified", n: sc.verified, color: "--green", filterKey: "status", filterValue: "verified" },
       { label: "draft", n: sc.draft, color: "--amber", filterKey: "status", filterValue: "draft" },
       { label: "unset", n: sc.unset, color: "--navy-300" }]
```

For Implementation coverage, `mitFacetValues()`'s `"implementations"` case currently only distinguishes `has`/`none`. Extend it so a `shared` value is also possible, keeping `has`/`none` intact for the existing facet UI:

```javascript
    case "implementations": {
      const impls = m.implementations || [];
      if (!impls.length) return ["none"];
      return impls.some(i => i.coverage === "shared") ? ["has", "shared"] : ["has"];
    }
```

And add the `shared` option to `mitFacetDefs()`:

```javascript
    { key: "implementations", label: "Implementations", opts: [["has", "has"], ["shared", "shared"], ["none", "none"]] },
```

Then wire the Implementation-coverage legend spans with `filterKey: "implementations", filterValue: "shared"` (shared bucket) and `filterValue: "none"` (none bucket) — `local_only` has no direct one-facet-value equivalent (it is "has" AND NOT "shared"), so leave that legend entry non-clickable (no `filterKey`).

**Step 3: Manual verification (no automated frontend test in this repo) — see Task 8**

**Step 4: Commit**

```bash
git add keel/static/index.html
git commit -m "feat(overview): click-through on warnings/activity chips and coverage stats"
```

---

### Task 8: Manual browser verification

**No new files — this task verifies Tasks 4–7 together, per the design doc's testing section.**

**Step 1: Start the app**

Use the `keel-web` preview config already in `.claude/launch.json` (added earlier this session) via the Browser pane's `preview_start`, then `navigate` to `http://localhost:8420` and open the Overview screen.

**Step 2: Visual check**

`read_page` the Overview screen; confirm all seven sections render (Counts, Draft/verified, Style-guide coverage, Implementation coverage, Gaps to review, Catalog warnings, Recent activity) and the two-column grid holds at a normal desktop width. `resize_window` to a narrower width and confirm `.ov-grid2` collapses to one column (the `@media (max-width: 900px)` rule from Task 4).

**Step 3: Click-through checks**

- Click a Catalog-warnings chip → confirm it opens the right threat (or mitigation) on the correct screen.
- Click a Recent-activity entity chip → same check.
- Click the "verified" number in Draft/verified → confirm it lands on Mitigations with the Status facet showing only `verified` selected and the list filtered accordingly.
- Click the "shared" number in Implementation coverage → confirm the Mitigations Implementations facet shows `shared` selected.

**Step 4: Degradation check**

Use `read_network_requests` or `preview_logs` to confirm no unhandled JS errors when a source is empty (e.g. a catalog with zero warnings should show the "Nothing flagged" clean-state, not a blank section or a console error). If feasible, verify the `Promise.allSettled` behavior by temporarily breaking one endpoint (e.g. stop the server mid-request, or check `read_console_messages` for a rejected-promise log) and confirming the other sections still render.

**Step 5: Screenshot + summary**

Take a screenshot of the finished dashboard as proof, per this project's UI-verification convention (see `CLAUDE.md`/session guidance: verify in-browser before claiming a UI change complete, don't ask the user to check manually).

**Step 6: Final full-suite run and commit**

Run: `python -m pytest -q`
Expected: all PASS.

```bash
git add -A
git commit -m "docs: mark overview dashboard redesign complete" --allow-empty
```

(Use `--allow-empty` only if Task 8 produced no file changes beyond what earlier tasks already committed; otherwise commit whatever verification artifacts, if any, were intentionally added.)
