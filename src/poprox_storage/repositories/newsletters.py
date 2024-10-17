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

            for impression in newsletter.impressions:
                stmt = insert(impression_table).values(
                    newsletter_id=str(newsletter.newsletter_id),
                    article_id=str(impression.article.article_id),
                    position=impression.position,
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

        impressions_query = (
            select(impressions_table.c.newsletter_id, impressions_table.c.position, articles_table)
            .join(
                impressions_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(impressions_table.c.newsletter_id.in_([row.newsletter_id for row in newsletter_result]))
        )

        impressions_result = self.conn.execute(impressions_query).fetchall()

        impressions_by_newsletter_id = defaultdict(list)
        for row in impressions_result:
            impressions_by_newsletter_id[row.newsletter_id].append(
                Impression(
                    newsletter_id=row.newsletter_id,
                    position=row.position,
                    article=Article(
                        article_id=row.article_id,
                        headline=row.headline,
                        subhead=row.subhead,
                        url=row.url,
                        preview_image_id=row.preview_image_id,
                        published_at=row.published_at,
                        source=row.source,
                        external_id=row.external_id,
                        raw_data=row.raw_data,
                    ),
                )
            )

        return [
            Newsletter(
                newsletter_id=row.newsletter_id,
                account_id=row.account_id,
                treatment_id=row.treatment_id,
                impressions=impressions_by_newsletter_id[row.newsletter_id],
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


def extract_and_flatten(newsletters: list[Newsletter]) -> list[dict]:
    impression_records = []
    for newsletter in newsletters:
        records = []
        for impression in newsletter.impressions:
            record = {}
            record["account_id"] = str(newsletter.account_id)
            record["newsletter_id"] = str(newsletter.newsletter_id)
            record["article_id"] = str(impression.article.article_id)
            record["position"] = impression.position
            records.append(record)
        impression_records.extend(records)
    return impression_records
