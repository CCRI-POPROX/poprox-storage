"""added newsletter feedback to newsletter table

Revision ID: 2b04e29af064
Revises: cd48a13758b9
Create Date: 2025-03-24 17:40:23.076888

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2b04e29af064'
down_revision: Union[str, None] = 'cd48a13758b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "newsletters",
        sa.Column("feedback", sa.BOOLEAN, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("newsletters", "feedback")
