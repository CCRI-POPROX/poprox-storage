"""add preview image url column to articles table

Revision ID: 5d566fff8aaa
Revises: 8fa118cae13f
Create Date: 2024-07-10 15:33:02.131813

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d566fff8aaa"
down_revision: str | None = "8fa118cae13f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("preview_image_id", sa.UUID(), nullable=True),
    )

    op.create_foreign_key(
        "fk_articles_preview_image_id",
        "articles",
        "images",
        ["preview_image_id"],
        ["image_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_articles_preview_image_id", "articles", type_="foreignkey")
    op.drop_column("articles", "preview_image_id")
