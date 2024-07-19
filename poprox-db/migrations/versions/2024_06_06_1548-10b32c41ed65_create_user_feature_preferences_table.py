"""create user_feature_preferences table

Revision ID: 10b32c41ed65
Revises: 5111c14454e5
Create Date: 2024-06-06 15:48:16.165974

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "10b32c41ed65"
down_revision: str | None = "5111c14454e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_interest_log",
        sa.Column(
            "account_interest_log_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("entity_id", sa.UUID, nullable=False),
        sa.Column("preference", sa.SmallInteger, nullable=True),
        sa.Column("frequency", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_account_interest_log_accounts_account_id",
        "account_interest_log",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_account_interest_log_accounts_entity_id",
        "account_interest_log",
        "entities",
        ["entity_id"],
        ["entity_id"],
    )

    # DISTINCT ON formally specifies that it returns the first row for each
    # unique value of the keys it is distinct on. Since this is distinct on
    # account and entity, it will return unique rows by account and entity.
    # The chosen row would be determined by the order by statement which
    # guarantees the first row for each account,entity pair is the most
    # recently created one.

    op.execute(
        """
        CREATE VIEW account_current_interest_view as
        SELECT DISTINCT ON (account_id, entity_id) *
        FROM account_interest_log
        ORDER BY account_id, entity_id, created_at DESC;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW account_current_interest_view;")

    op.drop_constraint(
        "fk_account_interest_log_accounts_account_id",
        "account_interest_log",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_account_interest_log_accounts_entity_id",
        "account_interest_log",
        type_="foreignkey",
    )
    op.drop_table("account_interest_log")
