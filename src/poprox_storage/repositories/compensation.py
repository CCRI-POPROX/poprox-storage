from datetime import datetime
from uuid import UUID

from poprox_concepts.domain import Account
from poprox_storage.repositories.data_stores.s3 import S3Repository


class S3CompensationRepository(S3Repository):
    def store_as_parquet(
        self,
        accounts: list[Account],
        active_days: dict[UUID, int],
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = [
            {
                "account_id": str(acct.account_id),
                "email": acct.email,
                "compensation": acct.compensation,
                "active_days": active_days[acct.account_id],
            }
            for acct in accounts
        ]
        return self._write_records_as_parquet(records, self.bucket_name, file_prefix, start_time)
