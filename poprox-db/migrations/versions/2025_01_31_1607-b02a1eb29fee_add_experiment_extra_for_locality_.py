"""add experiment_extra for locality experiment logging

Revision ID: b02a1eb29fee
Revises: f6ccafdb5b24
Create Date: 2025-01-31 16:07:04.005073

"""
from typing import Sequence, Union
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b02a1eb29fee'
down_revision: Union[str, None] = 'f6ccafdb5b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a single column of json type corresponding to the experiment_extra
    op.add_column(
        "impressions",
        sa.Column(
            "experiment_extra",
            JSONB
        ),
    )


def downgrade() -> None:
    # Drop the new primary key column
    op.drop_column("impressions", "experiment_extra")
