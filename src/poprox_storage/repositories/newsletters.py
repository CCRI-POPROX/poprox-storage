from typing import Dict

from sqlalchemy import (
    insert,
    Connection,
    Table,
)

from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbNewsletterRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: Dict[str, Table] = self._load_tables(
            "newsletters",
            "impressions",
        )

    def store_newsletter(
        self, newsletter_id, account_id, recommended_articles, article_html
    ):
        # TODO: Add the email title to the newsletter table
        newsletter_table = self.tables["newsletters"]
        impression_table = self.tables["impressions"]

        with self.conn.begin():
            stmt = insert(newsletter_table).values(
                newsletter_id=newsletter_id,
                account_id=str(account_id),
                content=[rec.json() for rec in recommended_articles],
                html=article_html,
            )
            self.conn.execute(stmt)

            for position, article in enumerate(recommended_articles):
                stmt = insert(impression_table).values(
                    newsletter_id=str(newsletter_id),
                    article_id=str(article.article_id),
                    position=1 + position,
                )
                self.conn.execute(stmt)

    log_newsletter_content = store_newsletter
