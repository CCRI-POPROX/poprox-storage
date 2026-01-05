from uuid import uuid4

from poprox_concepts.domain import Account, Article, Newsletter
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.articles import DbArticleRepository
from poprox_storage.repositories.clicks import DbClicksRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository
from tests import clear_tables


def test_get_click_between(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "impressions",
            "clicks",
            "impressed_sections",
            "section_types",
            "newsletters",
            "article_placements",
            "articles",
        )

        dbAccountRepository = DbAccountRepository(conn)
        dbArticleRepository = DbArticleRepository(conn)

        dbNewsletterRepository = DbNewsletterRepository(conn)
        dbClicksRepository = DbClicksRepository(conn)

        user_account_1 = dbAccountRepository.store_new_account(email=f"{uuid4()}@example.com", source="test")

        articles = [
            Article(headline="headline-1", url="url-1"),
            Article(headline="headline-2", url="url-2"),
        ]

        article_id_1 = dbArticleRepository.store_article(articles[0])
        article_id_2 = dbArticleRepository.store_article(articles[1])

        accounts = [
            Account(account_id=user_account_1.account_id, email=user_account_1.email, status="", source="test"),
            Account(account_id=uuid4(), email=f"{uuid4()}@gmail.com", status="", source="test"),
        ]

        newsletter = Newsletter(account_id=user_account_1.account_id, sections=[], subject="", body_html="")
        dbNewsletterRepository.store_newsletter(newsletter)

        dbClicksRepository.store_click(
            newsletter.newsletter_id, user_account_1.account_id, article_id_1, "headline-1", "2024-06-12 09:55:22"
        )
        dbClicksRepository.store_click(
            newsletter.newsletter_id, user_account_1.account_id, article_id_2, "headline-2", "2024-07-14 12:55:22"
        )

        start_time = "2024-06-13 09:55:22"
        end_time = "2024-07-15 09:55:22"
        results = dbClicksRepository.fetch_clicks_between(start_time, end_time, accounts)

        assert 2 == len(results)

        valid_click = results[user_account_1.account_id]

        assert 1 == len(valid_click)
        assert article_id_2 == valid_click[0].article_id
