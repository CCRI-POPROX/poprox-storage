from sqlalchemy import (
    Connection,
    Table,
    select,
)

from poprox_concepts.domain.article import ScrapedArticle
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbScrapeRepository(DatabaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn)
        self.tables: dict[str, Table] = self._load_tables("scraped_articles")

    def store_scrape(self, scrape: ScrapedArticle) -> None:
        return self._insert_model("scraped_articles", scrape)

    def fetch_scrape_by_url(self, url: str) -> ScrapedArticle | None:
        scrape_table = self.tables["scraped_articles"]

        query = select(scrape_table).where(scrape_table.c.url == url)

        result = self.conn.execute(query).first()

        if result:
            return ScrapedArticle(
                title=result.title,
                description=result.description,
                url=result.url,
                section=result.section,
                level=result.level,
                image_url=result.image_url,
                created_at=result.created_at,
            )
        else:
            return None

    # Delete a scrape by its URL
    def delete_scrape(self, url: str) -> None:
        table = self.tables["scraped_articles"]
        query = table.delete().where(table.c.url == url)
        self.conn.execute(query)
