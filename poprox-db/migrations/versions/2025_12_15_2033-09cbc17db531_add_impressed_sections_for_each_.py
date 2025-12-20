"""add impressed_sections for each newsletter

Revision ID: 09cbc17db531
Revises: 8195191bace8
Create Date: 2025-12-15 20:33:21.976210

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "09cbc17db531"
down_revision: Union[str, None] = "8195191bace8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add impressed_section_id associate to impression table
    op.add_column(
        "impressions",
        sa.Column("impressed_section_id", sa.UUID, nullable=True, default=sa.Null),
    )

    op.create_foreign_key(
        "fk_impression_impressed_section_id",
        "impressions",
        "impressed_sections",
        ["impressed_section_id"],
        ["section_id"],
    )

    # "generic" section type UUID 7d20c0bd-57d9-4d31-916d-4d2e7e148b71

    # Create a "generic" section type
    op.execute(
        "insert into section_types (section_type_id, flavor, seed, personalized, title) "
        "values ('7d20c0bd-57d9-4d31-916d-4d2e7e148b71', 'single_section', NULL, True, NULL)"
    )

    # Create a single section for each newsletter
    op.execute(
        "insert into impressed_sections(section_type_id, newsletter_id, position) "
        "select '7d20c0bd-57d9-4d31-916d-4d2e7e148b71' as section_type_id, newsletter_id, 1 as position from newsletters "
        "where newsletter_id not in (select newsletter_id from impressed_sections)"
    )

    # Update impression table with impressed sections from past step
    op.execute(
        """
        UPDATE impressions
        SET impressed_section_id = impressed_sections.section_id
        FROM impressed_sections
        WHERE impressions.newsletter_id=impressed_sections.newsletter_id
        """
    )

    op.alter_column("impressions", "impressed_section_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_impression_impressed_section_id", "impressions")
    op.drop_column("impressions", "impressed_section_id")

    op.execute("delete from impressed_sections where section_type_id='7d20c0bd-57d9-4d31-916d-4d2e7e148b71';")
    op.execute("delete from section_types where section_type_id = '7d20c0bd-57d9-4d31-916d-4d2e7e148b71'")
