from poprox_concepts.domain import Article, Impression, Newsletter
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.articles import DbArticleRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository
from tests import clear_tables


def test_fetch_newsletters(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "impressions",
            "clicks",
            "newsletters",
            "articles",
        )

        dbAccountRepository = DbAccountRepository(conn)
        dbArticleRepository = DbArticleRepository(conn)

        dbNewsletterRepository = DbNewsletterRepository(conn)

        newsletter_1_articles = [
            Article(
                headline="headline-1",
                subhead="subhead-1",
                url="url-1",
                external_id="external-1",
                source="tests",
            ),
            Article(
                headline="headline-2",
                url="url-2",
                external_id="external-2",
                source="tests",
            ),
        ]

        newsletter_2_articles = [
            Article(
                headline="headline-3",
                url="url-1",
                external_id="external-3",
                source="tests",
            ),
        ]

        user_account_1 = dbAccountRepository.store_new_account(email="user-1@gmail.com", source="test")
        user_account_2 = dbAccountRepository.store_new_account(email="user-2@gmail.com", source="test")
        accounts = [user_account_1, user_account_2]

        article_id_1 = dbArticleRepository.store_article(newsletter_1_articles[0])
        article_id_2 = dbArticleRepository.store_article(newsletter_1_articles[1])
        article_id_3 = dbArticleRepository.store_article(newsletter_2_articles[0])

        newsletter_1_articles = dbArticleRepository.fetch_articles_by_id([article_id_1, article_id_2])
        newsletter_2_articles = dbArticleRepository.fetch_articles_by_id([article_id_3])

        newsletter_1 = Newsletter(
            account_id=user_account_1.account_id,
            impressions=[
                Impression(position=idx, article=article) for idx, article in enumerate(newsletter_1_articles)
            ],
            subject="fake-subject",
            body_html="fake-html-1",
        )
        dbNewsletterRepository.store_newsletter(newsletter_1)

        newsletter_2 = Newsletter(
            account_id=user_account_2.account_id,
            impressions=[
                Impression(position=idx, article=article) for idx, article in enumerate(newsletter_2_articles)
            ],
            subject="fake-subject",
            body_html="fake-html-2",
        )
        dbNewsletterRepository.store_newsletter(newsletter_2)

        results = dbNewsletterRepository.fetch_newsletters(accounts)
        assert 2 == len(results)
        user_1_newsletter = results[user_account_1.account_id]
        assert 1 == len(user_1_newsletter)
        assert 2 == len(user_1_newsletter[newsletter_1.newsletter_id])
        assert "subhead-1" == user_1_newsletter[newsletter_1.newsletter_id][0].subhead

        user_2_newsletter = results[user_account_2.account_id]
        assert 1 == len(user_2_newsletter)
        assert 1 == len(user_2_newsletter[newsletter_2.newsletter_id])
