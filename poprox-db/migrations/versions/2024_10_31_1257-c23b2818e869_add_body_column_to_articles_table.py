"""Add body column to articles table

Revision ID: c23b2818e869
Revises: 965cca438fba
Create Date: 2024-10-31 12:57:14.134248

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c23b2818e869"
down_revision: Union[str, None] = "965cca438fba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("body", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "body")
