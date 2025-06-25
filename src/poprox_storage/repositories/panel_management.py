from datetime import datetime
from typing import List

from poprox_concepts.domain.account import Account
from poprox_concepts.domain.newsletter import Newsletter
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
        logins: List[dict],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_logins_to_records(logins)
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


def convert_logins_to_records(logins: List[dict]) -> List[dict]:
    records = []
    for login in logins:
        records.append(
            {
                "account_id": str(login["account_id"]),
                "newsletter_id": str(login["newsletter_id"]),
                "endpoint": login["endpoint"],
                "data": login["data"],
                "created_at": login["created_at"],
            }
        )
    return records
