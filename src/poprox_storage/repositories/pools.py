import logging
from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import (
    Connection,
    Table,
    and_,
    desc,
    select,
)
from sqlalchemy.dialects.postgresql import insert

from poprox_concepts.domain import CandidatePool
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

    def store_candidate_pool(self, pool: CandidatePool) -> UUID | None:
        candidate_pools_table = self.tables["candidate_pools"]
        candidate_articles_table = self.tables["candidate_articles"]

        pool_insert_stmt = (
            insert(candidate_pools_table)
            .values(candidate_pool_id=pool.pool_id, pool_type=pool.pool_type)
            .returning(candidate_pools_table.c.pool_id)
        )

        row = self.conn.execute(pool_insert_stmt).one_or_none()
        candidate_pool_id = row.candidate_pool_id

        if candidate_pool_id:
            insert_stmt = (
                insert(candidate_articles_table)
                .values(
                    [
                        {"candidate_pool_id": candidate_pool_id, "article_id": article.article_id}
                        for article in pool.articles
                    ]
                )
                .on_conflict_do_nothing(constraint="uq_candidate_articles")
            )
            self.conn.execute(insert_stmt)

        return candidate_pool_id

    def fetch_candidate_pool(self, candidate_pool_id: UUID) -> CandidatePool:
        pools_table = self.tables["candidate_pools"]
        candidates_table = self.tables["candidate_articles"]
        articles_table = self.tables["articles"]
        links_table = self.tables["article_links"]

        # First get the pool attributes
        pool_query = select(pools_table).where(pools_table.c.pool_id == candidate_pool_id)
        row = self.conn.execute(pool_query).one_or_none()
        pool = CandidatePool(pool_id=row.candidate_pool_id, pool_type=row.pool_type, created_at=row.created_at)

        # Then query for the articles and attach to the pool
        query = (
            select(articles_table)
            .join(candidates_table, candidates_table.c.article_id == articles_table.c.article_id)
            .where(candidates_table.c.candidate_pool_id == candidate_pool_id)
        )
        pool.articles = _fetch_articles(self.conn, query, links_table)

        return pool

    def fetch_candidate_pools_between(self, start_date: date, end_date: date) -> list[CandidatePool]:
        pools_table = self.tables["candidate_pools"]
        candidates_table = self.tables["candidate_articles"]
        articles_table = self.tables["articles"]
        links_table = self.tables["article_links"]

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        # First query for the pool ids and attributes
        pool_query = select(pools_table).where(
            and_(pools_table.c.created_at >= start_dt, pools_table.c.created_at <= end_dt)
        )
        rows = self.conn.execute(pool_query).fetchall()

        pools = [
            CandidatePool(pool_id=row.candidate_pool_id, pool_type=row.pool_type, created_at=row.created_at)
            for row in rows
        ]

        # Then loop through and fetch the contents
        for pool in pools:
            query = (
                select(articles_table)
                .join(candidates_table, candidates_table.c.article_id == articles_table.c.article_id)
                .where(candidates_table.c.candidate_pool_id == pool.pool_id)
            )
            pool.articles = _fetch_articles(self.conn, query, links_table)

        return pools

    def fetch_latest_pool_of_type(self, candidate_pool_type: str) -> CandidatePool | None:
        candidate_pools_table = self.tables["candidate_pools"]

        query = (
            select(candidate_pools_table)
            .where(candidate_pools_table.c.pool_type == candidate_pool_type)
            .order_by(desc(candidate_pools_table.c.created_at))
            .limit(1)
        )
        result = self.conn.execute(query).fetchone()

        return self.fetch_candidate_pool(result.candidate_pool_id) if result else None

    def fetch_latest_pool_of_type_before(self, pool_type: str, date: date) -> CandidatePool | None:
        candidate_pools_table = self.tables["candidate_pools"]

        query = (
            select(candidate_pools_table.c.candidate_pool_id)
            .where(candidate_pools_table.c.pool_type == pool_type, candidate_pools_table.c.created_at < date)
            .order_by(desc(candidate_pools_table.c.created_at))
            .limit(1)
        )
        result = self.conn.execute(query).fetchone()

        return self.fetch_candidate_pool(result.candidate_pool_id) if result else None
