"""update impression ids on clicks

Revision ID: 97cd9a356543
Revises: 81af2711e062
Create Date: 2025-12-09 10:15:09.396710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '97cd9a356543'
down_revision: Union[str, None] = '81af2711e062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE clicks
        SET impression_id=impressions.impression_id
        FROM impressions
        WHERE
            clicks.newsletter_id IS NOT NULL AND
            clicks.impression_id IS NULL AND
            clicks.newsletter_id=impressions.newsletter_id AND
            clicks.article_id=impressions.article_id AND
            clicks.newsletter_id NOT IN (
                SELECT newsletter_id
                FROM (
                    SELECT newsletter_id, article_id, COUNT(article_id) AS article_count
                    FROM impressions
                    GROUP BY newsletter_id, article_id
                    ORDER BY article_count DESC) AS duplicates
                WHERE article_count>1
            );
        """
    )

def downgrade() -> None:
    pass
