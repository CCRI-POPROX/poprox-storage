"""add treatment id to newsletters table

Revision ID: f7953f878964
Revises: 3f0cdf3794d7
Create Date: 2024-09-11 15:24:28.548749

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7953f878964"
down_revision: Union[str, None] = "3f0cdf3794d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "newsletters",
        sa.Column("treatment_id", sa.UUID(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("newsletters", "treatment_id")
