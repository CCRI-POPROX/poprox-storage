"""increase string length for race field on demographics table

Revision ID: 9370e559b657
Revises: 8418372f011f
Create Date: 2024-10-01 00:07:24.898408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9370e559b657'
down_revision: Union[str, None] = '8418372f011f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "demographics",
        "race",
        type_=sa.String(200),
        existing_type=sa.String(50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "demographics",
        "race",
        type_=sa.String(50),
        existing_type=sa.String(200),
        existing_nullable=False,
    )
