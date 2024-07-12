"""add consent log for tracking consent at onboarding

Revision ID: 185dacfa54c0
Revises: ddf8de4a8fa5
Create Date: 2024-06-14 11:17:07.191039

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "185dacfa54c0"
down_revision: Union[str, None] = "ddf8de4a8fa5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_consent_log",
        sa.Column(
            "account_consent_log_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        # The purpose of this field is twofold. First, it lets us track
        # different _versions_ of our consent documents. Secondly, it
        # lets this table be used for other consent documents (than a poprox-wide one) in the
        sa.Column("document_name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_account_consent_log_accounts_account_id",
        "account_consent_log",
        "accounts",
        ["account_id"],
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_account_consent_log_accounts_account_id",
        "account_consent_log",
        type_="foreignkey",
    )
    op.drop_table("account_consent_log")
