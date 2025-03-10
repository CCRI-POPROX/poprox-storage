"""storing headline

Revision ID: b5e32d031a20
Revises: a2e9ad765d9a
Create Date: 2025-03-06 11:48:54.186740

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5e32d031a20"
down_revision: Union[str, None] = "a2e9ad765d9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("impressions", sa.Column("headline", sa.String(), nullable=True))
    op.add_column("impressions", sa.Column("subhead", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("impressions", "headline")
    op.drop_column("impressions", "subhead")
