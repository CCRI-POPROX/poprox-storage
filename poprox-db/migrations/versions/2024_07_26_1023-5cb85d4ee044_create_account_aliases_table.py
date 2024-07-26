"""create account aliases table

Revision ID: 5cb85d4ee044
Revises: 653b309492ae
Create Date: 2024-07-26 10:23:16.288178

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5cb85d4ee044"
down_revision: Union[str, None] = "653b309492ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_aliases",
        sa.Column(
            "alias_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("dataset_id", sa.UUID, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_account_aliases_account_id",
        "account_aliases",
        "accounts",
        ["account_id"],
        ["account_id"],
    )

    op.create_foreign_key(
        "fk_account_aliases_dataset_id",
        "account_aliases",
        "datasets",
        ["dataset_id"],
        ["dataset_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_account_aliases_dataset_id", "account_aliases", type_="foreignkey")
    op.drop_constraint("fk_account_aliases_account_id", "account_aliases", type_="foreignkey")
    op.drop_table("account_aliases")
