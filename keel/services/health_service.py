"""Library health and statistics."""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from keel.models import Threat, Mitigation, ThreatMitigation
from keel.services.style_guide_service import get_coverage


async def get_stats(session: AsyncSession) -> dict[str, Any]:
    """Return counts across the library."""
    threat_count = (await session.execute(select(func.count()).select_from(Threat))).scalar_one()
    mitigation_count = (await session.execute(select(func.count()).select_from(Mitigation))).scalar_one()
    link_count = (await session.execute(select(func.count()).select_from(ThreatMitigation))).scalar_one()
    return {
        "threats": threat_count,
        "mitigations": mitigation_count,
        "threat_mitigation_links": link_count,
    }


async def check_library_health(session: AsyncSession) -> dict[str, Any]:
    """Surface content and integrity gaps in the library."""
    threats = (await session.execute(select(Threat))).scalars().all()
    mitigation_ids = set(
        (await session.execute(select(Mitigation.id))).scalars().all()
    )
    links = (await session.execute(select(ThreatMitigation))).scalars().all()

    linked_threat_ids = {link.threat_id for link in links}

    missing_vulnerability = sorted(t.id for t in threats if not t.vulnerability)
    missing_impact_class = sorted(t.id for t in threats if not (t.impact_class or "").strip())
    without_mitigation = sorted(t.id for t in threats if t.id not in linked_threat_ids)
    dangling_links = sorted(
        link.id for link in links if link.mitigation_id not in mitigation_ids
    )

    coverage = await get_coverage(session)

    issues = {
        "threats_missing_vulnerability": missing_vulnerability,
        "threats_missing_impact_class": missing_impact_class,
        "threats_without_mitigation": without_mitigation,
        "dangling_mitigation_links": dangling_links,
    }
    return {
        "success": True,
        "stats": await get_stats(session),
        "style_guide_coverage": coverage.overall,
        "issues": issues,
        "issue_count": sum(len(v) for v in issues.values()),
    }
