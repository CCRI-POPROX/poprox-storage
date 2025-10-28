"""Create top story packages table

Revision ID: e4bed855bbf8
Revises: 3a40fabe9845
Create Date: 2025-10-28 09:09:04.854047

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4bed855bbf8'
down_revision: Union[str, None] = '3a40fabe9845'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new table and link it to the entities table
    op.create_table(
        "top_story_packages",
        sa.Column("package_id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("entity_id", sa.UUID, nullable=True),
        sa.Column("as_of", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_top_story_packages_entity_id",
        "top_story_packages",
        "entities",
        ["entity_id"],
        ["entity_id"],
    )

    # Drop constraints and columns from the top_stories table
    op.drop_constraint("uq_top_stories_topic", "top_stories")
    op.drop_constraint("uq_top_stories_position", "top_stories")
    op.drop_constraint("fk_top_stories_entity_id", "top_stories", type_="foreignkey")

    op.drop_column("top_stories", "entity_id")
    op.drop_column("top_stories", "as_of")

    # Link the top_stories table to the top_story_packages table
    op.add_column("top_stories", sa.Column("package_id", sa.UUID, nullable=False))
    op.create_foreign_key(
        "fk_top_stories_package_id",
        "top_stories",
        "top_story_packages",
        ["package_id"],
        ["package_id"],
    )

    # Adjust the check constraints on the top_stories table to use package_id
    op.create_unique_constraint("uq_top_stories_position", "top_stories", ("package_id", "position"))
    op.create_unique_constraint("uq_top_stories_article_id", "top_stories", ("package_id", "article_id"))



def downgrade() -> None:
    # Drop the adjusted check constraints
    op.drop_constraint("uq_top_stories_position", "top_stories")
    op.drop_constraint("uq_top_stories_article_id", "top_stories")


    # Unlink top_stories with top_story_packages
    op.drop_constraint("fk_top_stories_package_id", "top_stories", type_="foreignkey")
    op.drop_column("top_stories", "package_id")


    # Re-add columns and constraints to top_stories table
    op.add_column("top_stories", sa.Column("entity_id", sa.UUID, nullable=True))
    op.add_column("top_stories", sa.Column("as_of", sa.DateTime, nullable=False))

    op.create_foreign_key(
        "fk_top_stories_entity_id",
        "top_stories",
        "entities",
        ["entity_id"],
        ["entity_id"],
    )

    # Each position can only have one article per topic (entity)
    op.create_unique_constraint("uq_top_stories_position", "top_stories", ("entity_id", "position", "as_of"))

    # Each article can only have one position per topic (entity)
    op.create_unique_constraint("uq_top_stories_topic", "top_stories", ("entity_id", "article_id", "as_of"))


    # Drop the foreign key and top_story_packages table
    op.drop_constraint("fk_top_story_packages_entity_id", "top_story_packages", type_="foreignkey")
    op.drop_table("top_story_packages")
