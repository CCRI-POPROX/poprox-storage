import datetime
import os

import pytest
from sqlalchemy import create_engine, text

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
        # Verify that the table was created and is initially empty
        result = conn.execute(text("SELECT * FROM scraped_articles"))
        assert result.fetchall() == []

        # Insert a row of data
        conn.execute(
            text(
                """
                INSERT INTO scraped_articles (title, description, url, section, level, image_url, scraped_at)
                VALUES ('test-title', 'test-description', 'test-url', 'test-section',
                'test-level', 'test-image_url', '2024-08-21 16:39:29')
                """
            )
        )

        # Verify that the data was inserted
        result = conn.execute(text("SELECT * FROM scraped_articles"))

        # Prepare a datetime object for "2024-08-21 16:39:29"
        scraped_at = datetime.datetime(2024, 8, 21, 16, 39, 29)
        assert result.fetchall() == [
            (
                "test-title",
                "test-description",
                "test-url",
                "test-section",
                "test-level",
                "test-image_url",
                scraped_at,
            )
        ]

        # Clear the table
        conn.execute(text("DELETE FROM scraped_articles"))

        # Verify that the table is empty
        result = conn.execute(text("SELECT * FROM scraped_articles"))
        assert result.fetchall() == []
