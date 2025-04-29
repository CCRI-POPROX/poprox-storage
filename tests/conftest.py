import os

import pytest
from sqlalchemy import create_engine

db_user = os.environ.get("POPROX_DB_USER", "postgres")
db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "5432")

DEFAULT_PG_URL = f"postgresql://{db_user}:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


@pytest.fixture(scope="session")
def db_engine(pg_url):
    return create_engine(pg_url)
