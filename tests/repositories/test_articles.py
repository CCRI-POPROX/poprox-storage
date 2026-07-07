from datetime import datetime

from sqlalchemy import text

from poprox_concepts.domain import Article
from poprox_storage.repositories.articles import DbArticleRepository
from tests import clear_tables

# Article children first (leaf tables that reference articles), then the rest, then articles.
_TABLES = [
    "mentions",
    "article_image_associations",
    "article_links",
    "candidate_articles",
    "impressions",
    "clicks",
    "impressed_sections",
    "section_types",
    "newsletters",
    "article_placements",
    "articles",
]


def test_fetch_by_external_id_is_source_aware(db_engine):
    # Two sources sharing an external_id must stay distinguishable (the core fix).
    with db_engine.connect() as conn:
        clear_tables(conn, *_TABLES)
        repo = DbArticleRepository(conn)
        repo.store_article(
            Article(headline="ap story", url="https://apnews.com/x", source="AP", external_id="shared-1")
        )
        repo.store_article(
            Article(headline="pp story", url="https://propublica.org/x", source="ProPublica", external_id="shared-1")
        )

        ap = repo.fetch_article_by_external_id("shared-1", source="AP")
        pp = repo.fetch_article_by_external_id("shared-1", source="ProPublica")

        assert ap is not None
        assert ap.source == "AP"
        assert ap.headline == "ap story"
        assert pp is not None
        assert pp.source == "ProPublica"
        assert pp.headline == "pp story"
        # right id, wrong source -> nothing
        assert repo.fetch_article_by_external_id("shared-1", source="Reuters") is None
        # unknown id -> nothing
        assert repo.fetch_article_by_external_id("does-not-exist", source="AP") is None


def test_fetch_by_external_id_without_source_is_backward_compatible(db_engine):
    # Omitting source keeps the pre-change behavior: returns a matching row (not None), source-blind.
    with db_engine.connect() as conn:
        clear_tables(conn, *_TABLES)
        repo = DbArticleRepository(conn)
        repo.store_article(
            Article(headline="ap story", url="https://apnews.com/x", source="AP", external_id="shared-2")
        )
        repo.store_article(
            Article(headline="pp story", url="https://propublica.org/x", source="ProPublica", external_id="shared-2")
        )

        result = repo.fetch_article_by_external_id("shared-2")
        assert result is not None
        assert result.external_id == "shared-2"


def test_metadata_only_article_round_trips(db_engine):
    # A ProPublica-shaped article: body text, canonical url, no images/mentions.
    with db_engine.connect() as conn:
        clear_tables(conn, *_TABLES)
        repo = DbArticleRepository(conn)
        repo.store_article(
            Article(
                headline="An Investigation",
                url="https://www.propublica.org/article/investigation",
                source="ProPublica",
                external_id="pp-meta-1",
                body="full article text",
                images=None,
                preview_image_id=None,
            )
        )

        article = repo.fetch_article_by_external_id("pp-meta-1", source="ProPublica")
        assert article is not None
        assert article.headline == "An Investigation"
        assert article.url == "https://www.propublica.org/article/investigation"
        assert article.source == "ProPublica"
        assert article.body == "full article text"
        assert not article.images  # None/empty: no images persisted

        # metadata-only -> zero image-association and mention rows
        assert conn.execute(text("SELECT count(*) FROM article_image_associations")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM mentions")).scalar() == 0


def test_same_source_external_id_dedups_to_latest(db_engine):
    # Multiple rows per (source, external_id) are kept as history; fetch returns the newest.
    with db_engine.connect() as conn:
        clear_tables(conn, *_TABLES)
        repo = DbArticleRepository(conn)
        repo.store_article(
            Article(
                headline="v1 headline",
                url="https://apnews.com/dup/v1",
                source="AP",
                external_id="dup-1",
                created_at=datetime(2024, 1, 1),
            )
        )
        repo.store_article(
            Article(
                headline="v2 headline",
                url="https://apnews.com/dup/v2",
                source="AP",
                external_id="dup-1",
                created_at=datetime(2025, 1, 1),
            )
        )

        # both rows persisted (history kept, not overwritten)
        count = conn.execute(
            text("SELECT count(*) FROM articles WHERE source = 'AP' AND external_id = 'dup-1'")
        ).scalar()
        assert count == 2

        latest = repo.fetch_article_by_external_id("dup-1", source="AP")
        assert latest is not None
        assert latest.headline == "v2 headline"  # newest created_at wins


def test_null_url_is_rejected_by_schema(db_engine):
    # url is NOT NULL: a url-less article is rejected -- the repo catches the NotNullViolation,
    # logs it, and returns None, so it is never silently stored.
    with db_engine.connect() as conn:
        clear_tables(conn, *_TABLES)
        repo = DbArticleRepository(conn)
        result = repo.store_article(Article(headline="no url", url=None, source="AP", external_id="no-url-1"))
        assert result is None
