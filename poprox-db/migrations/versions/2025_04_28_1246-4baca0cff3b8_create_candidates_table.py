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
        "candidate_pools",
        sa.Column("candidate_pool_id", sa.UUID, primary_key=True),
        sa.Column("pool_type", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "candidate_articles",
        sa.Column("candidate_pool_id", sa.UUID, nullable=False),
        sa.Column("article_id",sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_foreign_key(
        "fk_candidate_articles_pool_id",
        "candidate_articles",
        "candidate_pools",
        ["candidate_pool_id"],
        ["candidate_pool_id"],
    )

    op.create_unique_constraint("uq_candidate_articles", "candidate_articles", ("candidate_pool_id", "article_id"))


def downgrade() -> None:
    op.drop_constraint("uq_candidate_articles", "candidate_articles")
    op.drop_constraint("fk_candidate_articles_pool_id", "candidate_articles", type_="foreignkey")
    op.drop_table("candidate_articles")
    op.drop_table("candidate_pools")
