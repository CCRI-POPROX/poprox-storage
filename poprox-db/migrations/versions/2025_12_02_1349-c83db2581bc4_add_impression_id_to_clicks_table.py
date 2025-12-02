"""Add impression id to clicks table

Revision ID: c83db2581bc4
Revises: 7b9d2e5cab5d
Create Date: 2025-12-02 13:49:54.583565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83db2581bc4'
down_revision: Union[str, None] = '7b9d2e5cab5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clicks",
        sa.Column("impression_id", sa.UUID(), nullable=True),
    )

    op.create_foreign_key(
        "fk_clicks_impression_id",
        "clicks",
        "impressions",
        ["impression_id"],
        ["impression_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_clicks_impression_id", "clicks", type_="foreignkey")
    op.drop_column("clicks", "impression_id")
