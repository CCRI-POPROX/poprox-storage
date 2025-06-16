"""move templates to treatment

Revision ID: 72901f4ab61c
Revises: 356522e9ea7b
Create Date: 2025-06-16 14:21:58.040374

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "72901f4ab61c"
down_revision: Union[str, None] = "356522e9ea7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("recommenders", "template")
    # NOTE -- this is destructive as written... This collumn hasn't been use yet, so it's fine.

    op.add_column(
        "expt_treatments",
        sa.Column("template", sa.String, nullable=True),
    )
    op.add_column(
        "experiences",
        sa.Column("template", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.add_column(
        "recommenders",
        sa.Column("template", sa.String, nullable=True),
    )

    op.drop_column("expt_treatments", "template")
    op.drop_column("experiences", "template")
