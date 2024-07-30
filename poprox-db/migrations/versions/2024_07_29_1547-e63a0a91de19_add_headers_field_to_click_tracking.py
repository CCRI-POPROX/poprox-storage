"""add headers field to click tracking

Revision ID: e63a0a91de19
Revises: 98ff1c3ebe33
Create Date: 2024-07-29 15:47:21.060606

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "e63a0a91de19"
down_revision: Union[str, None] = "98ff1c3ebe33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clicks",
        sa.Column("headers", JSONB, nullable=True, server_default=sa.null()),
    )


def downgrade() -> None:
    op.drop_column("clicks", "headers")
