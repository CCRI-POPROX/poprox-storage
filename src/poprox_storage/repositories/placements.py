from uuid import UUID

from sqlalchemy import (
    Connection,
    Table,
    select,
)

from poprox_concepts.domain.article import ArticlePlacement
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbPlacementRepository(DatabaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn)
        self.tables: dict[str, Table] = self._load_tables("article_placements")

    # Store a placement in the database
    def store_placement(self, placement: ArticlePlacement) -> None:
        return self._insert_model("article_placements", placement)

    # Fetch a placement by its ID
    def fetch_placement_by_id(self, article_id: UUID) -> ArticlePlacement | None:
        placement_table = self.tables["article_placements"]

        query = select(placement_table).where(placement_table.c.article_id == article_id)

        result = self.conn.execute(query).first()

        if result:
            return ArticlePlacement(
                article_id=result.article_id,
                url=result.url,
                section=result.section,
                level=result.level,
                image_url=result.image_url,
                created_at=result.created_at,
            )
        else:
            return None

    # Fetch a placement by its URL
    def fetch_placement_by_url(self, url: str) -> ArticlePlacement | None:
        placement_table = self.tables["article_placements"]

        query = select(placement_table).where(placement_table.c.url == url)

        result = self.conn.execute(query).first()

        if result:
            return ArticlePlacement(
                article_id=result.article_id,
                url=result.url,
                section=result.section,
                level=result.level,
                image_url=result.image_url,
                created_at=result.created_at,
            )
        else:
            return None

    # Fetch all placements
    def fetch_all_placements(self) -> list[ArticlePlacement]:
        placement_table = self.tables["article_placements"]

        query = select(placement_table)

        results = self.conn.execute(query).fetchall()

        return [
            ArticlePlacement(
                article_id=result.article_id,
                url=result.url,
                section=result.section,
                level=result.level,
                image_url=result.image_url,
                created_at=result.created_at,
            )
            for result in results
        ]

    # Delete a placement by its URL
    def delete_placement(self, url: str) -> None:
        table = self.tables["article_placements"]
        query = table.delete().where(table.c.url == url)
        self.conn.execute(query)
