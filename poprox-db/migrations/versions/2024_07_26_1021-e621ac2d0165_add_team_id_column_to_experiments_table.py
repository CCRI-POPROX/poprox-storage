"""add team id column to experiments table

Revision ID: e621ac2d0165
Revises: 3e73b9c0cd35
Create Date: 2024-07-26 10:21:17.777032

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e621ac2d0165"
down_revision: Union[str, None] = "3e73b9c0cd35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "experiments",
        sa.Column("team_id", sa.UUID, nullable=False),
    )

    op.create_foreign_key(
        "fk_experiments_team_id",
        "experiments",
        "teams",
        ["team_id"],
        ["team_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_experiments_team_id", "experiments", type_="foreignkey")
    op.drop_column("experiments", "team_id")
