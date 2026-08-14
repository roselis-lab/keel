"""initial lean schema — threats, mitigations, link, style guide

Revision ID: 001
Revises:
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "threats",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("applicability", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "mitigations",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("requirement_level", sa.String(length=50), nullable=True),
        sa.Column("implementations", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "threat_mitigations",
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("threat_id", sa.String(length=50), nullable=False),
        sa.Column("mitigation_id", sa.String(length=50), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["threat_id"], ["threats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mitigation_id"], ["mitigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "style_guide_field",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("content_requirements", sa.JSON(), nullable=True),
        sa.Column("instructions", sa.JSON(), nullable=True),
        sa.Column("avoid", sa.JSON(), nullable=True),
        sa.Column("examples", sa.JSON(), nullable=True),
        sa.Column("subfields", sa.JSON(), nullable=True),
        sa.Column("allowed_values", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_orphan", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "field_name", name="uq_style_guide_field"),
    )


def downgrade() -> None:
    op.drop_table("style_guide_field")
    op.drop_table("threat_mitigations")
    op.drop_table("mitigations")
    op.drop_table("threats")
