"""create candidates table

Revision ID: 4baca0cff3b8
Revises: bad8a290077a
Create Date: 2025-04-28 12:46:08.761767

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4baca0cff3b8'
down_revision: Union[str, None] = 'bad8a290077a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_articles",
        sa.Column("article_id",sa.UUID, nullable=False),
        sa.Column("candidate_on", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_unique_constraint("uq_candidate_articles", "candidate_articles", ("article_id", "candidate_on"))


def downgrade() -> None:
    op.drop_constraint("uq_candidate_articles", "candidate_articles")
    op.drop_table("candidate_articles")
