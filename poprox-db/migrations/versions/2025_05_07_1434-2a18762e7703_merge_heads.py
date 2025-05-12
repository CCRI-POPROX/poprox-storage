"""merge heads

Revision ID: 2a18762e7703
Revises: 748a261a6d57, 4baca0cff3b8
Create Date: 2025-05-07 14:34:20.184640

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '2a18762e7703'
down_revision: Union[str, None] = ('748a261a6d57', '4baca0cff3b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
