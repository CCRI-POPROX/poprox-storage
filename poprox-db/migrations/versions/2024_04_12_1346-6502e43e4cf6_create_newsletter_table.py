"""create newsletter table

Revision ID: 6502e43e4cf6
Revises: 1496108a1b16
Create Date: 2024-04-12 13:46:34.347668

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6502e43e4cf6"
down_revision: Union[str, None] = "1496108a1b16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Newsletter log table
# newsletter_id: UUID
# account_id: UUID (foreign key)
# content: JSONB
# html: str
# created_at: timestamp
def upgrade() -> None:
    op.create_table(
        "newsletter",
        sa.Column(
            "newsletter_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("content", sa.dialects.postgresql.JSONB),
        sa.Column("html", sa.String, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")
        ),
    )

    op.create_foreign_key(
        "fk_newsletter_account",
        "newsletter",
        "account",
        ["account_id"],
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_newsletter_account", "newsletter", type_="foreignkey")
    op.drop_table("newsletter")
