"""create table to track qualtic surveys_instances

Revision ID: fefa750f5281
Revises: 5231010a6b14
Create Date: 2024-07-05 14:50:46.574307

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fefa750f5281"
down_revision: str | None = "5231010a6b14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "qualtrics_survey_instances",
        sa.Column(
            "survey_instance_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("survey_id", sa.UUID, nullable=False),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_qualtrics_survey_instances_accounts_account_id",
        "qualtrics_survey_instances",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_qualtrics_survey_instances_qualtrics_surveys_survey_id",
        "qualtrics_survey_instances",
        "qualtrics_surveys",
        ["survey_id"],
        ["survey_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_qualtrics_survey_instances_accounts_account_id",
        "qualtrics_survey_instances",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_qualtrics_survey_instances_qualtrics_surveys_survey_id",
        "qualtrics_survey_instances",
        type_="foreignkey",
    )
    op.drop_table("qualtrics_survey_instances")
