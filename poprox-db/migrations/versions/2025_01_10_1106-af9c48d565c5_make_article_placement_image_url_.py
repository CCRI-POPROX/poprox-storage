"""make article placement image_url nullable

Revision ID: af9c48d565c5
Revises: bc86d0a8b32f
Create Date: 2025-01-10 11:06:57.658856

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af9c48d565c5"
down_revision: Union[str, None] = "bc86d0a8b32f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("article_placements", "image_url", nullable=True)


def downgrade() -> None:
    op.alter_column("article_placements", "image_url", nullable=False)
