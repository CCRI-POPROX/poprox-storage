"""add opt-out column to experiment assignments

Revision ID: 211c6b3ac5de
Revises: 53fc350d4cd3
Create Date: 2024-07-26 09:53:57.652145

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "211c6b3ac5de"
down_revision: Union[str, None] = "53fc350d4cd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expt_assignments",
        sa.Column("opted_out", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("expt_assignments", "opted_out")
