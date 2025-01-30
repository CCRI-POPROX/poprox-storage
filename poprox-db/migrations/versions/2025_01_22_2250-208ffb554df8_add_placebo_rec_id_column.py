"""add rec_id column

Revision ID: 208ffb554df8
Revises: f6ccafdb5b24
Create Date: 2025-01-22 22:50:25.365300

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "208ffb554df8"
down_revision: Union[str, None] = "f6ccafdb5b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("rec_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "rec_id")
