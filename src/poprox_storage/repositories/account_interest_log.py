import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Connection,
)

from poprox_concepts.domain import AccountInterest
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"


class DbAccountInterestRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "account_interest_log", "entities", "account_current_interest_view"
        )

    def insert_topic_preference(
        self, account_id: UUID, entity_id: UUID, preference: int, frequency: int
    ) -> Optional[UUID]:
        interest_log_tbl = self.tables["account_interest_log"]
        return self._upsert_and_return_id(
            self.conn,
            interest_log_tbl,
            {
                "account_id": account_id,
                "entity_id": entity_id,
                "preference": preference,
                "frequency": frequency,
            },
            constraint="uq_account_interest_log",
        )

    def insert_topic_preferences(
        self, account_id: UUID, interests: List[AccountInterest]
    ) -> int:
        failed = 0

        for interest in interests:
            try:
                log_id = self.insert_topic_preference(
                    account_id,
                    interest.entity_id,
                    interest.preference,
                    interest.frequency,
                )
                if log_id is None:
                    raise RuntimeError(
                        f"Account Interest insert failed for account interest {interest}"
                    )
            except RuntimeError as exc:
                logger.error(exc)
                failed += 1
        return failed

    def get_topic_preferences(self, account_id: UUID) -> List[AccountInterest]:
        current_interest_tbl = self.tables["account_current_interest_view"]
        query = current_interest_tbl.select().where(
            current_interest_tbl.c.account_id == account_id
        )
        results = self.conn.execute(query).all()
        results = [
            AccountInterest(
                account_id=account_id,
                entity_id=row.entity_id,
                preference=row.preference,
                frequency=row.frequency,
            )
            for row in results
        ]
        return results
