import os

import pytest
from poprox_storage.repositories.scrapes import DbScrapeRepository
from sqlalchemy import create_engine, text

from poprox_concepts import ScrapedArticle

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_scrape_table(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from scraped_articles"))

        # Connect to the scrape repository
        scrape_repo = DbScrapeRepository(conn)

        # Create a test scrape
        test_scrape = ScrapedArticle(
            title="test-title",
            description="test-description",
            url="test-url",
            section="test-section",
            level="test-level",
            image_url="test-image_url",
            created_at="2024-08-22 17:56:00",
        )

        # Store the test scrape
        scrape_repo.store_scrape(test_scrape)

        # Verify that the test scrape was stored
        result = scrape_repo.fetch_scrape_by_url("test-url")
        assert result.title == "test-title"

        # Delete the test scrape and verify that it was deleted
        scrape_repo.delete_scrape("test-url")
        assert scrape_repo.fetch_scrape_by_url("test-url") is None
