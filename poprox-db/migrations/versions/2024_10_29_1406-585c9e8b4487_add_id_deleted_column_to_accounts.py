"""add id_deleted column to accounts

Revision ID: 585c9e8b4487
Revises: f8667df4b049
Create Date: 2024-10-29 14:06:53.219760

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "585c9e8b4487"
down_revision: Union[str, None] = "f8667df4b049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("is_deleted", sa.Boolean, nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "is_deleted")
