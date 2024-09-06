from poprox_storage.repositories.articles import DbArticleRepository
from poprox_storage.repositories.placements import DbPlacementRepository
from sqlalchemy import text

from poprox_concepts import Article, ArticlePlacement


def test_placement_table(db_engine):
    with db_engine.connect() as conn:
        conn.execute(text("delete from article_placements;"))

        # Connect to the article and placement repository
        dbArticleRepository = DbArticleRepository(conn)
        dbPlacementRepository = DbPlacementRepository(conn)

        # Create a test article
        test_article = Article(
            headline="test-headline",
            url="test-url",
        )

        # Store the test article and get the article_id
        test_article_id = dbArticleRepository.store_article(test_article)

        # Create a test placement
        test_placement = ArticlePlacement(
            article_id=test_article_id,
            url="test-url",
            section="test-section",
            level="test-level",
            image_url="test-image_url",
            created_at="2024-09-06 20:00:00",
        )

        # Store the test placement
        dbPlacementRepository.store_placement(test_placement)

        # Verify if there is only one placement in the table
        assert len(dbPlacementRepository.fetch_all_placements()) == 1

        # Verify if the test placement was stored -- by URL
        result = dbPlacementRepository.fetch_placement_by_url("test-url")
        assert result.image_url == "test-image_url"

        # Verify if the test placement was stored -- by article_id
        result = dbPlacementRepository.fetch_placement_by_id(test_article_id)
        assert result.url == "test-url"

        # Delete the test placement and verify that it was deleted
        dbPlacementRepository.delete_placement("test-url")
        assert dbPlacementRepository.fetch_placement_by_url("test-url") is None
