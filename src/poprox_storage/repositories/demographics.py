import logging
from datetime import datetime
from uuid import UUID

import sqlalchemy
from sqlalchemy import (
    Connection,
    select,
)

from poprox_concepts.domain import Demographics
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbDemographicsRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables("demographics")

    def store_demographics(self, demographic: Demographics) -> None:
        demographics_tbl = self.tables["demographics"]

        query = (
            sqlalchemy.insert(demographics_tbl)
            .values(
                account_id=demographic.account_id,
                gender=demographic.gender,
                birth_year=demographic.birth_year,
                zip3=demographic.zip3,
                education=demographic.education,
                race=demographic.race,
                email_client=demographic.email_client,
            )
            .returning(demographics_tbl.c.demographic_id)
        )
        row = self.conn.execute(query).fetchone()
        return row.demographic_id

    def fetch_demographics_by_account_ids(self, account_ids: list[UUID]) -> list[Demographics]:
        demographics_tbl = self.tables["demographics"]

        demo_query = select(demographics_tbl).where(demographics_tbl.c.account_id.in_(account_ids))
        result = self.conn.execute(demo_query).fetchall()

        return [
            Demographics(
                account_id=row.account_id,
                gender=row.gender,
                birth_year=row.birth_year,
                zip3=row.zip3,
                education=row.education,
                race=row.race,
                created_at=row.created_at,
            )
            for row in result
        ]

    # fetching latest demographic info
    def fetch_latest_demographics_by_account_id(self, account_id: UUID) -> Demographics:
        demographics_tbl = self.tables["demographics"]

        demo_query = (
            select(demographics_tbl)
            .where(demographics_tbl.c.account_id == account_id)
            .order_by(demographics_tbl.c.created_at.desc())
            .limit(1)
        )
        result = self.conn.execute(demo_query).fetchone()

        if result is None:
            return None

        return Demographics(
            account_id=result.account_id,
            gender=result.gender,
            birth_year=result.birth_year,
            zip3=result.zip3,
            education=result.education,
            race=result.race,
            email_client=result.email_client,
        )


class S3DemographicsRepository(S3Repository):
    def store_as_parquet(
        self,
        demographics: list[Demographics],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = convert_to_records(demographics)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def convert_to_records(demographics: list[Demographics]) -> list[dict]:
    records = []
    for demo in demographics:
        records.append(
            {
                "account_id": str(demo.account_id),
                "birth_year": demo.birth_year,
                "education": demo.education,
                "gender": demo.gender,
                "race": demo.race,
                "zip3": demo.zip3,
            }
        )

    return records
