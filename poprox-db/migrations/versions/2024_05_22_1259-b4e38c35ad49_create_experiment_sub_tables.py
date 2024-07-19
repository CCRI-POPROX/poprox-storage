"""create experiment sub-tables

Revision ID: b4e38c35ad49
Revises: abbe1a8bef82
Create Date: 2024-05-22 12:59:44.142662

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e38c35ad49"
down_revision: str | None = "abbe1a8bef82"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expt_groups",
        sa.Column(
            "group_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("group_name", sa.String, nullable=False),
        sa.Column("experiment_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_expt_groups_experiment_id",
        "expt_groups",
        "experiments",
        ["experiment_id"],
        ["experiment_id"],
    )

    op.create_unique_constraint("uq_expt_groups_name_experiment", "expt_groups", ("group_name", "experiment_id"))

    op.create_table(
        "expt_phases",
        sa.Column(
            "phase_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("phase_name", sa.String, nullable=False),
        sa.Column("experiment_id", sa.UUID, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_expt_phases_experiment_id",
        "expt_phases",
        "experiments",
        ["experiment_id"],
        ["experiment_id"],
    )

    op.create_unique_constraint("uq_expt_phases_name_experiment", "expt_phases", ("phase_name", "experiment_id"))

    op.create_table(
        "expt_recommenders",
        sa.Column(
            "recommender_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("recommender_name", sa.String, nullable=False),
        sa.Column("endpoint_url", sa.String, nullable=False),
        sa.Column("experiment_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_expt_recommenders_experiment_id",
        "expt_recommenders",
        "experiments",
        ["experiment_id"],
        ["experiment_id"],
    )

    op.create_unique_constraint(
        "uq_expt_recommenders_name_experiment",
        "expt_recommenders",
        ("recommender_name", "experiment_id"),
    )


def downgrade() -> None:
    op.drop_constraint("fk_expt_recommenders_experiment_id", "expt_recommenders", type_="foreignkey")
    op.drop_constraint("uq_expt_recommenders_name_experiment", "expt_recommenders")
    op.drop_table("expt_recommenders")

    op.drop_constraint("fk_expt_phases_experiment_id", "expt_phases", type_="foreignkey")
    op.drop_constraint("uq_expt_phases_name_experiment", "expt_phases")
    op.drop_table("expt_phases")

    op.drop_constraint("fk_expt_groups_experiment_id", "expt_groups", type_="foreignkey")
    op.drop_constraint("uq_expt_groups_name_experiment", "expt_groups")
    op.drop_table("expt_groups")
