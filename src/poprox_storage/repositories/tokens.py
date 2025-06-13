import datetime
import logging
import random
from uuid import UUID, uuid4

from sqlalchemy import (
    Connection,
    Table,
    select,
)

from poprox_concepts.api.tracking import Token
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# removing I,L,1, 0, O as too similar, and limiting to caps only.
# 32 options, 5 bits entropy per letter.
READABLE_CHARACTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class DbTokenRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables("tokens")

    def generate_code(self, length=5):
        # Assumption -- tokens live about 1 hour,
        # Assumption -- the "round-trip" for testing one code is ~50ms
        # that means you can brute-force around 72,000 to 100,000 codes.
        # Length 5 with repitition gives us 33,554,432 code options
        return "".join(random.choice(READABLE_CHARACTERS) for x in range(length))

    def create_token(self) -> Token:
        token = Token(
            token_id=uuid4(),
            code=self.generate_code(),
            created_at=datetime.datetime.now(datetime.timezone.utc).astimezone(),
        )
        self.store_token(token)
        return token

    def store_token(self, token: Token) -> UUID | None:
        return self._insert_model("tokens", token)

    def fetch_token_by_id(self, token_id: UUID) -> Token | None:
        tokens_table = self.tables["tokens"]

        token_query = select(tokens_table).where(tokens_table.c.token_id == token_id)

        result = self.conn.execute(token_query).first()
        if not result:
            return None
        else:
            return Token(token_id=result.token_id, code=result.code, created_at=result.created_at.astimezone())
