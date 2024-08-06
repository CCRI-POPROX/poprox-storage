import os
from uuid import uuid4

import pytest
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.articles import DbArticleRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository
from sqlalchemy import create_engine, text

from poprox_concepts import Article

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_fetch_newsletters(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from impressions"))
        conn.execute(text("delete from clicks;"))
        conn.execute(text("delete from newsletters;"))
        conn.execute(text("delete from articles;"))

        dbAccountRepository = DbAccountRepository(conn)
        dbArticleRepository = DbArticleRepository(conn)

        dbNewsletterRepository = DbNewsletterRepository(conn)

        newsletter_1_articles = [
            Article(title="title-1", content = "article content 1", url="url-1"),
            Article(title="title-2", url="url-2"),
        ]

        newsletter_2_articles = [
            Article(title="title-3", url="url-1"),
        ]

        user_account_1 = dbAccountRepository.create_new_account(email="user-1@gmail.com", source="test")
        user_account_2 = dbAccountRepository.create_new_account(email="user-2@gmail.com", source="test")
        accounts = [user_account_1, user_account_2]

        article_id_1 = dbArticleRepository.insert_article(newsletter_1_articles[0])
        article_id_2 = dbArticleRepository.insert_article(newsletter_1_articles[1])
        article_id_3 = dbArticleRepository.insert_article(newsletter_2_articles[0])

        newsletter_1_articles = dbArticleRepository.fetch_articles_by_id([article_id_1, article_id_2])
        newsletter_2_articles = dbArticleRepository.fetch_articles_by_id([article_id_3])

        newsletter_1_id = uuid4()
        newsletter_2_id = uuid4()

        dbNewsletterRepository.conn.commit()
        dbNewsletterRepository.log_newsletter_content(
            newsletter_1_id, user_account_1.account_id, newsletter_1_articles, "fake-url-1"
        )
        dbNewsletterRepository.log_newsletter_content(
            newsletter_2_id, user_account_2.account_id, newsletter_2_articles, "fake-url-2"
        )

        results = dbNewsletterRepository.fetch_newsletters(accounts)

        assert 2 == len(results)
        user_1_newsletter = results[user_account_1.account_id]
        assert 1 == len(user_1_newsletter)
        assert 2 == len(user_1_newsletter[newsletter_1_id])
        assert "article content 1" == user_1_newsletter[newsletter_1_id][0].content

        user_2_newsletter = results[user_account_2.account_id]
        assert 1 == len(user_2_newsletter)
        assert 1 == len(user_2_newsletter[newsletter_2_id])
