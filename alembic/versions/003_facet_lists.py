"""vector/surface become prose lists (Text -> JSON)

A threat's `vector` and `surface` are independent axes of prose items, not single
blobs. Storing them as JSON lists keeps each boundary/cause enumerable (coverage)
while staying prose. They are NOT bound to each other — the binding (a concrete
scenario) is an assessment-time product, so we keep O(n) axis values, not the
O(n^k) cross-product.

Columns are empty (facets not yet authored), so no data migration is needed; on
SQLite JSON has TEXT affinity, so this is effectively an annotation change.

Revision ID: 003
Revises: 002
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("threats") as batch:
        batch.alter_column("vector", type_=sa.JSON(), existing_type=sa.Text(), existing_nullable=True)
        batch.alter_column("surface", type_=sa.JSON(), existing_type=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("threats") as batch:
        batch.alter_column("vector", type_=sa.Text(), existing_type=sa.JSON(), existing_nullable=True)
        batch.alter_column("surface", type_=sa.Text(), existing_type=sa.JSON(), existing_nullable=True)
