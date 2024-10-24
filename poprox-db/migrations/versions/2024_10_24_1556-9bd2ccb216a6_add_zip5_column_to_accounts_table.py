"""add zip5 column to accounts table

Revision ID: 9bd2ccb216a6
Revises: e13962328d33
Create Date: 2024-10-24 15:56:56.017787

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9bd2ccb216a6'
down_revision: Union[str, None] = 'e13962328d33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'accounts',
        sa.Column('zip5', sa.String(length=5), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('accounts', 'zip5')
