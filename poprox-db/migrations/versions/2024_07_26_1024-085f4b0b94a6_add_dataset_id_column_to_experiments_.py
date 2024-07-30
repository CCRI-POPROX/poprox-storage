"""add dataset id column to experiments table

Revision ID: 085f4b0b94a6
Revises: 5cb85d4ee044
Create Date: 2024-07-26 10:24:45.561122

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "085f4b0b94a6"
down_revision: Union[str, None] = "5cb85d4ee044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "experiments",
        sa.Column("dataset_id", sa.UUID, nullable=True),
    )

    op.create_foreign_key(
        "fk_experiments_dataset_id",
        "experiments",
        "datasets",
        ["dataset_id"],
        ["dataset_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_experiments_dataset_id", "experiments", type_="foreignkey")
    op.drop_column("experiments", "dataset_id")
