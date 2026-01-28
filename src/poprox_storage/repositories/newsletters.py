from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID, uuid4

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
from poprox_concepts.domain.newsletter import ImpressedSection
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbNewsletterRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "newsletters",
            "impressions",
            "articles",
            "section_types",
            "impressed_sections",
        )

    def renumber_impressions(self, newsletter: Newsletter):
        section_num = 0
        newsletter_impression_num = 0

        # sort by position -- note, list.sort is stable -- so this shouldn't change order if no positions are sent.
        newsletter.sections.sort(key=lambda x: x.position if x.position is not None else 0)
        for section in newsletter.sections:
            section_num += 1
            section.position = section_num

            section_impression_num = 0

            # sort by position -- note, list.sort is stable -- so this shouldn't change order if no positions are sent.
            section.impressions.sort(key=lambda x: x.position_in_section if x.position_in_section is not None else 0)
            for impression in section.impressions:
                section_impression_num += 1
                newsletter_impression_num += 1
                impression.position_in_section = section_impression_num
                impression.position = newsletter_impression_num

    def store_newsletter(self, newsletter: Newsletter):
        newsletter_table = self.tables["newsletters"]

        self.renumber_impressions(newsletter)

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

            for position, section in enumerate(newsletter.sections):
                self._store_section(newsletter, section, position + 1)

    def _store_section(self, newsletter: Newsletter, section: ImpressedSection, position):
        impressed_sections_table = self.tables["impressed_sections"]
        section_id = section.section_id
        if section_id is None:
            section_id = uuid4()
            section.section_id = section_id

        section_type_id = self._get_section_type(section)
        stmt = insert(impressed_sections_table).values(
            section_id=section_id,
            section_type_id=section_type_id,
            newsletter_id=newsletter.newsletter_id,
            position=position,
        )
        self.conn.execute(stmt)

        for impression in section.impressions:
            self._store_impression(newsletter, section, impression)

    def _store_impression(self, newsletter: Newsletter, section: ImpressedSection, impression: Impression):
        impression_table = self.tables["impressions"]

        if impression.preview_image_id:
            preview_image_id = str(impression.preview_image_id)
        else:
            preview_image_id = null()

        stmt = insert(impression_table).values(
            impression_id=str(impression.impression_id),
            newsletter_id=str(newsletter.newsletter_id),
            impressed_section_id=str(section.section_id),
            article_id=str(impression.article.article_id),
            preview_image_id=preview_image_id,
            position=impression.position,
            extra=impression.extra,
            headline=impression.headline,
            subhead=impression.subhead,
            position_in_section=impression.position_in_section,
        )
        self.conn.execute(stmt)

    def _get_section_type(self, section: ImpressedSection) -> UUID:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["section_types"],
            {
                "flavor": section.flavor,
                "seed": section.seed_entity_id,
                "personalized": section.personalized,
                "title": section.title,
            },
            "uq_section_types",
            commit=False,
        )

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
        section_types_table = self.tables["section_types"]
        impressed_sections_table = self.tables["impressed_sections"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        return self._fetch_newsletters(
            newsletters_table,
            section_types_table,
            impressed_sections_table,
            impressions_table,
            articles_table,
            newsletters_table.c.account_id.in_([acct.account_id for acct in accounts]),
            excluded_columns=["content", "html"],
        )

    def fetch_newsletters_between(
        self, start_date: datetime, end_date: datetime, accounts: list[Account] | None = None
    ) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        section_types_table = self.tables["section_types"]
        impressed_sections_table = self.tables["impressed_sections"]
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
            section_types_table,
            impressed_sections_table,
            impressions_table,
            articles_table,
            where_clause,
            excluded_columns=["content", "html"],
        )

    def fetch_newsletters_since(self, days_ago=90, accounts: list[Account] | None = None) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        section_types_table = self.tables["section_types"]
        impressed_sections_table = self.tables["impressed_sections"]
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
            section_types_table,
            impressed_sections_table,
            impressions_table,
            articles_table,
            where_clause,
            excluded_columns=["content", "html"],
        )

    def fetch_newsletters_by_treatment_id(self, expt_treatment_ids: list[UUID]) -> list[Newsletter]:
        newsletters_table = self.tables["newsletters"]
        section_types_table = self.tables["section_types"]
        impressed_sections_table = self.tables["impressed_sections"]
        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        return self._fetch_newsletters(
            newsletters_table,
            section_types_table,
            impressed_sections_table,
            impressions_table,
            articles_table,
            newsletters_table.c.treatment_id.in_(expt_treatment_ids),
            excluded_columns=["content", "html"],
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
        # XXX - this does not currently fetch sections/impressions due to this feature not being needed.
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
            sections=[],
            subject=row.email_subject,
            body_html=row.html,
            created_at=row.created_at,
            recommender_info=RecommenderInfo(
                name=row.recommender_name,
                version=row.recommender_version,
                hash=row.recommender_hash,
            ),
        )

    def _fetch_newsletters(
        self,
        newsletters_table,
        section_types_table,
        impressed_sections_table,
        impressions_table,
        articles_table,
        where_clause=None,
        excluded_columns=None,
    ):
        excluded_columns = excluded_columns or []

        columns_to_select = [col for col in newsletters_table.columns if col.name not in excluded_columns]

        newsletter_query = select(*columns_to_select).select_from(newsletters_table)

        if where_clause is not None:
            newsletter_query = newsletter_query.where(where_clause)

        newsletter_result = self.conn.execute(newsletter_query).fetchall()

        sections_query = (
            select(
                impressed_sections_table,
                section_types_table.c.flavor,
                section_types_table.c.seed,
                section_types_table.c.personalized,
                section_types_table.c.title,
            )
            .join(
                section_types_table,
                impressed_sections_table.c.section_type_id == section_types_table.c.section_type_id,
            )
            .join(newsletters_table, impressed_sections_table.c.newsletter_id == newsletters_table.c.newsletter_id)
            .order_by(impressed_sections_table.c.position)
        )

        if where_clause is not None:
            sections_query = sections_query.where(where_clause)
        sections_result = self.conn.execute(sections_query).fetchall()

        impressions_query = (
            self.select_impressions_with_articles(impressions_table, articles_table)
            .join(
                impressions_table,
                articles_table.c.article_id == impressions_table.c.article_id,
            )
            .where(impressions_table.c.newsletter_id.in_([row.newsletter_id for row in newsletter_result]))
        )

        impressions_result = self.conn.execute(impressions_query).fetchall()
        return self._convert_to_newsletter_objs(newsletter_result, sections_result, impressions_result)

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

    def _convert_to_newsletter_objs(self, newsletter_result, sections_result, impressions_result):
        impressions_by_section_id = defaultdict(list)
        for row in impressions_result:
            impressions_by_section_id[row.impressed_section_id].append(self._convert_to_impression_obj(row))

        sections_by_newsletter = defaultdict(list)
        for row in sections_result:
            sections_by_newsletter[row.newsletter_id].append(
                ImpressedSection(
                    section_id=row.section_id,
                    title=row.title,
                    flavor=row.flavor,
                    personalized=row.personalized,
                    seed_entity_id=row.seed,
                    position=row.position,
                    impressions=sorted(impressions_by_section_id[row.section_id], key=lambda x: x.position),
                )
            )

        return [
            Newsletter(
                newsletter_id=row.newsletter_id,
                account_id=row.account_id,
                treatment_id=row.treatment_id,
                sections=sorted(sections_by_newsletter[row.newsletter_id], key=lambda x: x.position),
                subject=row.email_subject,
                body_html=row.html if hasattr(row, "html") else "",
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
        for section in newsletter.sections:
            for impression in newsletter.impressions:
                record = {}
                #--------------------newsletter items--------------------
                record["account_id"] = str(newsletter.account_id)
                record["newsletter_id"] = str(newsletter.newsletter_id)
                record["created_at"] = newsletter.created_at
                record["newsletter_feedback"] = str(newsletter.feedback)

                if include_treatment:
                    record["treatment_id"] = str(newsletter.treatment_id)
                if newsletter.recommender_info:
                    record["recommender_name"] = newsletter.recommender_info.name or ""
                    record["recommender_version"] = newsletter.recommender_info.version or ""
                    record["recommender_hash"] = newsletter.recommender_info.hash or ""

                #--------------------section items--------------------
                record["section_id"] = str(section.section_id) if section.section_id else ""
                record["section_title"] = section.title or ""
                record["section_flavor"] = section.flavor or ""
                record["section_personalized"] = section.personalized
                record["section_seed_entity_id"] = (
                    str(section.seed_entity_id) if section.seed_entity_id else ""
                )
                record["section_position"] = section.position

                #--------------------impression items--------------------
                record["article_id"] = str(impression.article.article_id)
                record["headline"] = impression.headline
                record["subhead"] = impression.subhead
                record["article_preview_image_id"] = (
                    str(impression.preview_image_id)
                    if impression.preview_image_id
                    else ""
                )
                record["position"] = impression.position
                record["impression_feedback"] = str(impression.feedback)

                if impression.extra:
                    for k, v in impression.extra.items():
                        record[str(k)] = v
                impression_records.append(record)
    return impression_records