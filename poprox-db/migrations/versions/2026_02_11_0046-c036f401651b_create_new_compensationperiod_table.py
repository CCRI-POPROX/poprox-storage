"""create new CompensationPeriod table

Revision ID: c036f401651b
Revises: 9aab06f29f2e
Create Date: 2026-02-11 00:46:31.391186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c036f401651b'
down_revision: Union[str, None] = '9aab06f29f2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'compensation_periods',
        sa.Column('compensation_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('compensation_id')
    )


def downgrade() -> None:
    op.drop_table('compensation_periods')
