"""record recommender pipeline info

Revision ID: bad8a290077a
Revises: b5e32d031a20
Create Date: 2025-03-27 08:46:47.702293

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bad8a290077a"
down_revision: Union[str, None] = "b5e32d031a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("newsletters", sa.Column("recommender_name", sa.String(), nullable=True))
    op.add_column("newsletters", sa.Column("recommender_version", sa.String(), nullable=True))
    op.add_column("newsletters", sa.Column("recommender_hash", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("newsletters", "recommender_name")
    op.drop_column("newsletters", "recommender_version")
    op.drop_column("newsletters", "recommender_hash")
