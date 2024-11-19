"""merge revision heads

Revision ID: 2f7fd221e67c
Revises: fc4ddf45fd2b, c23b2818e869, 4a67e9d1ca1e, 4f7e5bc8ac02
Create Date: 2024-11-19 09:31:14.853829

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "2f7fd221e67c"
down_revision: Union[str, None] = ("fc4ddf45fd2b", "c23b2818e869", "4a67e9d1ca1e", "4f7e5bc8ac02")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
