"""add label column to impressions table

Revision ID: 9aab06f29f2e
Revises: 8f61da0a457c
Create Date: 2026-02-02 14:25:51.332191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9aab06f29f2e'
down_revision: Union[str, None] = '8f61da0a457c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "impressions",
        sa.Column("label", sa.String, nullable=True, default=sa.Null),
    )


def downgrade() -> None:
    op.drop_column("impressions", "label")
