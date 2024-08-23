"""rename article headline and subhead

Revision ID: dd50d8e7777e
Revises: db45222a34e2
Create Date: 2024-08-21 14:18:35.334126

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd50d8e7777e"
down_revision: Union[str, None] = "db45222a34e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("articles", "title", new_column_name="headline")
    op.alter_column("articles", "content", new_column_name="subhead")


def downgrade() -> None:
    op.alter_column("articles", "headline", new_column_name="title")
    op.alter_column("articles", "subhead", new_column_name="content")
