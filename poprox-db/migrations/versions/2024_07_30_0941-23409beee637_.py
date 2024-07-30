"""empty message

Revision ID: 23409beee637
Revises: f5973e9cf00f, e63a0a91de19
Create Date: 2024-07-30 09:41:03.765588

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "23409beee637"
down_revision: Union[str, None] = ("f5973e9cf00f", "e63a0a91de19")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
