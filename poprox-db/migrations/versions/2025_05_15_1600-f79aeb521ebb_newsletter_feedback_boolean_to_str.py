"""newsletter feedback boolean to str

Revision ID: f79aeb521ebb
Revises: 45d10f860ff6
Create Date: 2025-05-15 16:00:51.469320

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f79aeb521ebb'
down_revision: Union[str, None] = '45d10f860ff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "newsletters",
        "feedback",
        type_=sa.String(15),
        existing_type=sa.BOOLEAN,
        existing_nullable=True
    ),


def downgrade() -> None:
    op.alter_column(
        'newsletters',
        'feedback',
        existing_type=sa.String(15),
        type_=sa.BOOLEAN,
        existing_nullable=True
    )
