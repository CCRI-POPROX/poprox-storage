"""merge heads

Revision ID: 81af2711e062
Revises: 6cb50b5e9d44, c83db2581bc4
Create Date: 2025-12-09 10:15:06.432455

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '81af2711e062'
down_revision: Union[str, None] = ('6cb50b5e9d44', 'c83db2581bc4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
