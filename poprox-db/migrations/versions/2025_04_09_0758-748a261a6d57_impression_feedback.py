"""Impression feedback

Revision ID: 748a261a6d57
Revises: 2b04e29af064
Create Date: 2025-04-09 07:58:02.592917

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '748a261a6d57'
down_revision: Union[str, None] = '2b04e29af064'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "impressions",
        sa.Column("feedback", sa.BOOLEAN, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("impressions", "feedback")
