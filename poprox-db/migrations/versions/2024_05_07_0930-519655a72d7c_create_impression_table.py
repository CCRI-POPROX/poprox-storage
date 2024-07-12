"""create impression table

Revision ID: 519655a72d7c
Revises: 6502e43e4cf6
Create Date: 2024-05-07 09:30:20.103281

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "519655a72d7c"
down_revision: Union[str, None] = "6502e43e4cf6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Impression log table
# newsletter_id: UUID (foreign key)
# article_id: UUID (foreign key)
# created_at: timestamp
def upgrade() -> None:
    op.create_table(
        "impression",
        sa.Column("newsletter_id", sa.UUID, nullable=False),
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_unique_constraint("uq_newsletter_position", "impression", ("newsletter_id", "position"))

    op.create_check_constraint("ch_position_positive", "impression", sa.sql.column("position") > 0)

    op.create_foreign_key(
        "fk_impression_newsletter",
        "impression",
        "newsletter",
        ["newsletter_id"],
        ["newsletter_id"],
    )

    op.create_foreign_key(
        "fk_impression_article",
        "impression",
        "article",
        ["article_id"],
        ["article_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_newsletter_position", "impression")
    op.drop_constraint("ch_position_positive", "impression")
    op.drop_constraint("fk_impression_newsletter", "impression", type_="foreignkey")
    op.drop_constraint("fk_impression_article", "impression", type_="foreignkey")
    op.drop_table("impression")
