import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

import sqlalchemy
from sqlalchemy import (
    and_,
    null,
    or_,
    select,
    Connection,
)

from poprox_concepts import Account
from poprox_storage.repositories.data_stores.db import DatabaseRepository


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbAccountRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "accounts",
            "expt_allocations",
            "expt_phases",
            "expt_treatments",
            "subscriptions",
        )

    def fetch_accounts(self, account_ids: Optional[List[UUID]] = None) -> List[Account]:
        account_tbl = self.tables["accounts"]

        query = select(account_tbl.c.account_id, account_tbl.c.email)
        if account_ids is None:
            query = query.where(account_tbl.c.account_id.in_(account_ids))
        elif len(account_ids) == 0:
            return []
        result = self.conn.execute(query).fetchall()

        return [Account(account_id=rec[0], email=rec[1]) for rec in result]

    def fetch_account_by_email(self, email: str) -> Optional[Account]:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(account_tbl.c.account_id, account_tbl.c.email).where(
            account_tbl.c.email == email
        )
        result = self.conn.execute(query).fetchall()
        accounts = [Account(account_id=row[0], email=row[1]) for row in result]
        if len(accounts) > 0:
            return accounts[0]
        return None

    def create_new_account(self, email: str) -> Account:
        account_tbl = self.tables["accounts"]
        query = (
            sqlalchemy.insert(account_tbl)
            .values(email=email)
            .returning(account_tbl.c.account_id, account_tbl.c.email)
        )
        row = self.conn.execute(query).one_or_none()
        return Account(account_id=row.account_id, email=row.email)

    def fetch_unassigned_accounts(self, start_date: date, end_date: date):
        account_tbl = self.tables["accounts"]
        allocation_tbl = self.tables["expt_allocations"]
        phase_tbl = self.tables["expt_phases"]
        treatment_tbl = self.tables["expt_treatments"]

        # Find the experiment phases that are active during the date window
        where_clause = or_(
            # Phase's start date is in the supplied range
            and_(
                phase_tbl.c.start_date > start_date,
                phase_tbl.c.start_date < end_date,
            ),
            # Phase's end date is in the supplied range
            and_(phase_tbl.c.end_date > start_date, phase_tbl.c.end_date < end_date),
            # Phase's dates cover the whole supplied range
            and_(phase_tbl.c.start_date < start_date, phase_tbl.c.end_date > end_date),
            # The supplied range covers the whole phase
            and_(phase_tbl.c.start_date > start_date, phase_tbl.c.end_date < end_date),
        )
        phase_query = select(phase_tbl.c.phase_id).where(where_clause)
        phase_ids = self._id_query(phase_query)

        # Find the experiment groups connected to those phases
        group_query = select(treatment_tbl.c.group_id).where(
            treatment_tbl.c.phase_id.in_(phase_ids)
        )
        group_ids = self._id_query(group_query)

        # Find the users allocated to those groups
        allocation_query = select(allocation_tbl.c.account_id).where(
            allocation_tbl.c.group_id.in_(group_ids)
        )
        allocation_account_ids = self._id_query(allocation_query)

        # Find all the users who aren't in the allocations above
        account_query = select(account_tbl.c.account_id).where(
            account_tbl.c.account_id.not_in(allocation_account_ids)
        )
        account_ids = self._id_query(account_query)

        return self.fetch_accounts(account_ids)

    def fetch_subscribed_accounts(self) -> List[Account]:
        subscription_tbl = self.tables["subscriptions"]

        account_query = select(subscription_tbl.c.account_id).where(
            subscription_tbl.c.ended == null()
        )
        account_ids = self._id_query(account_query)
        return self.fetch_accounts(account_ids)

    def fetch_subscription_for_account(self, account_id: UUID) -> Optional[UUID]:
        subscription_tbl = self.tables["subscriptions"]
        query = subscription_tbl.select().where(
            subscription_tbl.c.account_id == account_id,
            subscription_tbl.c.ended == null(),
        )
        result = self.conn.execute(query).one_or_none()
        if result:
            result = result.subscription_id
        return result

    def create_subscription_for_account(self, account_id: UUID):
        subscription_tbl = self.tables["subscriptions"]

        create_query = subscription_tbl.insert().values(account_id=account_id)
        if self.fetch_subscription_for_account(account_id) is None:
            self.conn.execute(create_query)

    def end_subscription_for_account(self, account_id: UUID):
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
