"""create team memberships table

Revision ID: 3e73b9c0cd35
Revises: c367e5f6fe3a
Create Date: 2024-07-26 10:20:15.921779

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e73b9c0cd35"
down_revision: Union[str, None] = "c367e5f6fe3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_memberships",
        sa.Column(
            "membership_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("team_id", sa.UUID, nullable=False),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_team_memberships_team_id",
        "team_memberships",
        "teams",
        ["team_id"],
        ["team_id"],
    )

    op.create_foreign_key(
        "fk_team_memberships_account_id",
        "team_memberships",
        "accounts",
        ["account_id"],
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_team_memberships_account_id", "team_memberships", type_="foreignkey")
    op.drop_constraint("fk_team_memberships_team_id", "team_memberships", type_="foreignkey")
    op.drop_table("team_memberships")
