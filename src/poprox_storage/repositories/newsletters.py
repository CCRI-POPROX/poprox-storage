import json
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Connection,
    Table,
    insert,
    select,
)

from poprox_concepts import Account, Article
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbNewsletterRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "newsletters",
            "impressions",
        )

    def store_newsletter(self, newsletter_id, account_id, recommended_articles, email_subject, article_html):
        newsletter_table = self.tables["newsletters"]
        impression_table = self.tables["impressions"]

        with self.conn.begin():
            stmt = insert(newsletter_table).values(
                newsletter_id=newsletter_id,
                account_id=str(account_id),
                content=[rec.json() for rec in recommended_articles],
                email_subject=email_subject,
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

    def fetch_newsletters(self, accounts: list[Account]) -> dict[UUID, dict[UUID, list[Article]]]:
        newsletter_table = self.tables["newsletters"]

        query = select(
            newsletter_table.c.newsletter_id,
            newsletter_table.c.account_id,
            newsletter_table.c.content,
        ).where(
            newsletter_table.c.account_id.in_([acct.account_id for acct in accounts]),
        )
        newsletter_result = self.conn.execute(query).fetchall()
        historic_newsletters = defaultdict(dict)
        for row in newsletter_result:
            raw_articles = []
            for article_json in row.content:
                if isinstance(article_json, dict):
                    article_json = json.dumps(article_json)
                raw_articles.append(json.loads(article_json))
            articles = [
                Article(
                    article_id=raw["article_id"],
                    title=raw["title"],
                    content=raw.get("content", None),
                    url=raw["url"],
                    published_at=datetime.strptime(
                        raw.get("published_at", "1970-01-01T00:00:00")[:19],
                        "%Y-%m-%dT%H:%M:%S",
                    ),
                )
                for raw in raw_articles
            ]
            historic_newsletters[row.account_id][row.newsletter_id] = articles
        return historic_newsletters
