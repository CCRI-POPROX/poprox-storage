"""pluralize table names

Revision ID: 12db57e34931
Revises: 8c2b0c4c3ae5
Create Date: 2024-05-16 08:33:51.827319

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12db57e34931"
down_revision: str | None = "8c2b0c4c3ae5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.rename_table("account", "accounts")
    op.rename_table("article", "articles")
    op.rename_table("newsletter", "newsletters")
    op.rename_table("impression", "impressions")
    op.rename_table("click", "clicks")


def downgrade():
    op.rename_table("clicks", "click")
    op.rename_table("impressions", "impression")
    op.rename_table("newsletters", "newsletter")
    op.rename_table("articles", "article")
    op.rename_table("accounts", "account")
