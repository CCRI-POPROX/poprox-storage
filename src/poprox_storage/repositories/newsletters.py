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

from poprox_concepts.domain import Account, Article, Newsletter
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbNewsletterRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "newsletters",
            "impressions",
        )

    def store_newsletter(self, newsletter: Newsletter):
        newsletter_table = self.tables["newsletters"]
        impression_table = self.tables["impressions"]

        self.conn.commit()  # End any transaction already in progress
        with self.conn.begin():
            stmt = insert(newsletter_table).values(
                newsletter_id=newsletter.newsletter_id,
                account_id=str(newsletter.account_id),
                treatment_id=str(newsletter.treatment_id) if newsletter.treatment_id else None,
                content=[rec.model_dump_json() for rec in newsletter.articles],
                email_subject=newsletter.subject,
                html=newsletter.body_html,
            )
            self.conn.execute(stmt)

            for position, article in enumerate(newsletter.articles):
                stmt = insert(impression_table).values(
                    newsletter_id=str(newsletter.newsletter_id),
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
                    headline=raw["headline"],
                    subhead=raw.get("subhead", None),
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


class S3NewsletterRepository(S3Repository):
    def store_as_parquet(self, newsletters: list[Newsletter]) -> str:
        import pandas as pd

        newsletter_df = pd.DataFrame.from_records(extract_and_flatten(newsletters))
        return self._write_dataframe_as_parquet(newsletter_df)


def extract_and_flatten(newsletters):
    def flatten(account_id, account_newsletters):
        newsletter_list = []
        for newsletter_id in account_newsletters:
            articles = account_newsletters[newsletter_id]
            for article in articles:
                row = {}
                row["account_id"] = str(account_id)
                row["newsletter_id"] = str(newsletter_id)
                row["article_id"] = str(article.article_id)
                newsletter_list.append(row)
        return newsletter_list

    final_list = []
    for account_id in newsletters:
        final_list.extend(flatten(account_id, newsletters[account_id]))
    return final_list
