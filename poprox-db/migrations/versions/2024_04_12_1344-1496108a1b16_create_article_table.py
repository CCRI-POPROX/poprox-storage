"""create article table

Revision ID: 1496108a1b16
Revises: b84ba9163a5d
Create Date: 2024-04-12 13:44:05.476707

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1496108a1b16"
down_revision: Union[str, None] = "b84ba9163a5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Article table
# article_id: UUID
# title: str
# content: str
# url: str
# published_at: timestamp
# created_at: timestamp
def upgrade() -> None:
    op.create_table(
        "article",
        sa.Column(
            "article_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("content", sa.String),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("published_at", sa.DateTime, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_unique_constraint("uq_articles", "article", ("title", "url"))


def downgrade() -> None:
    op.drop_constraint("uq_articles", "article")
    op.drop_table("article")
