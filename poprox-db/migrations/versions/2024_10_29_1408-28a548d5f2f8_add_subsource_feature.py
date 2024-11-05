"""add subsource feature

Revision ID: 28a548d5f2f8
Revises: 9370e559b657
Create Date: 2024-10-29 14:08:17.018870

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "28a548d5f2f8"
down_revision: Union[str, None] = "9370e559b657"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("subsource", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "subsource")
