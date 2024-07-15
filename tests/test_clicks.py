from poprox_storage.repositories.clicks import DbClicksRepository
from poprox_concepts import Account
from datetime import datetime

import json
import pytest
import os
from sqlalchemy import create_engine, text
from uuid import uuid4

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_get_active_survey(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from clicks;"))
        conn.execute(text("delete from newsletters;"))
        conn.execute(text("delete from articles;"))

        dummy_click_1 = uuid4()
        dummy_click_2 = uuid4()
        dummy_user_1 = uuid4()
        dummy_user_2 = uuid4()
        dummy_newsletter = uuid4()

        dummy_article_1 = uuid4()
        dummy_article_2 = uuid4()

        query_0 = text(
                f'''insert into accounts(account_id, email, status, source) values (:account_id, 'user-1@gmail.com', '', '');'''
            )
        query_1 = text(
                f'''insert into clicks(click_id, account_id, newsletter_id, article_id, created_at)
                    values (:click_id_1, :account_id, :newsletter_id, :article_id_1, '2024-06-12 09:55:22');'''
            )
        query_2 = text(
                f'''insert into clicks(click_id, account_id, newsletter_id, article_id, created_at)
                    values (:click_id_2, :account_id, :newsletter_id, :article_id_2,  '2024-07-14 12:55:22');'''
            )
        query_3 = text(
                f'''insert into newsletters(newsletter_id, account_id, content, created_at, html) 
                values (:newsletter_id, :account_id, '{json.dumps({})}', '{datetime.now()}', '');'''
            )
        query_4 = text(
            f'''insert into articles(article_id, published_at, created_at, title, content, url) 
                values (:article_id, '{datetime.now()}', '{datetime.now()}', :title, '{json.dumps({})}', :url);'''
        )
        
        params_0 = {
            'account_id': str(dummy_user_1)
        }
        
        params_1 = {
            'account_id': str(dummy_user_1),
            'click_id_1': str(dummy_click_1),
            'newsletter_id': str(dummy_newsletter),
            'article_id_1': str(dummy_article_1)
        }

        params_2 = {
            'account_id': str(dummy_user_1),
            'click_id_2': str(dummy_click_2),
            'newsletter_id': str(dummy_newsletter),
            'article_id_2': str(dummy_article_2)
        }
        params_3 = {
            'newsletter_id': str(dummy_newsletter),
            'account_id': str(dummy_user_1)
        }
        params_4 = {
            'article_id': str(dummy_article_1),
            'title': 'title-1',
            'url': 'url-1'
        }
        params_5 = {
            'article_id': str(dummy_article_2),
            'title': 'title-2',
            'url': 'url-2'
        }

        conn.execute(query_0, params_0)
        conn.execute(query_3, params_3)
        conn.execute(query_4, params_4)
        conn.execute(query_4, params_5)

        conn.execute(query_1, params_1)
        conn.execute(query_2, params_2)
        conn.commit()

        repo = DbClicksRepository(conn)
        accounts = [Account(account_id=dummy_user_1, email='user-1@gmail.com', status=''), 
                    Account(account_id=dummy_user_2, email='user-2@gmail.com', status='')]
        
        start_time = '2024-06-13 09:55:22'
        end_time = '2024-07-15 09:55:22'
        results = repo.get_clicks_within_timestamp(accounts, start_time, end_time)
        
        assert 2 == len(results)

        valid_click = results[dummy_user_1]

        assert 1 == len(valid_click)
        assert dummy_article_2 == valid_click[0].article_id