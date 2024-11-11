"""merge revision heads

Revision ID: 4f7e5bc8ac02
Revises: 7d9f1a1c4274, 28a548d5f2f8
Create Date: 2024-11-06 09:23:13.043862

"""
from typing import Sequence, Union

# import sqlalchemy as sa
# from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4f7e5bc8ac02'
down_revision: Union[str, None] = ('7d9f1a1c4274', '28a548d5f2f8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
