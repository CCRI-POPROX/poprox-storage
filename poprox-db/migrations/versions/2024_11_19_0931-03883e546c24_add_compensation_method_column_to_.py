"""add compensation method column to accounts table

Revision ID: 03883e546c24
Revises: 2f7fd221e67c
Create Date: 2024-11-19 09:31:16.868146

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "03883e546c24"
down_revision: Union[str, None] = "2f7fd221e67c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("compensation", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "compensation")
