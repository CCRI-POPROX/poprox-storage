from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import Connection, Table, and_, select

from poprox_concepts.domain import Account, Article, Impression, Newsletter
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbDatasetRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "account_aliases",
            "datasets",
            "experiments",
            "expt_assignments",
            "expt_groups",
            "teams",
            "newsletters",
            "impressions",
            "articles",
        )

    def store_new_dataset(self, accounts: list[Account], team_id: UUID) -> UUID:
        dataset_id = self._insert_dataset(team_id)

        for account in accounts:
            self._insert_account_alias(dataset_id, account)

        return dataset_id

    def fetch_dataset_id_by_assignment(self, assignment_id: UUID) -> UUID:
        dataset_table = self.tables["datasets"]
        experiment_table = self.tables["experiments"]
        group_table = self.tables["expt_groups"]
        assignment_table = self.tables["expt_assignments"]
        query = (
            select(dataset_table.c.dataset_id)
            .join(
                experiment_table,
                dataset_table.c.dataset_id == experiment_table.c.dataset_id,
            )
            .join(
                group_table,
                group_table.c.experiment_id == experiment_table.c.experiment_id,
            )
            .join(assignment_table, assignment_table.c.group_id == group_table.c.group_id)
            .where(assignment_table.c.assignment_id == assignment_id)
        )

        return self._id_query(query)[0]

    def fetch_account_alias(self, dataset_id, account_id) -> UUID:
        alias_table = self.tables["account_aliases"]
        query = select(alias_table.c.alias_id).where(
            and_(
                alias_table.c.account_id == account_id,
                alias_table.c.dataset_id == dataset_id,
            )
        )
        return self._id_query(query)[0]

    def fetch_account_aliases(self, dataset_id: UUID) -> dict[UUID, UUID]:
        alias_table = self.tables["account_aliases"]
        query = select(alias_table.c.account_id, alias_table.c.alias_id).where(alias_table.c.dataset_id == dataset_id)
        rows = self.conn.execute(query).fetchall()
        return {row.account_id: row.alias_id for row in rows}

    def fetch_newsletter_impressions(self, newsletter_ids: list[UUID]) -> list[Impression]:
        """
        Fetch impressions for a list of newsletters.
        """
        if not newsletter_ids:
            return []

        impressions_table = self.tables["impressions"]
        articles_table = self.tables["articles"]

        query = (
            select(
                impressions_table.c.impression_id,
                impressions_table.c.preview_image_id,
                impressions_table.c.position,
                impressions_table.c.extra,
                articles_table.c.article_id,
                articles_table.c.headline,
                articles_table.c.subhead,
                articles_table.c.url,
                articles_table.c.published_at,
                articles_table.c.created_at,
                articles_table.c.source,
                articles_table.c.external_id,
                articles_table.c.preview_image_id,
                articles_table.c.body,
            )
            .join(articles_table, articles_table.c.article_id == impressions_table.c.article_id)
            .where(impressions_table.c.newsletter_id.in_(newsletter_ids))
        )

        result = self.conn.execute(query).fetchall()

        impressions = [self._convert_to_impression_obj(row) for row in result]

        return impressions

    def fetch_newsletters(self, dataset_id: UUID, start: datetime, end: datetime) -> list[Newsletter]:
        """
        This function does not fetch impressions, see `fetch_newsletter_impressions`
        for fetching impressions seperately.
        """

        newsletters_table = self.tables["newsletters"]
        alias_table = self.tables["account_aliases"]

        query = (
            select(
                alias_table.c.account_id,
                newsletters_table.c.newsletter_id,
                newsletters_table.c.treatment_id,
                newsletters_table.c.html,
                newsletters_table.c.email_subject,
                newsletters_table.c.created_at,
            )
            .join(newsletters_table, alias_table.c.account_id == newsletters_table.c.account_id)
            .where(
                and_(
                    alias_table.c.dataset_id == dataset_id,
                    newsletters_table.c.created_at >= start,
                    newsletters_table.c.created_at <= end,
                )
            )
        )

        result = self.conn.execute(query).fetchall()

        return [
            Newsletter(
                newsletter_id=row.newsletter_id,
                account_id=row.account_id,
                treatment_id=row.treatment_id,
                impressions=[],
                subject=row.email_subject,
                body_html=row.html,
                created_at=row.created_at,
            )
            for row in result
        ]

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
            impression_id=row.impression_id,
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
            ),
        )

    def _insert_dataset(self, team_id: UUID) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["datasets"],
            {"team_id": team_id},
            commit=False,
        )

    def _insert_account_alias(self, dataset_id: UUID, account: Account) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["account_aliases"],
            values={
                "dataset_id": dataset_id,
                "account_id": account.account_id,
            },
            commit=False,
        )
