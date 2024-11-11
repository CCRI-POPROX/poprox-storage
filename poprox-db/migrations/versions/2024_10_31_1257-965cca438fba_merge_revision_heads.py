"""merge revision heads

Revision ID: 965cca438fba
Revises: 0f5739c4d79d, 9bd2ccb216a6
Create Date: 2024-10-31 12:57:11.613829

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "965cca438fba"
down_revision: Union[str, None] = ("0f5739c4d79d", "9bd2ccb216a6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
