"""create datasets table

Revision ID: 653b309492ae
Revises: e621ac2d0165
Create Date: 2024-07-26 10:22:11.312945

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "653b309492ae"
down_revision: Union[str, None] = "e621ac2d0165"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column(
            "dataset_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("team_id", sa.UUID, nullable=False),
        sa.Column("dataset_name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_foreign_key(
        "fk_datasets_team_id",
        "datasets",
        "teams",
        ["team_id"],
        ["team_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_datasets_team_id", "datasets", type_="foreignkey")
    op.drop_table("datasets")
