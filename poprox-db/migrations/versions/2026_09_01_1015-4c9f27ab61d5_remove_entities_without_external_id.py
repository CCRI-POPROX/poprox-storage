"""remove entities without an external id

AP sometimes returns entities without a code. Because PostgreSQL treats NULLs as
distinct in the unique constraint, these entities were duplicated across articles.

The AP parser now skips uncoded entities. This migration removes previously ingested
uncoded entities, their mentions, and their test-account interests, while preserving
entities referenced by article packages.

Revision ID: 4c9f27ab61d5
Revises: 62b01cd7d748
Create Date: 2026-09-01 10:15:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c9f27ab61d5"
down_revision: Union[str, None] = "62b01cd7d748"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove mentions of uncoded entities
    op.execute(
        """
        DELETE FROM mentions
        WHERE entity_id IN (
            SELECT entity_id FROM entities WHERE external_id IS NULL
        );
        """
    )

    # Remove interests in uncoded entities
    op.execute(
        """
        DELETE FROM account_interest_log
        WHERE entity_id IN (
            SELECT entity_id FROM entities WHERE external_id IS NULL
        );
        """
    )

    # Remove uncoded entities not used by packages
    op.execute(
        """
        DELETE FROM entities
        WHERE
            external_id IS NULL AND
            entity_id NOT IN (SELECT entity_id FROM article_packages WHERE entity_id IS NOT NULL);
        """
    )


def downgrade() -> None:
    pass
