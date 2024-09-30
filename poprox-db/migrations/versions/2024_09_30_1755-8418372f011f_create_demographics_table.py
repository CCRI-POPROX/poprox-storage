"""create_demographics_table

Revision ID: 8418372f011f
Revises: f7953f878964
Create Date: 2024-09-30 17:55:31.059281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8418372f011f'
down_revision: Union[str, None] = 'f7953f878964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demographics",
        sa.Column(
            "demographic_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", sa.UUID, nullable=False),
        sa.Column("gender", sa.String(50), nullable=False),
        sa.Column("birth_year", sa.Integer, nullable=False),
        sa.Column("zip5", sa.String(5), nullable=False),
        sa.Column("education", sa.String(50), nullable=False),
        sa.Column("race", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_demographics_account_id",
        "demographics",
        "accounts",
        ["account_id"],
        ["account_id"],
    )
    op.create_unique_constraint("uq_demographics", "demographics", ("account_id", "demographic_id"))


def downgrade() -> None:
    op.drop_constraint("uq_demographics", "demographics")
    op.drop_constraint("fk_demographics_account_id", "demographics", type_="foreignkey")
    op.drop_table("demographics")
