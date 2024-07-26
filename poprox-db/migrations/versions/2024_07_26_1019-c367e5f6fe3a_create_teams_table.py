"""create teams table

Revision ID: c367e5f6fe3a
Revises: fc8d79481ee4
Create Date: 2024-07-26 10:19:42.502432

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c367e5f6fe3a"
down_revision: Union[str, None] = "fc8d79481ee4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column(
            "team_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("teams")
