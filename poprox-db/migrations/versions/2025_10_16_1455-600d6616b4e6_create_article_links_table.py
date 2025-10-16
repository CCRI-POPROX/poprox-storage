"""Create article links table

Revision ID: 600d6616b4e6
Revises: 3a40fabe9845
Create Date: 2025-10-16 14:55:07.193353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '600d6616b4e6'
down_revision: Union[str, None] = '3a40fabe9845'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_links",
        sa.Column(
            "link_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),

        sa.Column("source_article_id", sa.UUID, nullable=False),
        sa.Column("target_article_id", sa.UUID, nullable=False),
        sa.Column("link_text", sa.String, nullable=False),
    )

    op.create_foreign_key(
        "fk_article_links_source_id",
        "article_links",
        "articles",
        ["source_article_id"],
        ["article_id"],
    )

    op.create_foreign_key(
        "fk_article_links_target_id",
        "article_links",
        "articles",
        ["target_article_id"],
        ["article_id"],
    )

def downgrade() -> None:
    op.drop_constraint("fk_article_links_source_id", "article_links", type_="foreignkey")
    op.drop_constraint("fk_article_links_target_id", "article_links", type_="foreignkey")
    op.drop_table("article_links")
