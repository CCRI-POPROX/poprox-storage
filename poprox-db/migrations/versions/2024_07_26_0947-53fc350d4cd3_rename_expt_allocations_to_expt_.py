"""rename expt_allocations to expt_assignments

Revision ID: 53fc350d4cd3
Revises: fc8d79481ee4
Create Date: 2024-07-26 09:47:21.351380

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "53fc350d4cd3"
down_revision: Union[str, None] = "fc8d79481ee4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_expt_allocations_group_id", "expt_allocations", type_="foreignkey")
    op.drop_constraint("fk_expt_allocations_account_id", "expt_allocations", type_="foreignkey")

    op.alter_column("expt_allocations", "allocation_id", new_column_name="assignment_id")
    op.rename_table("expt_allocations", "expt_assignments")

    op.create_foreign_key(
        "fk_expt_assignments_account_id",
        "expt_assignments",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_expt_assignments_group_id",
        "expt_assignments",
        "expt_groups",
        ["group_id"],
        ["group_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_expt_assignments_group_id", "expt_assignments", type_="foreignkey")
    op.drop_constraint("fk_expt_assignments_account_id", "expt_assignments", type_="foreignkey")

    op.alter_column("expt_assignments", "assignment_id", new_column_name="allocation_id")
    op.rename_table("expt_assignments", "expt_allocations")

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
