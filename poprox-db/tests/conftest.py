import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Union

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from configargparse import Namespace
from sqlalchemy_utils import create_database, drop_database
from yarl import URL

db_password = os.environ.get("POPROX_DB_PASSWORD", "")

PROJECT_PATH = Path(__file__).parent.parent.resolve()
PROJECT_NAME = PROJECT_PATH.stem
DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:5435/poprox"


def make_alembic_config(cmd_opts: Union[Namespace, SimpleNamespace], base_path: str = PROJECT_PATH) -> Config:
    # Replace path to alembic.ini file to absolute
    if not os.path.isabs(cmd_opts.config):
        cmd_opts.config = os.path.join(base_path, cmd_opts.config)

    config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts)

    # Replace path to alembic folder to absolute
    alembic_location = config.get_main_option("script_location")
    if not os.path.isabs(alembic_location):
        config.set_main_option("script_location", os.path.join(base_path, alembic_location))
    if cmd_opts.pg_url:
        config.set_main_option("sqlalchemy.url", cmd_opts.pg_url)

    return config


def alembic_config_from_url(pg_url: Optional[str] = None) -> Config:
    """
    Provides Python object, representing alembic.ini file.
    """
    cmd_options = SimpleNamespace(
        config="alembic.ini",
        name="alembic",
        pg_url=pg_url,
        raiseerr=False,
        x=None,
    )

    return make_alembic_config(cmd_options)


def get_revisions():
    # Create Alembic configuration object
    # (we don't need database for getting revisions list)
    config = alembic_config_from_url()

    # Get directory object with Alembic migrations
    revisions_dir = ScriptDirectory.from_config(config)

    # Get & sort migrations, from first to last
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions


@contextmanager
def tmp_database(db_url: URL, suffix: str = "", **kwargs):
    tmp_db_name = ".".join([uuid.uuid4().hex, PROJECT_NAME, suffix])
    tmp_db_url = str(db_url.with_path(tmp_db_name))
    create_database(tmp_db_url, **kwargs)

    try:
        yield tmp_db_url
    finally:
        drop_database(tmp_db_url)


@pytest.fixture
def postgres(pg_url):
    """
    Creates empty temporary database.
    """
    with tmp_database(pg_url, "pytest") as tmp_url:
        yield tmp_url


@pytest.fixture()
def alembic_config(postgres):
    """
    Alembic configuration object, bound to temporary database.
    """
    return alembic_config_from_url(postgres)


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return URL(os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL))
