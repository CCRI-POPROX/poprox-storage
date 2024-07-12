"""add article images table

Revision ID: 8fa118cae13f
Revises: b705c3374dfa
Create Date: 2024-07-05 10:29:25.409736

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "8fa118cae13f"
down_revision: Union[str, None] = "b705c3374dfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "images",
        sa.Column(
            "image_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=True),
        sa.Column("external_id", sa.String, nullable=True),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_unique_constraint("uq_images", "images", ("source", "external_id"))


def downgrade() -> None:
    op.drop_constraint("uq_images", "images")
    op.drop_table("images")
