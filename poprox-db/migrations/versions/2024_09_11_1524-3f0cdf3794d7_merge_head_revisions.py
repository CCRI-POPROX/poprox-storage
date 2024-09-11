"""merge head revisions

Revision ID: 3f0cdf3794d7
Revises: 4fc4a6030444, 8bf414e0ddfb
Create Date: 2024-09-11 15:24:24.666983

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3f0cdf3794d7"
down_revision: Union[str, None] = ("4fc4a6030444", "8bf414e0ddfb")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
