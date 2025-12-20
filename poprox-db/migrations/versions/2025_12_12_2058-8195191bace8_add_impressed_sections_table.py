"""add impressed_sections table

Revision ID: 8195191bace8
Revises: d737977ed772
Create Date: 2025-12-12 20:58:13.727086

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8195191bace8"
down_revision: Union[str, None] = "d737977ed772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "section_types",
        sa.Column(
            "section_type_id", sa.UUID, primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("flavor", sa.String, nullable=True),
        sa.Column("seed", sa.UUID, nullable=True),
        sa.Column("personalized", sa.Boolean, nullable=False),
        sa.Column("title", sa.String, nullable=True),
    )

    op.create_unique_constraint("uq_section_types", "section_types", ("flavor", "seed", "personalized", "title"))

    op.create_table(
        "impressed_sections",
        sa.Column("section_id", sa.UUID, primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("section_type_id", sa.UUID, nullable=False),
        sa.Column("newsletter_id", sa.UUID, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
    )

    # Link to section_type table
    op.create_foreign_key(
        "fk_impressed_section_section_type_id",
        "impressed_sections",
        "section_types",
        ["section_type_id"],
        ["section_type_id"],
    )

    # Link to newsletter table
    op.create_foreign_key(
        "fk_impressed_section_newsletter_id",
        "impressed_sections",
        "newsletters",
        ["newsletter_id"],
        ["newsletter_id"],
    )

    # Each newsletter can only have one section per position
    op.create_unique_constraint("uq_impressed_sections_position", "impressed_sections", ("newsletter_id", "position"))

    # Positions must be positive
    op.create_check_constraint(
        "ch_impressed_sections_position_positive", "impressed_sections", sa.sql.column("position") > 0
    )


def downgrade() -> None:
    op.drop_constraint("ch_impressed_sections_position_positive", "impressed_sections")
    op.drop_constraint("uq_impressed_sections_position", "impressed_sections")
    op.drop_constraint("fk_impressed_section_newsletter_id", "impressed_sections", type_="foreignkey")
    op.drop_constraint("fk_impressed_section_section_type_id", "impressed_sections", type_="foreignkey")

    op.drop_table("impressed_sections")
    op.drop_table("section_types")
