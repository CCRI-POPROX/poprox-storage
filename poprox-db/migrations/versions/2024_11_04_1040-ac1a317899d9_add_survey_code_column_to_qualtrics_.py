"""add survey_code column to qualtrics_surveys table

Revision ID: ac1a317899d9
Revises: 8f10a2101cb8
Create Date: 2024-11-04 10:40:23.404585

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ac1a317899d9"
down_revision: Union[str, None] = "8f10a2101cb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qualtrics_surveys", sa.Column("survey_code", sa.String(length=3), nullable=True))


def downgrade() -> None:
    op.drop_column("qualtrics_surveys", "survey_code")
