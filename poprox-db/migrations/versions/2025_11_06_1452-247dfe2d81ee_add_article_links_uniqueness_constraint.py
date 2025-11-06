"""Add article_links uniqueness constraint

Revision ID: 247dfe2d81ee
Revises: cfab7d94f987
Create Date: 2025-11-06 14:52:36.362195

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '247dfe2d81ee'
down_revision: Union[str, None] = 'cfab7d94f987'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_article_links", "article_links", ("source_article_id", "target_article_id", "link_text")
    )


def downgrade() -> None:
    op.drop_constraint("uq_article_links", "article_links")
