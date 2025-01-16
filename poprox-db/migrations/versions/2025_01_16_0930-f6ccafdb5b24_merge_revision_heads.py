"""merge revision heads

Revision ID: f6ccafdb5b24
Revises: adf30c8ce87e, 58deb24f5008
Create Date: 2025-01-16 09:30:17.947408

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6ccafdb5b24"
down_revision: Union[str, None] = ("adf30c8ce87e", "58deb24f5008")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
