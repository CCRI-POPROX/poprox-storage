"""Add constraint to candidate articles

Revision ID: 6cb50b5e9d44
Revises: 8365e8e80542
Create Date: 2025-12-01 16:13:27.052917

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6cb50b5e9d44"
down_revision: Union[str, None] = "8365e8e80542"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_candidate_articles_article_id",
        "candidate_articles",
        "articles",
        ["article_id"],
        ["article_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_candidate_articles_article_id", "candidate_articles")
