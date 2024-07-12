"""create subscription table

Revision ID: 5111c14454e5
Revises: adb103cc5e10
Create Date: 2024-06-03 12:24:19.591428

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5111c14454e5"
down_revision: Union[str, None] = "adb103cc5e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column(
            "subscription_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("started", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("ended", sa.DateTime, nullable=True, server_default=sa.null()),
    )

    op.create_foreign_key(
        "fk_subscriptions_account_id",
        "subscriptions",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.execute("insert into subscriptions (account_id) select account_id from accounts;")


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_account_id", "subscriptions", type_="foreignkey")

    op.drop_table("subscriptions")
