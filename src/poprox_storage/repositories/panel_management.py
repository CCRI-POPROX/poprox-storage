from datetime import datetime
from typing import List
from uuid import UUID

from poprox_concepts.domain import Account, Click, Newsletter, WebLogin
from poprox_storage.concepts.experiment import Assignment
from poprox_storage.repositories.data_stores.s3 import S3Repository


class S3PanelManagementRepository(S3Repository):
    def store_accounts_as_parquet(
        self,
        accounts: List[Account],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_accounts_to_records(accounts)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def store_newsletters_as_parquet(
        self,
        newsletters: List[Newsletter],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_newsletters_to_records(newsletters)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def store_web_logins_as_parquet(
        self,
        logins: List[WebLogin],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_logins_to_records(logins)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def store_clicks_as_parquet(
        self,
        clicks_by_account: dict[UUID, list[Click]],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_clicks_to_records(clicks_by_account)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def store_expt_assignments_as_parquet(
        self,
        assignments: list[Assignment],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_assignments_to_records(assignments)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def convert_accounts_to_records(accounts: List[Account]) -> List[dict]:
    records = []
    for acct in accounts:
        records.append(
            {
                "account_id": str(acct.account_id),
                "status": acct.status,
                "source": acct.source,
                "subsource": acct.subsource,
                "created_at": acct.created_at,
            }
        )
    return records


def convert_newsletters_to_records(newsletters: List[Newsletter]) -> List[dict]:
    records = []
    for nl in newsletters:
        records.append(
            {
                "newsletter_id": str(nl.newsletter_id),
                "account_id": str(nl.account_id),
                "created_at": nl.created_at,
            }
        )
    return records


def convert_logins_to_records(logins: List[WebLogin]) -> List[dict]:
    records = []
    for login in logins:
        records.append(
            {
                "account_id": str(login.account_id),
                "newsletter_id": str(login.newsletter_id) if login.newsletter_id else "",
                "endpoint": login.endpoint,
                "created_at": login.created_at,
            }
        )
    return records


def convert_clicks_to_records(clicks_by_accounts: dict[UUID, list[Click]]) -> List[dict]:
    records = []
    for account_id, clicks in clicks_by_accounts.items():
        for click in clicks:
            records.append(
                {
                    "account_id": str(account_id),
                    "newsletter_id": str(click.newsletter_id) if click.newsletter_id else "",
                    "created_at": click.timestamp.isoformat(),
                }
            )
    return records


def convert_assignments_to_records(assignments: list[Assignment]) -> list[dict]:
    records = []
    for assignment in assignments:
        records.append(
            {
                "assignment_id": str(assignment.assignment_id),
                "account_id": str(assignment.account_id),
                "group_id": str(assignment.group_id),
                "opted_out": assignment.opted_out,
            }
        )
    return records
