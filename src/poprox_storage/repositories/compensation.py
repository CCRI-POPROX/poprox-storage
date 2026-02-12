from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Connection,
    and_,
    select,
)

from poprox_concepts.domain import Account, CompensationPeriod
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbCompensationRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables("compensation_periods")

    def store_compensation_period(self, compensation_period: CompensationPeriod) -> UUID | None:
        return self._insert_model(
            "compensation_periods",
            compensation_period,
            exclude={"compensation_id"},
            constraint="uq_compensation_periods",
        )

    def fetch_compensation_period_between(self, start_date: datetime, end_date: datetime) -> CompensationPeriod | None:
        compensation_table = self.tables["compensation_periods"]

        where_clause = and_(
            compensation_table.c.start_date >= start_date,
            compensation_table.c.end_date <= end_date,
        )

        compensation_query = select(compensation_table).where(where_clause)

        result = self.conn.execute(compensation_query).first()
        if not result:
            return None
        else:
            return CompensationPeriod(
                compensation_id=result.compensation_id,
                name=result.name,
                start_date=result.start_date,
                end_date=result.end_date,
                created_at=result.created_at,
            )


class S3CompensationRepository(S3Repository):
    def store_as_parquet(
        self,
        accounts: list[Account],
        active_days: dict[UUID, int],
        survey_counts: dict[UUID, int],
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = [
            {
                "account_id": str(acct.account_id),
                "email": acct.email,
                "compensation": acct.compensation,
                "active_days": active_days[acct.account_id],
                "survey_counts": survey_counts[acct.account_id],
            }
            for acct in accounts
        ]
        return self._write_records_as_parquet(records, self.bucket_name, file_prefix, start_time)
