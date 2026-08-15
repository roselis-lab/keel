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

    missing_vulnerability = sorted(t["id"] for t in threats if not t.get("vulnerability"))
    missing_impact_class = sorted(t["id"] for t in threats if not (t.get("impact_class") or "").strip())
    without_mitigation = sorted(t["id"] for t in threats if not (t.get("mitigations")))
    dangling_links = sorted(
        f'{t["id"]}::{link["mitigation_id"]}'
        for t in threats
        for link in (t.get("mitigations") or [])
        if link["mitigation_id"] not in mitigation_ids
    )

    coverage = await get_coverage()
    issues = {
        "threats_missing_vulnerability": missing_vulnerability,
        "threats_missing_impact_class": missing_impact_class,
        "threats_without_mitigation": without_mitigation,
        "dangling_mitigation_links": dangling_links,
    }
    return {
        "success": True,
        "stats": await get_stats(),
        "style_guide_coverage": coverage.overall,
        "issues": issues,
        "issue_count": sum(len(v) for v in issues.values()),
    }
