"""merge revision heads

Revision ID: 8f10a2101cb8
Revises: 0f5739c4d79d, 9bd2ccb216a6
Create Date: 2024-11-04 10:40:21.754365

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "8f10a2101cb8"
down_revision: Union[str, None] = ("0f5739c4d79d", "9bd2ccb216a6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
