"""update placebo_id column to UUID with default

Revision ID: a09bfb1c0f31
Revises: c036f401651b
Create Date: 2026-02-25 09:52:12.189546

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a09bfb1c0f31"
down_revision: Union[str, None] = "c036f401651b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("accounts", "placebo_id")
    op.add_column(
        "accounts",
        sa.Column(
            "placebo_id",
            sa.UUID,
            nullable=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("accounts", "placebo_id")
    op.add_column(
        "accounts",
        sa.Column("placebo_id", sa.UUID, nullable=True),
    )
