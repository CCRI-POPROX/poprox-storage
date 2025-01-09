"""create image_associations table

Revision ID: adf30c8ce87e
Revises: c2007fa35fc2
Create Date: 2024-12-11 16:33:01.573897

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'adf30c8ce87e'
down_revision: Union[str, None] = 'c2007fa35fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_image_associations",
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("image_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_image_associations_article_id",
        "article_image_associations",
        "articles",
        ["article_id"],
        ["article_id"],
    )

    op.create_foreign_key(
        "fk_image_associations_image_id",
        "article_image_associations",
        "images",
        ["image_id"],
        ["image_id"],
    )
    op.create_unique_constraint(
        "uq_article_image_associations",
        "article_image_associations",
        ["article_id", "image_id"]
    )



def downgrade() -> None:
    op.drop_constraint("fk_image_associations_article_id", "article_image_associations", type_="foreignkey")
    op.drop_constraint("fk_image_associations_image_id", "article_image_associations", type_="foreignkey")
    op.drop_table("article_image_associations")
