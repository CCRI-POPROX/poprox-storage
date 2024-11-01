"""merge head revisions

Revision ID: 042705b8457c
Revises: 0f5739c4d79d, 9bd2ccb216a6
Create Date: 2024-10-29 13:23:05.581347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '042705b8457c'
down_revision: Union[str, None] = ('0f5739c4d79d', '9bd2ccb216a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
