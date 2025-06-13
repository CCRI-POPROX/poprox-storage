"""Create tokens table

Revision ID: 356522e9ea7b
Revises: 151edfaa96af
Create Date: 2025-06-13 12:17:53.446071

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '356522e9ea7b'
down_revision: Union[str, None] = '151edfaa96af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tokens",
        sa.Column("token_id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("tokens")
