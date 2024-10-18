import json
import logging
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, insert, select

from poprox_concepts import Account, Click
from poprox_storage.aws import s3
from poprox_storage.aws.exceptions import PoproxAwsUtilitiesException
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3ClicksRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)

    def fetch_clicks_from_dev_file(self, file_key):
        try:
            click_data = json.loads(s3.get_object(self.bucket_name, file_key).get("Body").read())
        except PoproxAwsUtilitiesException:
            logger.warning("No click log data found. Just going to go with random recommendations")
            click_data = {}

        return click_data

    def store_as_parquet(
        self,
        clicks: list[Click],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = extract_and_flatten(clicks)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


class DbClicksRepository(DatabaseRepository):
    def __init__(self, connection):
        super().__init__(connection)
        self.tables = self._load_tables("clicks")

    def store_click(self, newsletter_id, account_id, article_id, headers=None, created_at=None):
        click_table = self.tables["clicks"]
        with self.conn.begin():
            stmt = insert(click_table).values(
                newsletter_id=newsletter_id,
                account_id=account_id,
                article_id=article_id,
                headers=headers,
            )
            if created_at:
                stmt = stmt.values(created_at=created_at)
            self.conn.execute(stmt)

    def fetch_clicks(self, accounts: list[Account]) -> dict[UUID, list[Click]]:
        click_table = self.tables["clicks"]

        click_query = select(
            click_table.c.account_id,
            click_table.c.article_id,
            click_table.c.newsletter_id,
            click_table.c.created_at,
        ).where(click_table.c.account_id.in_([acct.account_id for acct in accounts]))
        click_result = self.conn.execute(click_query).fetchall()

        clicked_articles = defaultdict(list)
        for row in click_result:
            clicked_articles[row.account_id].append(
                Click(
                    article_id=row.article_id,
                    newsletter_id=row.newsletter_id,
                    timestamp=row.created_at,
                )
            )

        for account in accounts:
            account_id = account.account_id
            if account_id not in clicked_articles:
                clicked_articles[account_id] = []

        return clicked_articles

    def fetch_clicks_between(self, accounts: list[Account], start_time, end_time) -> dict[UUID, list[Click]]:
        click_table = self.tables["clicks"]

        click_query = select(
            click_table.c.account_id,
            click_table.c.article_id,
            click_table.c.newsletter_id,
            click_table.c.created_at,
        ).where(
            and_(
                click_table.c.account_id.in_([acct.account_id for acct in accounts]),
                click_table.c.created_at >= start_time,
                click_table.c.created_at <= end_time,
            )
        )
        click_result = self.conn.execute(click_query).fetchall()

        clicked_articles = defaultdict(list)
        for row in click_result:
            clicked_articles[row.account_id].append(
                Click(
                    article_id=row.article_id,
                    newsletter_id=row.newsletter_id,
                    timestamp=row.created_at,
                )
            )

        for account in accounts:
            account_id = account.account_id
            if account_id not in clicked_articles:
                clicked_articles[account_id] = []

        return clicked_articles

    def fetch_clicks_by_newsletter_ids(self, newsletter_ids: list[UUID]) -> list[Click]:
        click_table = self.tables["clicks"]

        click_query = select(click_table).where(click_table.c.newsletter_id.in_(newsletter_ids))
        result = self.conn.execute(click_query).fetchall()

        return [
            Click(
                article_id=row.article_id,
                newsletter_id=row.newsletter_id,
                timestamp=row.created_at,
            )
            for row in result
        ]


def extract_and_flatten(clicks: list[Click]) -> list[dict]:
    def flatten(click: Click):
        row = {}
        row["newsletter_id"] = str(click.newsletter_id)
        row["article_id"] = str(click.article_id)
        row["timestamp"] = click.timestamp
        return row

    final_list = []
    for click in clicks:
        final_list.append(flatten(click))

    return final_list
