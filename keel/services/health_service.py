"""Library health and statistics (backed by the file store)."""
from typing import Any

from keel.services.style_guide_service import get_coverage
from keel.store import get_store


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
    """Surface content and integrity gaps in the library."""
    store = get_store()
    threats = list(store.threats.values())
    mitigation_ids = set(store.mitigations)

    missing_weaknesses = sorted(t["id"] for t in threats if not t.get("weaknesses"))
    missing_harm = sorted(t["id"] for t in threats if not (t.get("harm") or "").strip())
    without_mitigation = sorted(t["id"] for t in threats if not (t.get("mitigations")))
    dangling_links = sorted(
        f'{t["id"]}::{link["id"]}'
        for t in threats
        for link in (t.get("mitigations") or [])
        if link.get("id") not in mitigation_ids
    )

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

    coverage = await get_coverage()
    issues = {
        "threats_missing_weaknesses": missing_weaknesses,
        "threats_missing_harm": missing_harm,
        "threats_without_mitigation": without_mitigation,
        "dangling_mitigation_links": dangling_links,
    }
    return {
        "success": True,
        "stats": await get_stats(),
        "style_guide_coverage": coverage.overall,
        "issues": issues,
        "issue_count": sum(len(v) for v in issues.values()),
        "mitigation_status_counts": status_counts,
        "implementation_coverage_counts": impl_counts,
    }


async def get_catalog_warnings() -> dict[str, Any]:
    """Structured advisory warnings for the dashboard (see `keel.catalog.catalog_warnings_structured`)."""
    from keel.catalog import catalog_warnings_structured

    return {"warnings": catalog_warnings_structured(get_store().dir)}
