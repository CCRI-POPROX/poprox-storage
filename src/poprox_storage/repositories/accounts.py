import logging
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

import sqlalchemy
from sqlalchemy import Connection, and_, null, or_, select

from poprox_concepts.api.tracking import LoginLinkData
from poprox_concepts.domain import Account, Subscription, WebLogin
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
            "team_memberships",
        )

    def fetch_accounts(self, account_ids: list[UUID] | None = None) -> list[Account]:
        account_tbl = self.tables["accounts"]

        query = select(
            account_tbl.c.account_id,
            account_tbl.c.email,
            account_tbl.c.status,
            account_tbl.c.source,
            account_tbl.c.subsource,
            account_tbl.c.compensation,
            account_tbl.c.created_at,
        )
        if account_ids is not None and len(account_ids) > 0:
            query = query.where(account_tbl.c.account_id.in_(account_ids))
        elif account_ids is not None and len(account_ids) == 0:
            return []
        return self._fetch_acounts(query)

    def fetch_accounts_between(self, start_date, end_date) -> list[Account]:
        """fetch all accounts whose created at is between start_date and end_date (inclusive)"""
        account_tbl = self.tables["accounts"]

        query = select(account_tbl).where(
            and_(account_tbl.c.created_at >= start_date, account_tbl.c.created_at <= end_date)
        )

        return self._fetch_acounts(query)

    def fetch_account_by_email_query(self, email_query: str) -> list[Account]:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(
            account_tbl,
        ).where(account_tbl.c.email.like(email_query))
        return self._fetch_acounts(query)

    def fetch_account_by_email(self, email: str) -> Account | None:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(account_tbl).where(account_tbl.c.email == email)
        accounts = self._fetch_acounts(query)

        if len(accounts) > 0:
            return accounts[0]
        return None

    def store_account(self, account: Account, commit=False) -> UUID | None:
        account_tbl = self.tables["accounts"]
        return self._upsert_and_return_id(
            self.conn,
            account_tbl,
            {
                "account_id": account.account_id,
                "email": account.email,
                "source": account.source,
                "subsource": account.subsource,
                "status": account.status,
            },
            # NOTE -- this is not explicitly named in out migrations and therefore is _fragile_
            constraint="account_pkey",
            commit=commit,
        )

    def store_new_account(self, email: str, source: str, subsource: str = None) -> Account:
        account_tbl = self.tables["accounts"]
        query = (
            sqlalchemy.insert(account_tbl)
            .values(email=email, source=source, subsource=subsource, status="new_account")
            .returning(account_tbl.c.account_id, account_tbl.c.email, account_tbl.c.status)
        )
        row = self.conn.execute(query).one_or_none()
        return Account(
            account_id=row.account_id, email=row.email, status=row.status, source=source, subsource=subsource
        )

    ######################### storing & fetching the zip code #########################

    def store_zip5(self, account_id: UUID, zip5: str) -> bool:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.update(account_tbl).values(zip5=zip5).where(account_tbl.c.account_id == account_id)
        result = self.conn.execute(query)
        return result.rowcount > 0

    def fetch_zip5(self, account_id: UUID) -> str | None:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(account_tbl.c.zip5).where(account_tbl.c.account_id == account_id)
        result = self.conn.execute(query).one_or_none()
        return result.zip5 if result else None

    ######################### storing & fetching the zip code #########################

    def store_compensation(self, account_id: UUID, compensation: str) -> bool:
        account_tbl = self.tables["accounts"]
        query = (
            sqlalchemy.update(account_tbl)
            .values(compensation=compensation)
            .where(account_tbl.c.account_id == account_id)
        )
        result = self.conn.execute(query)
        return result.rowcount > 0

    def fetch_compensation(self, account_id: UUID) -> str | None:
        account_tbl = self.tables["accounts"]
        query = sqlalchemy.select(account_tbl.c.compensation).where(account_tbl.c.account_id == account_id)
        result = self.conn.execute(query).one_or_none()
        return result.compensation if result else None

    def fetch_unassigned_accounts(self, start_date: date, end_date: date):
        account_tbl = self.tables["accounts"]
        assignment_tbl = self.tables["expt_assignments"]
        phase_tbl = self.tables["expt_phases"]
        treatment_tbl = self.tables["expt_treatments"]

        # Find the experiment phases that are active during the date window
        where_clause = or_(
            # Phase's start date is in the supplied range
            and_(
                phase_tbl.c.start_date >= start_date,
                phase_tbl.c.start_date <= end_date,
            ),
            # Phase's end date is in the supplied range
            and_(phase_tbl.c.end_date >= start_date, phase_tbl.c.end_date <= end_date),
            # Phase's dates cover the whole supplied range
            and_(phase_tbl.c.start_date <= start_date, phase_tbl.c.end_date >= end_date),
            # The supplied range covers the whole phase
            and_(phase_tbl.c.start_date >= start_date, phase_tbl.c.end_date <= end_date),
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

    def fetch_subscribed_accounts_since(self, days_ago=1) -> list[Account]:
        subscription_tbl = self.tables["subscriptions"]

        cutoff = datetime.now() - timedelta(days=days_ago)

        account_query = select(subscription_tbl.c.account_id).where(
            or_(subscription_tbl.c.ended == null(), subscription_tbl.c.ended >= cutoff)
        )
        account_ids = self._id_query(account_query)
        return self.fetch_accounts(account_ids)

    def fetch_subscribed_accounts_between(self, start_date, end_date) -> list[Account]:
        subscription_tbl = self.tables["subscriptions"]

        account_query = select(subscription_tbl.c.account_id).where(
            and_(
                subscription_tbl.c.started <= end_date,
                or_(subscription_tbl.c.ended >= start_date, subscription_tbl.c.ended == null()),
            )
        )
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

    def fetch_logins_between(
        self, start_date: datetime, end_date: datetime, accounts: list[Account] | None = None
    ) -> list[WebLogin]:
        web_login_tbl = self.tables["web_logins"]

        login_query = sqlalchemy.select(
            web_login_tbl.c.account_id,
            web_login_tbl.c.newsletter_id,
            web_login_tbl.c.endpoint,
            web_login_tbl.c.created_at,
        )

        where_clause = and_(
            web_login_tbl.c.created_at >= start_date,
            web_login_tbl.c.created_at <= end_date,
        )

        if accounts:
            account_ids = [a.account_id for a in accounts]
            where_clause = and_(where_clause, web_login_tbl.c.account_id.in_(account_ids))

        login_query = login_query.where(where_clause)
        return self._fetch_logins(login_query)

    def _fetch_logins(self, login_query) -> list[WebLogin]:
        rows = self.conn.execute(login_query).fetchall()

        return [
            WebLogin(
                account_id=row.account_id,
                newsletter_id=row.newsletter_id,
                endpoint=row.endpoint,
                created_at=row.created_at,
            )
            for row in rows
        ]

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

    def end_consent_for_account(self, account_id: UUID):
        consent_tbl = self.tables["account_consent_log"]
        update_query = (
            consent_tbl.update()
            .where(
                consent_tbl.c.account_id == account_id,
                consent_tbl.c.ended_at == null(),
            )
            .values(ended_at=sqlalchemy.text("NOW()"))
        )
        self.conn.execute(update_query)

    def remove_email_for_account(self, account_id: UUID):
        account_tbl = self.tables["accounts"]
        update_query = (
            account_tbl.update()
            .where(
                account_tbl.c.account_id == account_id,
                account_tbl.c.email != null(),
            )
            .values(email=null())
        )
        self.conn.execute(update_query)

    def set_deletion_for_account(self, account_id: UUID):
        account_tbl = self.tables["accounts"]
        update_query = (
            account_tbl.update()
            .where(
                account_tbl.c.account_id == account_id,
            )
            .values(is_deleted=True)
        )
        self.conn.execute(update_query)

    def set_placebo_id(self, account_id: UUID):
        account_tbl = self.tables["accounts"]
        update_query = (
            account_tbl.update()
            .where(
                account_tbl.c.account_id == account_id,
            )
            .values(placebo_id=uuid4())
        )
        self.conn.execute(update_query)

    def fetch_internal_accounts_by_team(self, team_id: UUID) -> list[Account]:
        team_memberships_tbl = self.tables.get("team_memberships")
        accounts_tbl = self.tables.get("accounts")

        # Getting account_ids from team_memberships for the given team_id
        membership_query = select(team_memberships_tbl.c.account_id).where(team_memberships_tbl.c.team_id == team_id)
        membership_results = self.conn.execute(membership_query).fetchall()

        if not membership_results:
            return []

        account_ids = [row[0] for row in membership_results]

        account_query = select(accounts_tbl).where(accounts_tbl.c.account_id.in_(account_ids))
        return self._fetch_acounts(account_query)

    def _fetch_acounts(self, account_query) -> list[Account]:
        result = self.conn.execute(account_query).fetchall()

        return [
            Account(
                account_id=row.account_id,
                email=row.email,
                status=row.status,
                source=row.source,
                subsource=row.subsource,
                compensation=row.compensation,
                created_at=row.created_at,
            )
            for row in result
        ]
