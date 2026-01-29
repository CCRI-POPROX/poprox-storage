"""update charitable donation option

Revision ID: 8f61da0a457c
Revises: 97cd9a356543, 09cbc17db531
Create Date: 2026-01-29 17:27:42.061269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f61da0a457c'
down_revision: Union[str, None] = ('97cd9a356543', '09cbc17db531')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE accounts SET compensation = 'Feeding America'
        WHERE compensation = 'American Red Cross'
        OR compensation = 'American Cancer Society'
        OR compensation = 'Boys & Girls Club of America'
        """
    )


def downgrade() -> None:
    # No possible downgrade for this migration
    pass
