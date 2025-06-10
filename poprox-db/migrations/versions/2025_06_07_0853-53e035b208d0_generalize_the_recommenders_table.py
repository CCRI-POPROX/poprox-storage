"""Generalize the recommenders table

Revision ID: 53e035b208d0
Revises: 61310e29d84f
Create Date: 2025-06-07 08:53:32.337982

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '53e035b208d0'
down_revision: Union[str, None] = '61310e29d84f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("expt_recommenders", "recommenders")
    op.add_column(
        "recommenders",
        sa.Column("template", sa.String, nullable=True),
    )
    op.add_column(
        "recommenders",
        sa.Column("team_id", sa.UUID, nullable=True),
    )

    op.create_foreign_key(
        "fk_recommenders_team_id",
        "recommenders",
        "teams",
        ["team_id"],
        ["team_id"],
    )

    op.create_check_constraint("ch_recommenders_team_or_expt", "recommenders",
                               sa.or_(
                                   sa.sql.column("experiment_id") is not None,
                                   sa.sql.column("team_id") is not None
                                )
                            )

    op.alter_column("recommenders", "experiment_id", nullable=True)

def downgrade() -> None:
    op.alter_column("recommenders", "experiment_id", nullable=False)
    op.drop_constraint("ch_recommenders_team_or_expt", "recommenders")
    op.drop_constraint("fk_recommenders_team_id", "recommenders", type_="foreignkey")
    op.drop_column("recommenders", "team_id")
    op.drop_column("recommenders", "template")
    op.rename_table("recommenders", "expt_recommenders")
