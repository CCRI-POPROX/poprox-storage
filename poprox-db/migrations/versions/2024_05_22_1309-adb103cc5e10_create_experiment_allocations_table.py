"""create experiment allocations table

Revision ID: adb103cc5e10
Revises: aad7bde678ba
Create Date: 2024-05-22 13:09:57.172205

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "adb103cc5e10"
down_revision: Union[str, None] = "aad7bde678ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expt_allocations",
        sa.Column(
            "allocation_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("group_id", sa.UUID, nullable=False),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
    )

    op.create_foreign_key(
        "fk_expt_allocations_account_id",
        "expt_allocations",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_expt_allocations_group_id",
        "expt_allocations",
        "expt_groups",
        ["group_id"],
        ["group_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_expt_allocations_group_id", "expt_allocations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_expt_allocations_account_id", "expt_allocations", type_="foreignkey"
    )

    op.drop_table("expt_allocations")
