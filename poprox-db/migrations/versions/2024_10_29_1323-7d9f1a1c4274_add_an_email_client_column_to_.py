"""add an email client column to demographics

Revision ID: 7d9f1a1c4274
Revises: 042705b8457c
Create Date: 2024-10-29 13:23:15.381486

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7d9f1a1c4274'
down_revision: Union[str, None] = '042705b8457c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "demographics",
        sa.Column("email_client", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("demographics", "email_client")
