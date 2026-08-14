"""threat facets — impact_class, vector, surface

Adds the impact-centric facet columns to `threats`:
  impact_class — strict/minimal anchor (enum enforced in Pydantic, plain string here)
  vector       — prose: how the harmful output/action arises (cause)
  surface      — prose: trust boundary / interaction point

All nullable: existing rows keep NULL until the facet-authoring pass fills them.

Revision ID: 002
Revises: 001
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("threats", sa.Column("impact_class", sa.String(length=50), nullable=True))
    op.add_column("threats", sa.Column("vector", sa.Text(), nullable=True))
    op.add_column("threats", sa.Column("surface", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("threats", "surface")
    op.drop_column("threats", "vector")
    op.drop_column("threats", "impact_class")
