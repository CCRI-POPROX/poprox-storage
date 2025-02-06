"""empty message

Revision ID: a67fedcb0af0
Revises: 208ffb554df8, 316ffc744a8b
Create Date: 2025-02-06 13:38:37.146146

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a67fedcb0af0"
down_revision: Union[str, None] = ("208ffb554df8", "316ffc744a8b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
