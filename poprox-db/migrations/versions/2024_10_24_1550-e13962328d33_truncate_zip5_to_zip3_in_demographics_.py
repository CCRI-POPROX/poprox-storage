"""truncate zip5 to zip3 in demographics table

Revision ID: e13962328d33
Revises: 9370e559b657
Create Date: 2024-10-24 15:50:59.650029

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e13962328d33'
down_revision: Union[str, None] = '9370e559b657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'demographics',
        'zip5',
        new_column_name='zip3',
        existing_type=sa.String(length=5),
        type_=sa.String(length=3),
        postgresql_using='substring(zip5 from 1 for 3)'
    )


def downgrade() -> None:
    op.alter_column(
        'demographics',
        'zip3',
        new_column_name='zip5',
        existing_type=sa.String(length=3),
        type_=sa.String(length=5),
        postgresql_using='zip3 || \'000\''
    )
