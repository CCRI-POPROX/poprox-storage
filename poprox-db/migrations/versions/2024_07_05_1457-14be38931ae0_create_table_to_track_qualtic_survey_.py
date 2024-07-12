"""create table to track qualtic survey responses

Revision ID: 14be38931ae0
Revises: fefa750f5281
Create Date: 2024-07-05 14:57:16.651570

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "14be38931ae0"
down_revision: Union[str, None] = "fefa750f5281"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qualtrics_survey_responses",
        sa.Column(
            "survey_response_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # NOTE -- nullable=True is deliberate here. I want to account for possibly unlinkable survey responses.
        sa.Column("survey_instance_id", sa.UUID, nullable=True),
        sa.Column("qualtrics_response_id", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("raw_data", JSONB, nullable=True),
    )

    op.create_foreign_key(
        "fk_qualtrics_survey_responses_survey_instance_id",
        "qualtrics_survey_responses",
        "qualtrics_survey_instances",
        ["survey_instance_id"],
        ["survey_instance_id"],
    )

    op.create_unique_constraint(
        "uq_qualtrics_response_id",
        "qualtrics_survey_responses",
        ("qualtrics_response_id",),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_qualtrics_survey_responses_survey_instance_id",
        "qualtrics_survey_responses",
        type_="foreignkey",
    )
    op.drop_constraint("uq_qualtrics_response_id", "qualtrics_survey_responses")

    op.drop_table("qualtrics_survey_responses")
