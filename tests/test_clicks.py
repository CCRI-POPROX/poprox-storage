import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from poprox_concepts import Account, Article
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.articles import DbArticleRepository
from poprox_storage.repositories.clicks import DbClicksRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_get_click_between(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from impressions"))
        conn.execute(text("delete from clicks;"))
        conn.execute(text("delete from newsletters;"))
        conn.execute(text("delete from articles;"))

        dbAccountRepository = DbAccountRepository(conn)
        dbArticleRepository = DbArticleRepository(conn)

        dbNewsletterRepository = DbNewsletterRepository(conn)
        dbClicksRepository = DbClicksRepository(conn)

        user_account_1 = dbAccountRepository.store_new_account(email="user-1@gmail.com", source="test")

        articles = [
            Article(title="title-1", url="url-1"),
            Article(title="title-2", url="url-2"),
        ]

        article_id_1 = dbArticleRepository.store_article(articles[0])
        article_id_2 = dbArticleRepository.store_article(articles[1])

        accounts = [
            Account(account_id=user_account_1.account_id, email="user-1@gmail.com", status="", source="test"),
            Account(account_id=uuid4(), email="user-2@gmail.com", status="", source="test"),
        ]

        newsletter_id = uuid4()
        dbNewsletterRepository.store_newsletter(newsletter_id, user_account_1.account_id, [], "", "")

        dbClicksRepository.store_click(
            newsletter_id, user_account_1.account_id, article_id_1, "title-1", "2024-06-12 09:55:22"
        )
        dbClicksRepository.store_click(
            newsletter_id, user_account_1.account_id, article_id_2, "title-2", "2024-07-14 12:55:22"
        )

        start_time = "2024-06-13 09:55:22"
        end_time = "2024-07-15 09:55:22"
        results = dbClicksRepository.fetch_clicks_between(accounts, start_time, end_time)

        assert 2 == len(results)

        valid_click = results[user_account_1.account_id]

        assert 1 == len(valid_click)
        assert article_id_2 == valid_click[0].article_id
