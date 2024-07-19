"""add raw data column to articles table

Revision ID: b705c3374dfa
Revises: 185dacfa54c0
Create Date: 2024-07-01 09:10:49.622969

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "b705c3374dfa"
down_revision: str | None = "185dacfa54c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("source", sa.String, nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("external_id", sa.String, nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("raw_data", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("articles", "source")
    op.drop_column("articles", "external_id")
    op.drop_column("articles", "raw_data")
