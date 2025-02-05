"""Add hidden column to clicks table

Revision ID: a8b87deb82b5
Revises: f6ccafdb5b24
Create Date: 2025-01-29 13:56:25.912158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8b87deb82b5'
down_revision: Union[str, None] = 'f6ccafdb5b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clicks", sa.Column("hidden", sa.Boolean, nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("clicks", "hidden")
