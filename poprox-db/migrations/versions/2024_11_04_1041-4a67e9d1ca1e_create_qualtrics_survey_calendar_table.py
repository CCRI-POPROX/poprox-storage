"""create qualtrics_survey_calendar table

Revision ID: 4a67e9d1ca1e
Revises: ac1a317899d9
Create Date: 2024-11-04 10:41:33.258386

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a67e9d1ca1e"
down_revision: Union[str, None] = "ac1a317899d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qualtrics_survey_calendar",
        sa.Column(
            "calendar_entry_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("survey_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_survey_calendar_survey_id",
        "qualtrics_survey_calendar",
        "qualtrics_surveys",
        ["survey_id"],
        ["survey_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_survey_calendar_survey_id", "qualtrics_survey_calendar", type_="foreignkey")
    op.drop_table("qualtrics_survey_calendar")
