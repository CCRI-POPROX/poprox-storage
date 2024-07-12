"""add mentions table

Revision ID: 8c2b0c4c3ae5
Revises: 7784f1ca77d3
Create Date: 2024-05-14 15:40:48.293198

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c2b0c4c3ae5"
down_revision: Union[str, None] = "7784f1ca77d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mentions",
        sa.Column(
            "mention_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_id", sa.UUID, nullable=False),
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("source", sa.String, nullable=True),
        sa.Column("relevance", sa.Double, nullable=False),
    )

    op.create_foreign_key(
        "fk_mentions_article",
        "mentions",
        "article",
        ["article_id"],
        ["article_id"],
        ondelete="RESTRICT",
    )

    op.create_foreign_key(
        "fk_mentions_entity",
        "mentions",
        "entities",
        ["entity_id"],
        ["entity_id"],
        ondelete="RESTRICT",
    )

    op.create_unique_constraint(
        "uq_mentions", "mentions", ("entity_id", "article_id", "source")
    )


def downgrade() -> None:
    op.drop_constraint("uq_mentions", "mentions")
    op.drop_constraint("fk_mentions_entity", "mentions", type_="foreignkey")
    op.drop_constraint("fk_mentions_article", "mentions", type_="foreignkey")
    op.drop_table("mentions")
