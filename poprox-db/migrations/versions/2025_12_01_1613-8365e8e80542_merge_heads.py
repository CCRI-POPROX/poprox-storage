"""merge heads

Revision ID: 8365e8e80542
Revises: 27d1fd295797, a1b2c3d4e5f6
Create Date: 2025-12-01 16:13:25.012181

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "8365e8e80542"
down_revision: Union[str, None] = ("27d1fd295797", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
