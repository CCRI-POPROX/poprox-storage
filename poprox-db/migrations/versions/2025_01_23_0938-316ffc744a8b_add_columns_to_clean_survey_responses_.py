"""Add columns to clean survey responses table

Revision ID: 316ffc744a8b
Revises: f6ccafdb5b24
Create Date: 2025-01-23 09:38:51.366350

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "316ffc744a8b"
down_revision: Union[str, None] = "f6ccafdb5b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qualtrics_clean_responses", sa.Column("account_id", sa.UUID, nullable=False))
    op.add_column("qualtrics_clean_responses", sa.Column("survey_id", sa.UUID, nullable=False))
    op.add_column("qualtrics_clean_responses", sa.Column("qualtrics_id", sa.String, nullable=False))
    op.add_column("qualtrics_clean_responses", sa.Column("survey_code", sa.String, nullable=True))

    op.create_foreign_key(
        "fk_qualtrics_clean_responses_account_id",
        "qualtrics_clean_responses",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_qualtrics_clean_responses_survey_id",
        "qualtrics_clean_responses",
        "qualtrics_surveys",
        ["survey_id"],
        ["survey_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_qualtrics_clean_responses_account_id", "qualtrics_clean_responses", type_="foreignkey")
    op.drop_constraint("fk_qualtrics_clean_responses_survey_id", "qualtrics_clean_responses", type_="foreignkey")

    op.drop_column("qualtrics_clean_responses", "survey_code")
    op.drop_column("qualtrics_clean_responses", "qualtrics_id")
    op.drop_column("qualtrics_clean_responses", "survey_id")
    op.drop_column("qualtrics_clean_responses", "account_id")
