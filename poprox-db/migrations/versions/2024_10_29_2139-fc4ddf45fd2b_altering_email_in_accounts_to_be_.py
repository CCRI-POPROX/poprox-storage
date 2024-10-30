"""altering email in accounts to be nullable

Revision ID: fc4ddf45fd2b
Revises: f15365e37756
Create Date: 2024-10-29 21:39:35.816185

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fc4ddf45fd2b"
down_revision: Union[str, None] = "f15365e37756"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("accounts", "email", nullable=True)


def downgrade() -> None:
    op.alter_column("accounts", "email", nullable=False)
