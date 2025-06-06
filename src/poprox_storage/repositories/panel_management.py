from datetime import datetime
from typing import List

from poprox_concepts.domain.account import Account
from poprox_storage.repositories.data_stores.s3 import S3Repository


class S3PanelManagementRepository(S3Repository):
    def store_as_parquet(
        self,
        accounts: List[Account],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_to_records(accounts)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def convert_to_records(accounts: List[Account]) -> List[dict]:
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
