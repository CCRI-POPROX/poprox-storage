"""remove section_name column

Revision ID: d737977ed772
Revises: 6cb50b5e9d44, c83db2581bc4
Create Date: 2025-12-12 20:18:21.561769

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d737977ed772"
down_revision: Union[str, None] = ("6cb50b5e9d44", "c83db2581bc4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_impressions_newsletter_section_position", "impressions")
    op.drop_column("impressions", "section_name")


def downgrade() -> None:
    op.add_column(
        "impressions",
        sa.Column("section_name", sa.String, nullable=True),
    )

    # Each position in each section can only occur once per newsletter
    op.create_unique_constraint(
        "uq_impressions_newsletter_section_position",
        "impressions",
        ["newsletter_id", "section_name", "position_in_section"],
    )
