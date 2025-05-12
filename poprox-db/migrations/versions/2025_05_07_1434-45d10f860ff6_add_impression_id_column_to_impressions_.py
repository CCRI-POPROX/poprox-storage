"""add impression_id column to impressions table

Revision ID: 45d10f860ff6
Revises: 2a18762e7703
Create Date: 2025-05-07 14:34:22.412392

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45d10f860ff6"
down_revision: Union[str, None] = "2a18762e7703"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "impressions",
        sa.Column("impression_id", sa.UUID, server_default=sa.text("gen_random_uuid()")),
    )
    op.create_primary_key("pk_impressions_impression_id", "impressions", ["impression_id"])


def downgrade() -> None:
    op.drop_constraint("pk_impressions_impression_id", "impressions")
    op.drop_column("impressions", "impression_id")
