"""add account status field to account table to track progress when onboarding. as well field for tracking source

Revision ID: ddf8de4a8fa5
Revises: 10b32c41ed65
Create Date: 2024-06-14 11:12:30.235044

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ddf8de4a8fa5"
down_revision: Union[str, None] = "10b32c41ed65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("status", sa.String(), default="new_account", nullable=True),
    )
    op.add_column(
        "accounts",
        sa.Column("source", sa.String(), nullable=True),
    )

    op.execute(
        """
        update accounts set status='new_account', source='team' where status is null;
        """
    )

    op.alter_column("accounts", "status", nullable=False)
    op.alter_column("accounts", "source", nullable=False)


def downgrade() -> None:
    op.drop_column("accounts", "status")
    op.drop_column("accounts", "source")
