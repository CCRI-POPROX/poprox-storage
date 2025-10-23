from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import (
    Connection,
    Table,
    and_,
    insert,
    null,
    select,
    update,
)

from poprox_concepts.domain import Account, Article, Impression, Newsletter, RecommenderInfo
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
                experience_id=str(newsletter.experience_id) if newsletter.experience_id else None,
                content=[rec.model_dump_json() for rec in newsletter.articles],
                email_subject=newsletter.subject,
                html=newsletter.body_html,
                recommender_name=newsletter.recommender_info.name if newsletter.recommender_info else None,
                recommender_version=newsletter.recommender_info.version if newsletter.recommender_info else None,
                recommender_hash=newsletter.recommender_info.hash if newsletter.recommender_info else None,
            )
            self.conn.execute(stmt)

            for impression in newsletter.impressions:
                if impression.preview_image_id:
                    preview_image_id = str(impression.preview_image_id)
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
                    section_name=impression.section_name,
                    position_in_section=impression.position_in_section,
                )
                self.conn.execute(stmt)

    def store_newsletter_feedback(self, account_id: UUID, newsletter_id: UUID, feedback: str | None):
        newsletter_table = self.tables["newsletters"]

        stmt = (
            update(newsletter_table)
            .where(and_(newsletter_table.c.newsletter_id == newsletter_id, newsletter_table.c.account_id == account_id))
            .values(
                feedback=feedback,
            )
        )
        self.conn.execute(stmt)

    def store_impression_feedback(self, impression_id: UUID, is_positive: bool | None):
        impressions_table = self.tables["impressions"]

        stmt = (
            update(impressions_table)
            .where(
                impressions_table.c.impression_id == impression_id,
            )
            .values(
                feedback=is_positive,
            )
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

    def fetch_newsletters_between(
        self, start_date: datetime, end_date: datetime, accounts: list[Account] | None = None
    ) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        where_clause = and_(
            newsletters_table.c.created_at >= start_date,
            newsletters_table.c.created_at <= end_date,
        )

        if accounts:
            account_ids = [a.account_id for a in accounts]
            where_clause = and_(where_clause, newsletters_table.c.account_id.in_(account_ids))

        return self._fetch_newsletters(
            newsletters_table,
            impressions_table,
            articles_table,
            where_clause,
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
        articles_table = self.tables["articles"]

        query = (
            self.select_impressions_with_articles(impressions_table, articles_table)
            .join(
                articles_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(
                impressions_table.c.newsletter_id.in_(newsletter_ids),
            )
            .order_by(impressions_table.c.position.asc())
        )
        rows = self.conn.execute(query).fetchall()
        return [self._convert_to_impression_obj(row) for row in rows]

    def fetch_feedback_impressions_by_account_id(self, account_id: UUID) -> list[Impression]:
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]
        newsletters_table = self.tables["newsletters"]

        query = (
            self.select_impressions_with_articles(impressions_table, articles_table)
            .join(
                newsletters_table,
                newsletters_table.c.newsletter_id == impressions_table.c.newsletter_id,
            )
            .join(
                articles_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(
                and_(
                    newsletters_table.c.account_id == account_id,
                    impressions_table.c.feedback.isnot(None),
                )
            )
        )
        rows = self.conn.execute(query).fetchall()

        impressions = [self._convert_to_impression_obj(row) for row in rows]
        return sorted(impressions, key=lambda i: i.created_at)

    def fetch_most_recent_newsletter(self, account_id, since: datetime, exclude_experiences=True) -> Newsletter | None:
        # XXX - this does not currently fetch impressions due to this feature not being needed.
        newsletters_table = self.tables["newsletters"]

        clauses = [newsletters_table.c.account_id == account_id, newsletters_table.c.created_at >= since]
        if exclude_experiences:
            clauses.append(newsletters_table.c.experience_id.is_(None))

        query = select(newsletters_table).where(and_(*clauses)).order_by(newsletters_table.c.created_at.desc()).limit(1)

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
            recommender_info=RecommenderInfo(
                name=row.recommender_name,
                version=row.recommender_version,
                hash=row.recommender_hash,
            ),
        )

    def _fetch_newsletters(self, newsletters_table, impressions_table, articles_table, where_clause=None):
        newsletter_query = select(newsletters_table)

        if where_clause is not None:
            newsletter_query = newsletter_query.where(where_clause)

        newsletter_result = self.conn.execute(newsletter_query).fetchall()

        impressions_query = (
            self.select_impressions_with_articles(impressions_table, articles_table)
            .join(
                impressions_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(impressions_table.c.newsletter_id.in_([row.newsletter_id for row in newsletter_result]))
        )

        impressions_result = self.conn.execute(impressions_query).fetchall()
        return self._convert_to_newsletter_objs(newsletter_result, impressions_result)

    def select_impressions_with_articles(self, impressions_table, articles_table):
        return select(
            impressions_table,
            articles_table.c.article_id,
            articles_table.c.external_id,
            articles_table.c.headline,
            articles_table.c.subhead,
            articles_table.c.body,
            articles_table.c.url,
            articles_table.c.source,
            articles_table.c.published_at,
            articles_table.c.preview_image_id,
        )

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
                recommender_info=RecommenderInfo(
                    name=row.recommender_name,
                    version=row.recommender_version,
                    hash=row.recommender_hash,
                ),
            )
            for row in newsletter_result
        ]

    def _convert_to_impression_obj(self, row):
        return Impression(
            impression_id=row.impression_id,
            newsletter_id=row.newsletter_id,
            headline=row.headline,
            subhead=row.subhead,
            position=row.position,
            extra=getattr(row, "extra", None),
            feedback=row.feedback,
            article=Article(
                article_id=row.articles_article_id,
                headline=row.articles_headline,
                subhead=row.articles_subhead,
                url=row.articles_url,
                preview_image_id=row.articles_preview_image_id,
                published_at=row.articles_published_at,
                source=row.articles_source,
                external_id=row.articles_external_id,
            ),
            created_at=row.created_at,
            section_name=row.section_name,
            position_in_section=row.position_in_section,
        )


class S3NewsletterRepository(S3Repository):
    def store_as_parquet(
        self,
        newsletters: list[Newsletter],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
        include_treatment: bool = False,
    ) -> str:
        records = extract_and_flatten(newsletters, include_treatment=include_treatment)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def extract_and_flatten(newsletters: list[Newsletter], include_treatment: bool = False) -> list[dict]:
    impression_records = []
    for newsletter in newsletters:
        records = []
        for impression in newsletter.impressions:
            record = {}
            record["profile_id"] = str(newsletter.account_id)
            record["newsletter_id"] = str(newsletter.newsletter_id)
            record["article_id"] = str(impression.article.article_id)
            record["position"] = impression.position
            record["created_at"] = newsletter.created_at
            record["headline"] = impression.headline
            record["subhead"] = impression.subhead
            record["recommender_name"] = newsletter.recommender_info.name if newsletter.recommender_info else ""
            record["recommender_version"] = newsletter.recommender_info.version if newsletter.recommender_info else ""
            record["recommender_hash"] = newsletter.recommender_info.hash if newsletter.recommender_info else ""
            if include_treatment:
                record["treatment_id"] = str(newsletter.treatment_id)
            if impression.extra:
                for k, v in impression.extra.items():
                    record[str(k)] = v
            records.append(record)
        impression_records.extend(records)
    return impression_records
