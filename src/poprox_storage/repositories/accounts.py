import logging
from datetime import date
from uuid import UUID

import sqlalchemy
from sqlalchemy import (
    Connection,
    and_,
    null,
    or_,
    select,
)

from poprox_concepts import Account
from poprox_concepts.api.tracking import LoginLinkData
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbAccountRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "accounts",
            "expt_assignments",
            "expt_phases",
            "expt_treatments",
            "subscriptions",
            "account_consent_log",
            "web_logins",
        )

    def fetch_accounts(self, account_ids: list[UUID] | None = None) -> list[Account]:
        account_tbl = self.tables["accounts"]

        query = select(
            account_tbl.c.account_id,
            account_tbl.c.email,
            account_tbl.c.status,
            account_tbl.c.source,
        )
        if account_ids is not None:
            query = query.where(account_tbl.c.account_id.in_(account_ids))
        elif len(account_ids) == 0:
            return []
        result = self.conn.execute(query).fetchall()

        return [
            Account(
                account_id=row.account_id,
                email=row.email,
                status=row.status,
                source=row.source,
            )
            for row in result
        ]

    def fetch_account_by_email(self, email: str) -> Account | None:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(
            account_tbl.c.account_id,
            account_tbl.c.email,
            account_tbl.c.status,
            account_tbl.c.source,
        ).where(account_tbl.c.email == email)
        result = self.conn.execute(query).fetchall()
        accounts = [
            Account(
                account_id=row.account_id,
                email=row.email,
                status=row.status,
                source=row.source,
            )
            for row in result
        ]
        if len(accounts) > 0:
            return accounts[0]
        return None

    def store_account(self, account: Account) -> UUID | None:
        account_tbl = self.tables["accounts"]
        query = (
            sqlalchemy.insert(account_tbl)
            .values(
                account_id=account.account_id,
                email=account.email,
                source=account.source,
                status="new_account",
            )
            .returning(account_tbl.c.account_id)
        )
        row = self.conn.execute(query).one_or_none()
        return row.account_id

    def store_new_account(self, email: str, source: str) -> Account:
        account_tbl = self.tables["accounts"]
        query = (
            sqlalchemy.insert(account_tbl)
            .values(email=email, source=source, status="new_account")
            .returning(account_tbl.c.account_id, account_tbl.c.email, account_tbl.c.status)
        )
        row = self.conn.execute(query).one_or_none()
        return Account(account_id=row.account_id, email=row.email, status=row.status, source=source)

    def fetch_unassigned_accounts(self, start_date: date, end_date: date):
        account_tbl = self.tables["accounts"]
        assignment_tbl = self.tables["expt_assignments"]
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
        group_query = select(treatment_tbl.c.group_id).where(treatment_tbl.c.phase_id.in_(phase_ids))
        group_ids = self._id_query(group_query)

        # Find the users allocated to those groups
        assignment_query = select(assignment_tbl.c.account_id).where(assignment_tbl.c.group_id.in_(group_ids))
        assignment_account_ids = self._id_query(assignment_query)

        # Find all the users who aren't in the assignments above
        account_query = select(account_tbl.c.account_id).where(account_tbl.c.account_id.not_in(assignment_account_ids))
        account_ids = self._id_query(account_query)

        return self.fetch_accounts(account_ids)

    def fetch_expt_eligible_accounts(self, start_date: date, end_date: date) -> list[Account]:
        unassigned_accts = self.fetch_unassigned_accounts(start_date, end_date)
        unassigned_acct_ids = [acct.account_id for acct in unassigned_accts]

        subscription_tbl = self.tables["subscriptions"]
        consent_tbl = self.tables["account_consent_log"]

        account_query = (
            select(subscription_tbl.c.account_id)
            .where(
                and_(
                    subscription_tbl.c.account_id.in_(unassigned_acct_ids),
                    subscription_tbl.c.ended == null(),
                )
            )
            .join(consent_tbl, subscription_tbl.c.account_id == consent_tbl.c.account_id)
        )
        eligible_acct_ids = self._id_query(account_query)

        return self.fetch_accounts(eligible_acct_ids)

    def fetch_subscribed_accounts(self) -> list[Account]:
        subscription_tbl = self.tables["subscriptions"]

        account_query = select(subscription_tbl.c.account_id).where(subscription_tbl.c.ended == null())
        account_ids = self._id_query(account_query)
        return self.fetch_accounts(account_ids)

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

    def store_consent(self, account_id: UUID, document_name: str):
        consent_tbl = self.tables["account_consent_log"]
        query = sqlalchemy.insert(consent_tbl).values(account_id=account_id, document_name=document_name)
        self.conn.execute(query)

    def update_status(self, account_id: UUID, new_status: str):
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.update(account_tbl).values(status=new_status).where(account_tbl.c.account_id == account_id)
        self.conn.execute(query)

    def store_login(self, link_data: LoginLinkData):
        web_login_tbl = self.tables["web_logins"]
        query = sqlalchemy.insert(web_login_tbl).values(
            account_id=link_data.account_id,
            newsletter_id=link_data.newsletter_id,
            endpoint=link_data.endpoint,
            data=link_data.data,
        )
        self.conn.execute(query)
