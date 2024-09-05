import os
import uuid

import pytest
from sqlalchemy import create_engine, text

from poprox_concepts import ArticlePlacement
from poprox_storage.repositories.placements import DbPlacementRepository

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_placement_table(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from article_placements"))

        # Connect to the placement repository
        placement_repo = DbPlacementRepository(conn)

        # Create a test placement
        test_placement = ArticlePlacement(
            article_id=uuid.uuid4(),
            url="test-url",
            section="test-section",
            level="test-level",
            image_url="test-image_url",
            created_at="2024-09-04 20:00:00",
        )

        # Store the test placement
        placement_repo.store_placement(test_placement)

        # Verify if there is only one placement in the table
        assert len(placement_repo.fetch_all_placements()) == 1

        # Verify if the test placement was stored -- by URL
        result = placement_repo.fetch_placement_by_url("test-url")
        assert result.image_url == "test-image_url"

        # Delete the test placement and verify that it was deleted
        placement_repo.delete_placement("test-url")
        assert placement_repo.fetch_placement_by_url("test-url") is None
