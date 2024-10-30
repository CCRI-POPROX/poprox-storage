"""add ended_at in account_consent_log

Revision ID: f15365e37756
Revises: 585c9e8b4487
Create Date: 2024-10-29 21:36:40.856197

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f15365e37756"
down_revision: Union[str, None] = "585c9e8b4487"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("account_consent_log", sa.Column("ended_at", sa.DateTime, nullable=True))


def downgrade() -> None:
    op.drop_column("account_consent_log", "ended_at")
