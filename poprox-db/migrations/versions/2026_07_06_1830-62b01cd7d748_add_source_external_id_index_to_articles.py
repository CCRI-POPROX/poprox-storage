"""add source external_id index to articles

Adds a non-unique index on articles(source, external_id) to back the source-aware
lookup added to DbArticleRepository.fetch_article_by_external_id. The pair is
intentionally NOT unique: multiple rows per (source, external_id) are expected --
they are kept as history and deduped to the latest row at read time.

Revision ID: 62b01cd7d748
Revises: d4e5f6a7b8c9
Create Date: 2026-07-06 18:30:32.656756

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "62b01cd7d748"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_articles_source_external_id", "articles", ["source", "external_id"])


def downgrade() -> None:
    op.drop_index("ix_articles_source_external_id", table_name="articles")
