"""adding preview image

Revision ID: 3d17fcf49eaa
Revises: f6ccafdb5b24
Create Date: 2025-01-31 15:54:10.085416

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3d17fcf49eaa'
down_revision: Union[str, None] = 'f6ccafdb5b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("impressions", sa.Column("preview_image_id", sa.UUID, nullable=True))

    op.create_foreign_key(
        "fk_impressions_images",
        "impressions",
        "images",
        ["preview_image_id"],
        ["image_id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_impressions_images", "impressions", type_="foreignkey")
    op.drop_column("impressions", "preview_image_id")
