"""create table to track qualtic surveys

Revision ID: 5231010a6b14
Revises: b705c3374dfa
Create Date: 2024-07-05 14:40:13.331142

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5231010a6b14"
down_revision: Union[str, None] = "b705c3374dfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qualtrics_surveys",
        sa.Column(
            "survey_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("qualtrics_id", sa.String, nullable=False),
        sa.Column("base_url", sa.String, nullable=False),
        sa.Column("continuation_token", sa.String, default=sa.null()),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_updated", sa.DateTime, nullable=True, onupdate=sa.text("NOW()")),
    )
    op.create_unique_constraint("uq_qualtrics_id", "qualtrics_surveys", ("qualtrics_id",))


def downgrade() -> None:
    op.drop_constraint("uq_qualtrics_id", "qualtrics_surveys")
    op.drop_table("qualtrics_surveys")
