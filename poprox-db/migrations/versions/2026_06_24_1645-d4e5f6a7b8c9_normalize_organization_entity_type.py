"""normalize organization entity_type spelling

Normalizes the entity_type for organization entities from the British spelling
"organisation" (emitted by the older AP parser) to the canonical American spelling
"organization", matching poprox_concepts.domain.account.EntityType.

Revision ID: d4e5f6a7b8c9
Revises: a09bfb1c0f31
Create Date: 2026-06-24 16:45:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "a09bfb1c0f31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE entities SET entity_type = 'organization' WHERE entity_type = 'organisation'")


def downgrade() -> None:
    op.execute("UPDATE entities SET entity_type = 'organisation' WHERE entity_type = 'organization'")
