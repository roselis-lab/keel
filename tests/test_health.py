"""Health and stats checks for the library (app.services.health_service).

Ports the check-health smoke test from the predecessor repo: an in-memory SQLite
database, empty and populated, exercised through the same service functions the MCP
`get_stats` / `check_library_health` tools call.
"""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Mitigation, Threat, ThreatMitigation
from app.services.health_service import check_library_health, get_stats

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine():
    """Fresh in-memory schema per test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(async_engine):
    maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest.mark.asyncio
async def test_get_stats_empty(session):
    """An empty library reports zero across the board."""
    result = await get_stats(session)
    assert result["threats"] == 0
    assert result["mitigations"] == 0
    assert result["threat_mitigation_links"] == 0


@pytest.mark.asyncio
async def test_check_library_health_empty(session):
    """An empty library is healthy: every issue bucket is empty."""
    result = await check_library_health(session)
    assert result["success"] is True
    assert result["issue_count"] == 0
    assert result["stats"]["threats"] == 0
    assert all(bucket == [] for bucket in result["issues"].values())


@pytest.mark.asyncio
async def test_get_stats_counts_rows(session):
    """Counts track the rows actually present."""
    session.add(
        Threat(
            id="T-DEMO",
            title="Demo threat",
            impact_class="decision-integrity",
            vulnerability=["a recognizable exploitation pattern"],
            reachability="not applicable if the attacker cannot influence the input",
        )
    )
    session.add(Mitigation(id="M-DEMO", name="Demo control", mitigation_class="gating_control"))
    session.add(
        ThreatMitigation(
            id="T-DEMO::M-DEMO",
            threat_id="T-DEMO",
            mitigation_id="M-DEMO",
            rationale="blocks the path",
        )
    )
    await session.commit()

    assert await get_stats(session) == {
        "threats": 1,
        "mitigations": 1,
        "threat_mitigation_links": 1,
    }


@pytest.mark.asyncio
async def test_check_library_health_flags_gaps(session):
    """A threat with no facets and no mitigation surfaces in every relevant bucket."""
    session.add(Threat(id="T-BAD", title="Incomplete threat"))
    await session.commit()

    result = await check_library_health(session)
    issues = result["issues"]
    assert "T-BAD" in issues["threats_missing_vulnerability"]
    assert "T-BAD" in issues["threats_missing_impact_class"]
    assert "T-BAD" in issues["threats_without_mitigation"]
    assert result["issue_count"] >= 3
    assert result["success"] is True
