import logging
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    Connection,
    Table,
    desc,
    select,
)
from sqlalchemy.dialects.postgresql import insert

from poprox_concepts.domain import Article
from poprox_storage.repositories.articles import _fetch_articles
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbCandidatePoolRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "articles", "article_links", "candidate_pools", "candidate_articles"
        )

    def store_candidate_pool(self, pool_type: str, articles: list[Article]):
        candidate_pools_table = self.tables["candidate_pools"]
        candidate_articles_table = self.tables["candidate_articles"]

        candidate_pool_id: UUID = uuid4()

        set_insert_stmt = insert(candidate_pools_table).values(
            {"candidate_pool_id": candidate_pool_id, "pool_type": pool_type}
        )
        self.conn.execute(set_insert_stmt)

        insert_stmt = (
            insert(candidate_articles_table)
            .values(
                [{"candidate_pool_id": candidate_pool_id, "article_id": article.article_id} for article in articles]
            )
            .on_conflict_do_nothing(constraint="uq_candidate_articles")
        )
        self.conn.execute(insert_stmt)

        return candidate_pool_id

    def fetch_candidate_pool(self, candidate_pool_id: UUID) -> list[Article]:
        candidate_articles_table = self.tables["candidate_articles"]
        articles_table = self.tables["articles"]
        links_table = self.tables["article_links"]

        query = (
            select(articles_table)
            .join(candidate_articles_table, candidate_articles_table.c.article_id == articles_table.c.article_id)
            .where(candidate_articles_table.c.candidate_pool_id == candidate_pool_id)
        )

        return _fetch_articles(self.conn, query, links_table)

    def fetch_latest_pool_of_type(self, candidate_pool_type: str) -> UUID | None:
        candidate_pools_table = self.tables["candidate_pools"]

        query = (
            select(candidate_pools_table)
            .where(candidate_pools_table.c.pool_type == candidate_pool_type)
            .order_by(desc(candidate_pools_table.c.created_at))
            .limit(1)
        )

        result = self.conn.execute(query).fetchone()

        return result.candidate_pool_id if result else None

    def fetch_latest_pool_of_type_before(self, pool_type: str, date: date) -> UUID | None:
        candidate_pools_table = self.tables["candidate_pools"]

        query = (
            select(candidate_pools_table.c.candidate_pool_id)
            .where(candidate_pools_table.c.pool_type == pool_type, candidate_pools_table.c.created_at < date)
            .order_by(desc(candidate_pools_table.c.created_at))
            .limit(1)
        )

        result = self.conn.execute(query).fetchone()

        return result.candidate_pool_id if result else None
