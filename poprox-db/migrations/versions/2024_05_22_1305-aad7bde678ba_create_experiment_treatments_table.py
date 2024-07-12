"""create experiment treatments table

Revision ID: aad7bde678ba
Revises: b4e38c35ad49
Create Date: 2024-05-22 13:05:19.632323

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aad7bde678ba"
down_revision: Union[str, None] = "b4e38c35ad49"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expt_treatments",
        sa.Column(
            "treatment_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("recommender_id", sa.UUID, nullable=False),
        sa.Column("phase_id", sa.UUID, nullable=False),
        sa.Column("group_id", sa.UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
    )

    op.create_foreign_key(
        "fk_expt_treatments_recommender_id",
        "expt_treatments",
        "expt_recommenders",
        ["recommender_id"],
        ["recommender_id"],
    )

    op.create_foreign_key(
        "fk_expt_treatments_phase_id",
        "expt_treatments",
        "expt_phases",
        ["phase_id"],
        ["phase_id"],
    )

    op.create_foreign_key(
        "fk_expt_treatments_group_id",
        "expt_treatments",
        "expt_groups",
        ["group_id"],
        ["group_id"],
    )

    op.create_unique_constraint(
        "uq_expt_treatments_group_phase_ids",
        "expt_treatments",
        ("group_id", "phase_id"),
    )


def downgrade() -> None:
    op.drop_constraint("uq_expt_treatments_group_phase_ids", "expt_treatments")

    op.drop_constraint(
        "fk_expt_treatments_group_id", "expt_treatments", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_expt_treatments_phase_id", "expt_treatments", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_expt_treatments_recommender_id", "expt_treatments", type_="foreignkey"
    )

    op.drop_table("expt_treatments")
