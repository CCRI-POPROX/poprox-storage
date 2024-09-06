"""create article_placements table

Revision ID: 4fc4a6030444
Revises: 23409beee637
Create Date: 2024-08-21 16:39:29.883880

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fc4a6030444"
down_revision: Union[str, None] = "23409beee637"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Article placements table
# article_id: UUID, foreign key
# url: str, primary key
# section: str
# level: str
# image_url: str
# created_at: timestamp
# article_id_fk = sa.ForeignKeyConstraint(
#     ["article_id"],
#     ["article.article_id"],
#     name="fk_article_placements_articles",
# )


def upgrade() -> None:
    op.create_table(
        "article_placements",
        *[
            sa.Column("article_id", sa.UUID, primary_key=True, nullable=False),
            sa.Column("url", sa.String, nullable=False),
            sa.Column("section", sa.String, nullable=False),
            sa.Column("level", sa.String),
            sa.Column("image_url", sa.String, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        ],
    )
    op.create_foreign_key(
        "fk_articles_placements_articles",
        "article_placements",
        "articles",
        ["article_id"],
        ["article_id"]
    )


def downgrade() -> None:
    # Drop the FK constraint before dropping the table
    op.drop_constraint(
        "fk_article_placements_articles",
        "article_placements",
        type_="foreignkey",
    )

    # Drop the table if it exists
    op.drop_table("article_placements")
