"""create scraped_articles table

Revision ID: 4fc4a6030444
Revises: 23409beee637
Create Date: 2024-08-21 16:39:29.883880

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4fc4a6030444'
down_revision: Union[str, None] = '23409beee637'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Scraped articles table
# title: str
# description: str
# url: str, primary key
# section: str
# level: str
# image_url: str
# scraped_at: timestamp
def upgrade() -> None:
    op.create_table(
        "scraped_articles",
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.String),
        sa.Column("url", sa.String, primary_key=True),
        sa.Column("section", sa.String),
        sa.Column("level", sa.String),
        sa.Column("image_url", sa.String),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    # Drop the table if it exists
    op.drop_table("scraped_articles")
