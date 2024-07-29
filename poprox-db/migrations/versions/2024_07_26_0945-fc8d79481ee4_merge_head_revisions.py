"""merge head revisions

Revision ID: fc8d79481ee4
Revises: 14be38931ae0, 5d566fff8aaa
Create Date: 2024-07-26 09:45:33.246538

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "fc8d79481ee4"
down_revision: Union[str, None] = ("14be38931ae0", "5d566fff8aaa")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
