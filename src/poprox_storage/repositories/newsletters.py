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

from poprox_concepts.domain import Account, Article, Impression, Newsletter
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbNewsletterRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "newsletters",
            "impressions",
            "articles",
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

    def fetch_newsletters_by_treatment_id(self, expt_treatment_ids: list[UUID]) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        newsletters_query = select(newsletters_table).where(
            newsletters_table.c.treatment_id.in_(expt_treatment_ids),
        )
        newsletter_result = self.conn.execute(newsletters_query).fetchall()

        articles_query = (
            select(impressions_table.c.newsletter_id, articles_table)
            .join(
                impressions_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(impressions_table.c.newsletter_id.in_([row.newsletter_id for row in newsletter_result]))
        )

        articles_result = self.conn.execute(articles_query).fetchall()

        articles_by_newsletter_id = defaultdict(list)
        for row in articles_result:
            articles_by_newsletter_id[row.newsletter_id].append(
                Article(
                    article_id=row.article_id,
                    headline=row.headline,
                    subhead=row.subhead,
                    url=row.url,
                    preview_image_id=row.preview_image_id,
                    published_at=row.published_at,
                    source=row.source,
                    external_id=row.external_id,
                    raw_data=row.raw_data,
                )
            )

        return [
            Newsletter(
                newsletter_id=row.newsletter_id,
                account_id=row.account_id,
                treatment_id=row.treatment_id,
                articles=articles_by_newsletter_id[row.newsletter_id],
                subject=row.email_subject,
                body_html=row.html,
                created_at=row.created_at,
            )
            for row in newsletter_result
        ]

    def fetch_impressions_by_newsletter_ids(self, newsletter_ids: list[UUID]) -> list[Impression]:
        impressions_table = self.tables["impressions"]

        query = select(
            impressions_table.c.newsletter_id,
            impressions_table.c.article_id,
            impressions_table.c.position,
        ).where(
            impressions_table.c.newsletter_id.in_(newsletter_ids),
        )
        rows = self.conn.execute(query).fetchall()
        return [
            Impression(
                newsletter_id=row.newsletter_id,
                article_id=row.article_id,
                position=row.position,
            )
            for row in rows
        ]


class S3NewsletterRepository(S3Repository):
    def store_as_parquet(
        self,
        newsletters: list[Newsletter],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ) -> str:
        import pandas as pd

        newsletter_df = pd.DataFrame.from_records(extract_and_flatten(newsletters))
        return self._write_dataframe_as_parquet(newsletter_df, bucket_name, file_prefix, start_time)

    def store_impressions_as_parquet(
        self,
        impressions: list[Impression],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ) -> str:
        import pandas as pd

        impression_df = pd.DataFrame.from_records(convert_impressions_to_records(impressions))
        return self._write_dataframe_as_parquet(impression_df, bucket_name, file_prefix, start_time)


def extract_and_flatten(newsletters: list[Newsletter]) -> list[dict]:
    def flatten(newsletter):
        rows = []
        for article in newsletter.articles:
            row = {}
            row["account_id"] = str(newsletter.account_id)
            row["newsletter_id"] = str(newsletter.newsletter_id)
            row["article_id"] = str(article.article_id)
            rows.append(row)
        return rows

    final_list = []
    for newsletter in newsletters:
        final_list.extend(flatten(newsletter))
    return final_list


def convert_impressions_to_records(impressions: list[Impression]) -> list[dict]:
    rows = []

    for impression in impressions:
        row = {}
        row["newsletter_id"] = str(impression.newsletter_id)
        row["article_id"] = str(impression.article_id)
        row["position"] = impression.position
        rows.append(row)

    return rows
