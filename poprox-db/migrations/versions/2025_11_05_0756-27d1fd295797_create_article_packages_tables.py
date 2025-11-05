"""create article packages tables

Revision ID: 27d1fd295797
Revises: 95080bdb0b0d
Create Date: 2025-11-05 07:56:46.208063

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '27d1fd295797'
down_revision: Union[str, None] = '95080bdb0b0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("package_id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("entity_id", sa.UUID, nullable=True),
        sa.Column("current_as_of", sa.DateTime, nullable=True, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    # There can only be one package per source and entity that's current at a given time
    op.create_unique_constraint(
        "uq_packages",
        "packages",
        ("source", "entity_id", "current_as_of")
    )

    # Link to entities table
    op.create_foreign_key(
        "fk_packages_entity_id",
        "packages",
        "entities",
        ["entity_id"],
        ["entity_id"],
    )

    # Create table to track the articles in each package
    op.create_table(
        "package_contents",
        sa.Column("package_id", sa.UUID, nullable=False),
        sa.Column("article_id", sa.UUID, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
    )

    # Link to packages table
    op.create_foreign_key(
        "fk_packages_package_id",
        "package_contents",
        "packages",
        ["package_id"],
        ["package_id"],
    )

    # Link to articles table
    op.create_foreign_key(
        "fk_packages_article_id",
        "package_contents",
        "articles",
        ["article_id"],
        ["article_id"],
    )

    # Each package can only have one article per position
    op.create_unique_constraint(
        "uq_package_contents_position",
        "package_contents",
        ("package_id", "position")
    )

    # Positions must be positive
    op.create_check_constraint(
        "ch_package_contents_position_positive",
        "package_contents",
        sa.sql.column("position") > 0
    )


def downgrade() -> None:
    op.drop_constraint("ch_package_contents_position_positive", "package_contents")
    op.drop_constraint("uq_package_contents_position", "package_contents")
    op.drop_constraint("fk_packages_article_id", "package_contents", type_="foreignkey")
    op.drop_constraint("fk_packages_package_id", "package_contents", type_="foreignkey")
    op.drop_table("package_contents")

    op.drop_constraint("fk_packages_entity_id", "packages", type_="foreignkey")
    op.drop_table("packages")
