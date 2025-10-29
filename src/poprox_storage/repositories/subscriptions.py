import logging
from datetime import datetime, timedelta
from uuid import UUID

import sqlalchemy
from sqlalchemy import (
    Connection,
    and_,
    null,
    or_,
    select,
)

from poprox_concepts.domain import Subscription
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbSubscriptionRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables("subscriptions")

    def store_subscription_for_account(self, account_id: UUID):
        subscription_tbl = self.tables["subscriptions"]

        create_query = subscription_tbl.insert().values(account_id=account_id)
        if self.fetch_subscription_for_account(account_id) is None:
            self.conn.execute(create_query)

    def remove_subscription_for_account(self, account_id: UUID):
        subscription_tbl = self.tables["subscriptions"]
        delete_query = (
            subscription_tbl.update()
            .where(
                subscription_tbl.c.account_id == account_id,
                subscription_tbl.c.ended == null(),
            )
            .values(ended=sqlalchemy.text("NOW()"))
        )
        self.conn.execute(delete_query)

    def fetch_subscriber_account_ids(self) -> list[UUID]:
        subscription_tbl = self.tables["subscriptions"]

        account_query = select(subscription_tbl.c.account_id).where(subscription_tbl.c.ended == null())
        account_ids = self._id_query(account_query)
        return account_ids

    def fetch_subscribed_accounts_since(self, days_ago=1) -> list[UUID]:
        subscription_tbl = self.tables["subscriptions"]

        cutoff = datetime.now() - timedelta(days=days_ago)

        account_query = select(subscription_tbl.c.account_id).where(
            or_(subscription_tbl.c.ended == null(), subscription_tbl.c.ended >= cutoff)
        )
        account_ids = self._id_query(account_query)
        return account_ids

    def fetch_subscribed_accounts_between(self, start_date, end_date) -> list[UUID]:
        subscription_tbl = self.tables["subscriptions"]

        account_query = select(subscription_tbl.c.account_id).where(
            and_(
                subscription_tbl.c.started <= end_date,
                or_(subscription_tbl.c.ended >= start_date, subscription_tbl.c.ended == null()),
            )
        )
        account_ids = self._id_query(account_query)
        return account_ids

    # TODO: Update this to return a Subscription
    def fetch_subscription_for_account(self, account_id: UUID) -> UUID | None:
        subscription_tbl = self.tables["subscriptions"]
        query = subscription_tbl.select().where(
            subscription_tbl.c.account_id == account_id,
            subscription_tbl.c.ended == null(),
        )
        result = self.conn.execute(query).one_or_none()
        if result:
            result = result.subscription_id
        return result

    def fetch_subscriptions_by_account_ids(self, account_ids: list[UUID]) -> list[Subscription]:
        subscription_tbl = self.tables["subscriptions"]
        query = subscription_tbl.select().where(subscription_tbl.c.account_id.in_(account_ids))
        results = self.conn.execute(query).fetchall()
        return [
            Subscription(
                subscription_id=row.subscription_id, account_id=row.account_id, started=row.started, ended=row.ended
            )
            for row in results
        ]
