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
    # Remove duplicate mentions

    # When there are two mentions on the same article linked to different entities
    # where the mentions and entities together only differ by entity_type
    # then delete the `topic` one
    op.execute(
        """
        DELETE FROM mentions
        WHERE mention_id IN (
            SELECT topic_mention_id FROM (
                SELECT mentions.mention_id AS topic_mention_id, mentions.article_id, mentions.source, entities.external_id, entities.name
                FROM mentions JOIN entities ON mentions.entity_id=entities.entity_id WHERE entity_type='topic'
            ) t JOIN (
                SELECT mentions.mention_id AS subject_mention_id, mentions.article_id, mentions.source, entities.external_id, entities.name
                FROM mentions JOIN entities ON mentions.entity_id=entities.entity_id WHERE entity_type='subject'
            ) s ON t.article_id=s.article_id AND t.source=s.source AND t.external_id=s.external_id AND t.name=s.name
        );
        """
    )

    # Update remaining mentions to point at entities with type `subject`
    op.execute(
        """
        UPDATE mentions
        SET entity_id = mapping.subject_entity_id
        FROM (
            SELECT topic_entity_id, subject_entity_id FROM (
                SELECT entity_id AS topic_entity_id, external_id FROM entities WHERE entity_type='topic'
            ) t JOIN (
                SELECT entity_id AS subject_entity_id, external_id FROM entities WHERE entity_type='subject'
            ) s ON t.external_id=s.external_id
        ) mapping
        WHERE mentions.entity_id=topic_entity_id
        """
    )

    # Remove duplicate entities with type `topic`, leaving the non-dupes alone
    op.execute(
        """
        DELETE FROM entities
        WHERE entity_type='topic'
        AND external_id IN (
            SELECT external_id FROM entities WHERE entity_type = 'subject'
        )
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
