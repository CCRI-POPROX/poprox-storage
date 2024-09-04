"""remove name column from datasets table

Revision ID: 8bf414e0ddfb
Revises: dd50d8e7777e
Create Date: 2024-09-04 11:25:43.062068

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8bf414e0ddfb"
down_revision: Union[str, None] = "dd50d8e7777e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("datasets", "dataset_name")


def downgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column("dataset_name", sa.String),
    )
