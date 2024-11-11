"""merge head revisions

Revision ID: f8667df4b049
Revises: 0f5739c4d79d, 9bd2ccb216a6
Create Date: 2024-10-29 14:06:37.323505

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8667df4b049'
down_revision: Union[str, None] = ('0f5739c4d79d', '9bd2ccb216a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
