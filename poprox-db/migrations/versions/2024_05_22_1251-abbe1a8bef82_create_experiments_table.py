"""create experiments table

Revision ID: abbe1a8bef82
Revises: 12db57e34931
Create Date: 2024-05-22 12:51:38.075973

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "abbe1a8bef82"
down_revision: Union[str, None] = "12db57e34931"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column(
            "experiment_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
    )


def downgrade() -> None:
    op.drop_table("experiments")
