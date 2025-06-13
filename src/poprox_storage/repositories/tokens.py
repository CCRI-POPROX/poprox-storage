import logging
from uuid import UUID

from sqlalchemy import (
    Connection,
    Table,
    select,
)

from poprox_concepts.api.tracking import Token
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbTokenRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables("tokens")

    def store_token(self, token: Token) -> UUID | None:
        return self._insert_model("tokens", token)

    def fetch_token_by_id(self, token_id: UUID) -> Token | None:
        tokens_table = self.tables["tokens"]

        token_query = select(tokens_table).where(tokens_table.c.token_id == token_id)

        result = self.conn.execute(token_query).first()
        if not result:
            return None
        else:
            return Token(token_id=result.token_id, code=result.code, created_at=result.created_at)
