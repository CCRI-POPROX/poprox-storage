import logging
from uuid import UUID

from sqlalchemy import Connection, func, select

from poprox_concepts.domain import AccountInterest
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbAccountInterestRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables("account_interest_log", "entities", "account_current_interest_view")

    def store_topic_preference(self, account_id: UUID, entity_id: UUID, preference: int, frequency: int) -> UUID | None:
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
        )

    def store_topic_preferences(self, account_id: UUID, interests: list[AccountInterest]) -> int:
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
                    msg = f"Account Interest insert failed for account interest {interest}"
                    raise RuntimeError(msg)
            except RuntimeError as exc:
                logger.error(exc)
                failed += 1
        return failed

    def fetch_entity_by_name(self, entity_name: str) -> UUID | None:
        entity_tbl = self.tables["entities"]

        query = entity_tbl.select().filter(func.lower(entity_tbl.c.name) == func.lower(entity_name))
        result = self.conn.execute(query).one_or_none()

        if result is not None:
            result = result.entity_id
        return result

    def fetch_topic_preferences(self, account_id: UUID) -> list[AccountInterest]:
        current_interest_tbl = self.tables["account_current_interest_view"]
        entity_tbl = self.tables["entities"]
        query = (
            select(
                current_interest_tbl.c.entity_id,
                current_interest_tbl.c.preference,
                current_interest_tbl.c.frequency,
                entity_tbl.c.name,
            )
            .join(entity_tbl, current_interest_tbl.c.entity_id == entity_tbl.c.entity_id)
            .where(current_interest_tbl.c.account_id == account_id)
        )
        results = self.conn.execute(query).all()
        results = [
            AccountInterest(
                account_id=account_id,
                entity_name=row.name,
                entity_id=row.entity_id,
                preference=row.preference,
                frequency=row.frequency,
            )
            for row in results
        ]
        return results

    insert_topic_preference = store_topic_preference
    insert_topic_preferences = store_topic_preferences
    lookup_entity_by_name = fetch_entity_by_name
    get_topic_preferences = fetch_topic_preferences
