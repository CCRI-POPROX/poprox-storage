"""Create an experiences table

Revision ID: 87aa4d7933b2
Revises: 53e035b208d0
Create Date: 2025-06-07 08:54:46.636431

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '87aa4d7933b2'
down_revision: Union[str, None] = '53e035b208d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experiences",
        sa.Column("experience_id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("recommender_id", sa.UUID, nullable=False),
        sa.Column("team_id", sa.UUID, nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_experiences_recommender_id",
        "experiences",
        "recommenders",
        ["recommender_id"],
        ["recommender_id"],
    )
    op.create_foreign_key(
        "fk_top_stories_team_id",
        "experiences",
        "teams",
        ["team_id"],
        ["team_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_top_stories_team_id", "top_stories", type_="foreignkey")
    op.drop_constraint("fk_experiences_recommender_id", "top_stories", type_="foreignkey")

    op.drop_table("experiences")
