"""change primary key on article_placements table

Revision ID: 58deb24f5008
Revises: af9c48d565c5
Create Date: 2025-01-10 11:19:21.401633

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "58deb24f5008"
down_revision: Union[str, None] = "af9c48d565c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove foreign key and primary key constraints on article_id column
    op.drop_constraint(
        "fk_articles_placements_articles",
        "article_placements",
        type_="foreignkey",
    )
    op.drop_constraint("article_placements_pkey", "article_placements", type_="primary")

    # Add a new column to be the primary key
    op.add_column(
        "article_placements",
        sa.Column(
            "placement_id",
            sa.UUID,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )

    # Add primary key constraints on placement_id column
    op.create_primary_key(
        "article_placements_pkey",
        "article_placements",
        [
            "placement_id",
        ],
    )

    # Recreate foreign key constraint on article_id column
    op.create_foreign_key(
        "fk_articles_placements_articles", "article_placements", "articles", ["article_id"], ["article_id"]
    )


def downgrade() -> None:
    # Drop the new primary key column
    op.drop_column("article_placements", "placement_id")

    # Recreate the old primary and foreign key constraints
    op.create_primary_key(
        "article_placements_pkey",
        "article_placements",
        [
            "article_id",
        ],
    )
