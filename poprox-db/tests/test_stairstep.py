from pathlib import Path

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import Script

from tests.conftest import get_revisions

PROJECT_PATH = Path(__file__).parent.parent.resolve()


@pytest.mark.parametrize("revision", get_revisions())
def test_migrations_stairway(alembic_config: Config, revision: Script):
    """
    From https://github.com/alvassin/alembic-quickstart

    Test can find forgotten downgrade methods, undeleted data types in downgrade
    methods, typos and many other errors.

    Does not require any maintenance - you just add it once to check 80% of typos
    and mistakes in migrations forever.
    """
    if isinstance(revision.down_revision, tuple):
        return  # don't test merge revisions

    upgrade(alembic_config, revision.revision)

    # We need -1 for downgrading first migration (its down_revision is None)
    downgrade(alembic_config, revision.down_revision or "-1")
    upgrade(alembic_config, revision.revision)
