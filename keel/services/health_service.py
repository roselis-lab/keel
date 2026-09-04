"""Library health and statistics (backed by the file store)."""
from typing import Any

from keel.services.style_guide_service import get_coverage
from keel.store import get_store


def _findings_for_the_served_catalog(store: Any) -> list[dict[str, Any]]:
    """The rules, run over what is loaded rather than over the files.

    `keel validate` reads the directory, because its question is whether the files may be
    trusted. The dashboard's question is different: what is wrong with the catalog people
    are looking at right now. Re-reading the disk here would let the two disagree the
    moment a write lands, which is exactly when someone is looking.
    """
    from keel.rules import Catalog, check_all
    from keel.services.coverage_service import load_sources

    cat = Catalog.from_store(store, coverage=load_sources(store.dir))
    return [f.as_dict() for f in check_all(cat)]


async def get_stats() -> dict[str, Any]:
    """Return counts across the library."""
    store = get_store()
    links = sum(len(t.get("mitigations") or []) for t in store.threats.values())
    return {
        "threats": len(store.threats),
        "mitigations": len(store.mitigations),
        "threat_mitigation_links": links,
    }


async def check_library_health() -> dict[str, Any]:
    """Everything the dashboard needs to say how the library is doing.

    Three tiers, deliberately separate. `errors` are hard defects found when the catalog
    was loaded — a record that failed its schema is not being served at all. `warnings`
    are advisory: real, but a half-authored draft may legitimately trip them.

    Everything except the load problems comes from the one rule registry, so the
    dashboard cannot know something the write that caused it did not.
    """
    store = get_store()
    mitigations = list(store.mitigations.values())
    impl_counts = {"shared": 0, "local_only": 0, "none": 0}
    for m in mitigations:
        impls = m.get("implementations") or []
        if not impls:
            impl_counts["none"] += 1
        elif any(i.get("coverage") == "shared" for i in impls):
            impl_counts["shared"] += 1
        else:
            impl_counts["local_only"] += 1

    coverage = await get_coverage()
    findings = _findings_for_the_served_catalog(store)
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "advice"]
    return {
        "success": True,
        "stats": await get_stats(),
        "style_guide_coverage": coverage.overall,
        # Two kinds of hard defect, kept apart because they are fixed differently.
        # `load_problems` are records that failed their schema and are not being served
        # at all - the file has to be repaired before anything else is true about it.
        # `errors` are records that loaded and are wrong against the rest of the catalog.
        "load_problems": store.problems,
        "errors": errors,
        "error_count": len(store.problems) + len(errors),
        # Advisory: real, but a half-authored draft may legitimately trip them.
        "warnings": warnings,
        "warning_count": len(warnings),
        "implementation_coverage_counts": impl_counts,
    }


async def get_catalog_warnings() -> dict[str, Any]:
    """The advisory half of the sweep, for the dashboard's own warnings block."""
    return {"warnings": [f for f in _findings_for_the_served_catalog(get_store())
                         if f["severity"] == "advice"]}
