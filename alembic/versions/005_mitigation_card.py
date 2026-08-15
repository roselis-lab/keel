"""Expand the mitigation into a full mitigation card.

Replaces the old (title, description, type, requirement_level, implementations) shape with the
mitigation-card schema (class as a switch, scope, control mechanism, failure behavior, telemetry,
anti-patterns, validation, FAQ, status, review, ownership). The DB is generated from catalog/,
so this is a pure schema change — data is re-seeded from the migrated YAML.

Revision ID: 005
Revises: 004
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("mitigations")
    op.create_table(
        "mitigations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("mitigation_class", sa.String(50), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("formal_implementation_risk", sa.Text(), nullable=True),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("maintainer", sa.String(255), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("locus", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("control_mechanism", sa.Text(), nullable=True),
        sa.Column("failure_behavior", sa.Text(), nullable=True),
        sa.Column("telemetry", sa.Text(), nullable=True),
        sa.Column("anti_patterns", sa.JSON(), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("faq", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("mitigations")
    op.create_table(
        "mitigations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("requirement_level", sa.String(50), nullable=True),
        sa.Column("implementations", sa.JSON(), nullable=True),
    )
