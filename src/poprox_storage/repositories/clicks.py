import json
import logging
from collections import defaultdict
from uuid import UUID

from poprox_concepts import Account, ClickHistory
from poprox_concepts.domain.click import Click
from sqlalchemy import insert, select, and_

from poprox_storage.aws import s3
from poprox_storage.aws.exceptions import PoproxAwsUtilitiesException
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3ClicksRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)

    def get_clicks_from_dev_file(self, file_key):
        try:
            click_data = json.loads(s3.get_object(self.bucket_name, file_key).get("Body").read())
        except PoproxAwsUtilitiesException:
            logger.warning("No click log data found. Just going to go with random recommendations")
            click_data = {}

        return click_data


class DbClicksRepository(DatabaseRepository):
    def __init__(self, connection):
        super().__init__(connection)
        self.tables = self._load_tables("clicks")

    def track_click_in_database(self, newsletter_id, account_id, article_id, created_at):
        click_table = self.tables["clicks"]
        with self.conn.begin():
            stmt = insert(click_table).values(
                newsletter_id=newsletter_id,
                account_id=account_id,
                article_id=article_id,
                created_at=created_at
            )
            self.conn.execute(stmt)

    def get_clicks(self, accounts: list[Account]) -> dict[UUID, ClickHistory]:
        click_table = self.tables["clicks"]

        click_query = select(click_table.c.account_id, click_table.c.article_id).where(
            click_table.c.account_id.in_([acct.account_id for acct in accounts])
        )
        click_result = self.conn.execute(click_query).fetchall()

        clicked_articles = defaultdict(list)
        for row in click_result:
            clicked_articles[row[0]].append(row[1])

        for account in accounts:
            account_id = account.account_id
            if account_id not in clicked_articles:
                clicked_articles[account_id] = []

        histories = {}
        for account_id, user_clicks in clicked_articles.items():
            histories[account_id] = ClickHistory(article_ids=user_clicks)

        return histories

    def get_clicks_between(self, accounts: list[Account], start_time, end_time) -> dict[UUID, list[Click]]:
        click_table = self.tables["clicks"]

        click_query = select(click_table.c.account_id, click_table.c.article_id, click_table.c.created_at).where(
            and_(
                click_table.c.account_id.in_([acct.account_id for acct in accounts]),
                click_table.c.created_at >= start_time,
                click_table.c.created_at <= end_time
            )
        )
        click_result = self.conn.execute(click_query).fetchall()

        clicked_articles = defaultdict(list)
        for row in click_result:
            clicked_articles[row.account_id].append(Click(article_id=row.article_id, timestamp=row.created_at))
        
        for account in accounts:
            account_id = account.account_id
            if account_id not in clicked_articles:
                clicked_articles[account_id] = []
        
        histories = {}
        for account_id, user_clicks in clicked_articles.items():
            histories[account_id] = user_clicks

        return histories
