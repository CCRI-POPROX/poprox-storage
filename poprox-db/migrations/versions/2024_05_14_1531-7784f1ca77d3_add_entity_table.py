"""add entity table

Revision ID: 7784f1ca77d3
Revises: a5be6e14d5ff
Create Date: 2024-05-14 15:31:53.092234

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "7784f1ca77d3"
down_revision: Union[str, None] = "a5be6e14d5ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column(
            "entity_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("external_id", sa.String, nullable=True),
        sa.Column("raw_data", JSONB, nullable=True),
    )

    op.create_unique_constraint("uq_entities", "entities", ("entity_type", "name", "source", "external_id"))


def downgrade() -> None:
    op.drop_constraint("uq_entities", "entities")
    op.drop_table("entities")
