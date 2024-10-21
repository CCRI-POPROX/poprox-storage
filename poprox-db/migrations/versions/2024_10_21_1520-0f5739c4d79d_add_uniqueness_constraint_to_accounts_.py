"""Add uniqueness constraint to accounts table

Revision ID: 0f5739c4d79d
Revises: 9370e559b657
Create Date: 2024-10-21 15:20:58.490255

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f5739c4d79d"
down_revision: Union[str, None] = "9370e559b657"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_accounts", "accounts", ("email",))


def downgrade() -> None:
    op.drop_constraint("uq_accounts", "accounts")
