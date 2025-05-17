"""Create top_stories table

Revision ID: 1d20bc70fa6d
Revises: 45d10f860ff6
Create Date: 2025-05-17 07:54:17.565202

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1d20bc70fa6d'
down_revision: Union[str, None] = '45d10f860ff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "top_stories",
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("entity_id", sa.UUID, nullable=False),
        sa.Column("headline", sa.String, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("as_of", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_top_stories_article_id",
        "top_stories",
        "articles",
        ["article_id"],
        ["article_id"],
    )

    op.create_foreign_key(
        "fk_top_stories_entity_id",
        "top_stories",
        "entities",
        ["entity_id"],
        ["entity_id"],
    )

    # Positions must be positive
    op.create_check_constraint("ch_top_stories_position_positive", "top_stories", sa.sql.column("position") > 0)

    # Each position can only have one article per topic (entity)
    op.create_unique_constraint("uq_top_stories_position", "top_stories", ("entity_id", "position", "as_of"))
    
    # Each article can only have one position per topic (entity)
    op.create_unique_constraint("uq_top_stories_topic", "top_stories", ("entity_id", "article_id", "as_of"))


def downgrade() -> None:
    op.drop_constraint("ch_top_stories_position_positive", "top_stories")
    op.drop_constraint("uq_top_stories_topic", "top_stories")
    op.drop_constraint("uq_top_stories_position", "top_stories")

    op.drop_constraint("fk_top_stories_entity_id", "top_stories", type_="foreignkey")
    op.drop_constraint("fk_top_stories_article_id", "top_stories", type_="foreignkey")

    op.drop_table("top_stories")