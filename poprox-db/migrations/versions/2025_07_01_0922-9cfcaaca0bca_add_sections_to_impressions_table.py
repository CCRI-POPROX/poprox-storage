"""Add sections to impressions table

Revision ID: 9cfcaaca0bca
Revises: 72901f4ab61c
Create Date: 2025-07-01 09:22:33.547681

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9cfcaaca0bca'
down_revision: Union[str, None] = '72901f4ab61c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "impressions",
        sa.Column("section_name", sa.String, nullable=True),
    )

    op.add_column(
        "impressions",
        sa.Column("position_in_section", sa.Integer, nullable=True),
    )

    # Positions must be positive
    op.create_check_constraint(
        "ch_impressions_position_in_section_positive", "impressions", sa.sql.column("position_in_section") > 0
    )


def downgrade() -> None:
    op.drop_constraint("ch_impressions_position_in_section_positive", "impressions")
    op.drop_column("impressions", "section_name")
    op.drop_column("impressions", "position_in_section")
