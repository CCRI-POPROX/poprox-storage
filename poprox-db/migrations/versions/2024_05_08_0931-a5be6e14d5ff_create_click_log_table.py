"""create click table

Revision ID: a5be6e14d5ff
Revises: 519655a72d7c
Create Date: 2024-05-08 09:31:02.263478

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5be6e14d5ff"
down_revision: Union[str, None] = "519655a72d7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Click table
# click_id: int (primary)
# account_id: UUID (foreign key)
# newsletter_id: UUID (foreign key) <- the specific newsletter they clicked on
# article_id: UUID (foreign key)
# created_at: timestamp
def upgrade() -> None:
    op.create_table(
        "click",
        sa.Column(
            "click_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("newsletter_id", sa.UUID),
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_click_account",
        "click",
        "account",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_click_newsletter",
        "click",
        "newsletter",
        ["newsletter_id"],
        ["newsletter_id"],
    )

    op.create_foreign_key(
        "fk_click_article",
        "click",
        "article",
        ["article_id"],
        ["article_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_click_account", "click", type_="foreignkey")
    op.drop_constraint("fk_click_newsletter", "click", type_="foreignkey")
    op.drop_constraint("fk_click_article", "click", type_="foreignkey")
    op.drop_table("click")
