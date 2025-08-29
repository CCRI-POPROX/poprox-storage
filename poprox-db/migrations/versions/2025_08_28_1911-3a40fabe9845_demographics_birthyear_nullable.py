"""demographics birthyear nullable

Revision ID: 3a40fabe9845
Revises: 9cfcaaca0bca
Create Date: 2025-08-28 19:11:02.569603

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3a40fabe9845'
down_revision: Union[str, None] = '9cfcaaca0bca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("demographics", "birth_year",
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column("demographics", "birth_year",
        existing_type=sa.Integer(),
        nullable=False
    )
