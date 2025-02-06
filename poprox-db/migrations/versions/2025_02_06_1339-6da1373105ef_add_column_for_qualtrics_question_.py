"""add column for qualtrics question metadata

Revision ID: 6da1373105ef
Revises: a67fedcb0af0
Create Date: 2025-02-06 13:39:14.630988

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "6da1373105ef"
down_revision: Union[str, None] = "a67fedcb0af0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("qualtrics_surveys", sa.Column("question_metadata", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("qualtrics_surveys", "question_metadata")
