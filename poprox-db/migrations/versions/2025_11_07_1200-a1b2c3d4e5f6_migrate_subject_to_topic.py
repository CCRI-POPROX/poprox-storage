"""Migrate entity_type from subject to topic

Revision ID: a1b2c3d4e5f6
Revises: 247dfe2d81ee
Create Date: 2025-11-07 17:55:44.456804

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '247dfe2d81ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE entities
        SET entity_type = 'topic'
        WHERE entity_type = 'subject'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE entities
        SET entity_type = 'subject'
        WHERE entity_type = 'topic'
        """
    )
