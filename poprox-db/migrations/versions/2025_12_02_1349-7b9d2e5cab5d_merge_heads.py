"""merge heads

Revision ID: 7b9d2e5cab5d
Revises: 27d1fd295797, a1b2c3d4e5f6
Create Date: 2025-12-02 13:49:51.666923

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '7b9d2e5cab5d'
down_revision: Union[str, None] = ('27d1fd295797', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
