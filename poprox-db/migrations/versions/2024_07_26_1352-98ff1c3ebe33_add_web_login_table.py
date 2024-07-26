"""add web_login table

Revision ID: 98ff1c3ebe33
Revises: 211c6b3ac5de
Create Date: 2024-07-26 13:52:10.169410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "98ff1c3ebe33"
down_revision: Union[str, None] = "211c6b3ac5de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "web_logins",
        sa.Column(
            "web_login_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("newsletter_id", sa.UUID, nullable=True),
        sa.Column("endpoint", sa.String, nullable=False),
        sa.Column("data", JSONB, nullable=False),  # not raw_data -- only contains extra url parameters.
    )

    op.create_foreign_key(
        "fk_web_logins_accounts_account_id",
        "web_logins",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_web_logins_newsletters_newsletter_id",
        "web_logins",
        "newsletters",
        ["newsletter_id"],
        ["newsletter_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_web_logins_accounts_account_id",
        "web_logins",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_web_logins_newsletters_newsletter_id",
        "web_logins",
        type_="foreignkey",
    )

    op.drop_table("web_logins")
