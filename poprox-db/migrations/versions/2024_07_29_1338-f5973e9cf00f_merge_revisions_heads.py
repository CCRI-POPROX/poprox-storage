"""merge revisions heads

Revision ID: f5973e9cf00f
Revises: 085f4b0b94a6, 98ff1c3ebe33
Create Date: 2024-07-29 13:38:37.108840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5973e9cf00f'
down_revision: Union[str, None] = ('085f4b0b94a6', '98ff1c3ebe33')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
