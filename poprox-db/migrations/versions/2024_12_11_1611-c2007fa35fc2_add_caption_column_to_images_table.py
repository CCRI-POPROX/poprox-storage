"""add caption column to images table

Revision ID: c2007fa35fc2
Revises: 03883e546c24
Create Date: 2024-12-11 16:11:30.234857

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c2007fa35fc2'
down_revision: Union[str, None] = '03883e546c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("images", sa.Column("caption", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("images", "caption")
