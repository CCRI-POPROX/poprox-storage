"""Create survey_responses table

Revision ID: bc86d0a8b32f
Revises: 03883e546c24
Create Date: 2024-12-20 14:21:24.816917

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "bc86d0a8b32f"
down_revision: Union[str, None] = "03883e546c24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qualtrics_clean_responses",
        sa.Column(
            "survey_response_id",
            sa.UUID,
            primary_key=True,
        ),
        sa.Column("survey_instance_id", sa.UUID, nullable=False),
        sa.Column("response_values", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_clean_responses_survey_response_id",
        "qualtrics_clean_responses",
        "qualtrics_survey_responses",
        ["survey_response_id"],
        ["survey_response_id"],
    )

    op.create_foreign_key(
        "fk_clean_responses_survey_instance_id",
        "qualtrics_clean_responses",
        "qualtrics_survey_instances",
        ["survey_instance_id"],
        ["survey_instance_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_clean_responses_survey_response_id", "qualtrics_clean_responses", type_="foreignkey")
    op.drop_constraint("fk_clean_responses_survey_instance_id", "qualtrics_clean_responses", type_="foreignkey")
    op.drop_table("qualtrics_clean_responses")
