"""empty message

Revision ID: a2e9ad765d9a
Revises: 3d17fcf49eaa, b02a1eb29fee, 6da1373105ef
Create Date: 2025-03-06 11:48:43.596314

"""

from typing import Sequence, Union

# from alembic import op
# import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a2e9ad765d9a"
down_revision: Union[str, None] = ("3d17fcf49eaa", "b02a1eb29fee", "6da1373105ef")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
