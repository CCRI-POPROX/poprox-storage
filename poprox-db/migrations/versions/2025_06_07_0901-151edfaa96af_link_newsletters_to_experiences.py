"""Link newsletters to experiences

Revision ID: 151edfaa96af
Revises: 87aa4d7933b2
Create Date: 2025-06-07 09:01:25.346787

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '151edfaa96af'
down_revision: Union[str, None] = '87aa4d7933b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "newsletters",
        sa.Column("experience_id", sa.UUID, nullable=True),
    )

    op.create_foreign_key(
        "fk_newsletters_experience_id",
        "newsletters",
        "experiences",
        ["experience_id"],
        ["experience_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_newsletters_experience_id", "newsletters", type_="foreignkey")
    op.drop_column("newsletters", "experience_id")
