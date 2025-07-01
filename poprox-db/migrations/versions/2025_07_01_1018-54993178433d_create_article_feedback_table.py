"""Create article feedback table

Revision ID: 54993178433d
Revises: 72901f4ab61c
Create Date: 2025-07-01 10:18:44.057202

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '54993178433d'
down_revision: Union[str, None] = '72901f4ab61c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_feedback",
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("feedback", sa.String(15), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    # Link the new table to existing tables
    op.create_foreign_key(
        "fk_article_feedback_account_id",
        "article_feedback",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_article_feedback_article_id",
        "article_feedback",
        "articles",
        ["article_id"],
        ["article_id"],
    )

    # TODO: Migrate feedback from impressions table


    # Drop feedback column from impressions table
    op.drop_column("impressions", "feedback")

def downgrade() -> None:
    # Add the feedback column back to the impressions table
    op.add_column("impressions", sa.Column("feedback", sa.String(15), nullable=True))

    # TODO: Migrate feedback back to the impressions table

    # Drop the foreign keys
    op.drop_constraint("fk_article_feedback_account_id", "article_feedback", type_="foreignkey")
    op.drop_constraint("fk_article_feedback_article_id", "article_feedback", type_="foreignkey")

    # Drop the table
    op.drop_table("article_feedback")
