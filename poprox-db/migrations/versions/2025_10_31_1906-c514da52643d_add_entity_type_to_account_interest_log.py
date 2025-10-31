"""add entity_type to account_interest_log

Revision ID: c514da52643d
Revises: e4bed855bbf8
Create Date: 2025-10-31 19:06:16.904096

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c514da52643d'
down_revision: Union[str, None] = 'e4bed855bbf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("account_interest_log", sa.Column("entity_type", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("account_interest_log", "entity_type")
