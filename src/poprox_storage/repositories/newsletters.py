from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Connection, Table, and_, insert, null, select

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
                if impression.article.preview_image_id:
                    preview_image_id = str(impression.article.preview_image_id)
                else:
                    preview_image_id = null()

                stmt = insert(impression_table).values(
                    newsletter_id=str(newsletter.newsletter_id),
                    article_id=str(impression.article.article_id),
                    preview_image_id=preview_image_id,
                    position=impression.position,
                    extra=impression.extra,
                    headline=impression.headline,
                    subhead=impression.subhead,
                )
                self.conn.execute(stmt)

    def fetch_newsletters(self, accounts: list[Account]) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        return self._fetch_newsletters(
            newsletters_table,
            impressions_table,
            articles_table,
            newsletters_table.c.account_id.in_([acct.account_id for acct in accounts]),
        )

    def fetch_newsletters_since(self, days_ago=90, accounts: list[Account] | None = None) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        cutoff = datetime.now() - timedelta(days=days_ago)

        where_clause = newsletters_table.c.created_at >= cutoff

        if accounts:
            where_clause = and_(
                where_clause, newsletters_table.c.account_id.in_([acct.account_id for acct in accounts])
            )

        return self._fetch_newsletters(
            newsletters_table,
            impressions_table,
            articles_table,
            where_clause,
        )

    def fetch_newsletters_by_treatment_id(self, expt_treatment_ids: list[UUID]) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        return self._fetch_newsletters(
            newsletters_table,
            impressions_table,
            articles_table,
            newsletters_table.c.treatment_id.in_(expt_treatment_ids),
        )

    def fetch_impressions_by_newsletter_ids(self, newsletter_ids: list[UUID]) -> list[Impression]:
        impressions_table = self.tables["impressions"]

        query = select(
            impressions_table.c.newsletter_id,
            impressions_table.c.article_id,
            impressions_table.c.position,
            impressions_table.c.extra,
            impressions_table.c.headline,
            impressions_table.c.subhead,
        ).where(
            impressions_table.c.newsletter_id.in_(newsletter_ids),
        )
        rows = self.conn.execute(query).fetchall()
        return [
            Impression(
                newsletter_id=row.newsletter_id,
                article_id=row.article_id,
                position=row.position,
                extra=row.extra,
                headline=row.headline,
                subhead=row.subhead,
            )
            for row in rows
        ]

    def fetch_most_recent_newsletter(self, account_id, since: datetime) -> Newsletter | None:
        # XXX - this does not currently fetch impressions due to this feature not being needed.
        newsletters_table = self.tables["newsletters"]

        query = (
            select(newsletters_table)
            .where(and_(newsletters_table.c.account_id == account_id, newsletters_table.c.created_at >= since))
            .order_by(newsletters_table.c.created_at.desc())
            .limit(1)
        )

        row = self.conn.execute(query).fetchone()

        if row is None:
            return None
        return Newsletter(
            newsletter_id=row.newsletter_id,
            account_id=row.account_id,
            treatment_id=row.treatment_id,
            impressions=[],
            subject=row.email_subject,
            body_html=row.html,
            created_at=row.created_at,
        )

    def _fetch_newsletters(self, newsletters_table, impressions_table, articles_table, where_clause=None):
        newsletter_query = select(newsletters_table)

        if where_clause is not None:
            newsletter_query = newsletter_query.where(where_clause)

        newsletter_result = self.conn.execute(newsletter_query).fetchall()

        impressions_query = (
            select(
                impressions_table.c.newsletter_id,
                impressions_table.c.preview_image_id,
                impressions_table.c.position,
                impressions_table.c.extra,
                articles_table,
            )
            .join(
                impressions_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(impressions_table.c.newsletter_id.in_([row.newsletter_id for row in newsletter_result]))
        )

        impressions_result = self.conn.execute(impressions_query).fetchall()
        return self._convert_to_newsletter_objs(newsletter_result, impressions_result)

    def _convert_to_newsletter_objs(self, newsletter_result, impressions_result):
        impressions_by_newsletter_id = defaultdict(list)
        for row in impressions_result:
            impressions_by_newsletter_id[row.newsletter_id].append(self._convert_to_impression_obj(row))

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

    def _convert_to_impression_obj(self, row):
        return Impression(
            newsletter_id=row.newsletter_id,
            preview_image_id=row.preview_image_id,
            position=row.position,
            extra=row.extra,
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


class S3NewsletterRepository(S3Repository):
    def store_as_parquet(
        self,
        newsletters: list[Newsletter],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ) -> str:
        records = extract_and_flatten(newsletters)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


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
            record["created_at"] = newsletter.created_at
            record["extra"] = impression.extra
            records.append(record)
        impression_records.extend(records)
    return impression_records
