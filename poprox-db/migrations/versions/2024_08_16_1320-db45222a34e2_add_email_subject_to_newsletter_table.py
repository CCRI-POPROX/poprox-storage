"""add email_subject to newsletter table

Revision ID: db45222a34e2
Revises: 23409beee637
Create Date: 2024-08-16 13:20:27.673943

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db45222a34e2"
down_revision: Union[str, None] = "23409beee637"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "newsletters",
        sa.Column("email_subject", sa.String, nullable=True),
    )
    op.execute(
        """
        update newsletters set email_subject='Just something to read daily' where email_subject is null;
        """
    )

    op.alter_column("newsletters", "email_subject", nullable=False)


def downgrade() -> None:
    op.drop_column("newsletters", "email_subject")
