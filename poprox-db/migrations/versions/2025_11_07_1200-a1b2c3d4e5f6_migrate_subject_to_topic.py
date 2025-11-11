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
    # Update mentions to point at entities with type `subject`
    op.execute(
        """
        UPDATE mentions
        SET entity_id = mapping.target_entity_id
        FROM (
            SELECT source_entity_id, target_entity_id FROM (
                SELECT entity_id AS source_entity_id, external_id FROM entities WHERE entity_type='topic'
            ) s JOIN (
                SELECT entity_id AS target_entity_id, external_id FROM entities WHERE entity_type='subject'
            ) t ON s.external_id=t.external_id;
        ) mapping
        WHERE mentions.entity_id=source_entity_id
        """
    )

    # Remove entities with type `topic`
    op.execute(
        """
        DELETE FROM entities
        WHERE entity_type='topic'
        """
    )

    # Update entities from type `subject` to `topic`
    op.execute(
        """
        UPDATE entities
        SET entity_type='topic'
        WHERE entity_type='subject'
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
