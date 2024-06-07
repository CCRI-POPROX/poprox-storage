import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import (
    Connection,
    MetaData,
    Table,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, InternalError

from poprox_storage.aws import DB_ENGINE


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DatabaseRepository:
    def __init__(self, connection: Connection):
        self.conn: Connection = connection

    def _load_tables(self, *args):
        metadata = MetaData()
        tables = {}
        for table_name in args:
            tables[table_name] = Table(table_name, metadata, autoload_with=DB_ENGINE)
        return tables

    def _id_query(self, query):
        result = self.conn.execute(query).fetchall()
        return [row[0] for row in result]

    def _upsert_and_return_id(
        self,
        conn,
        table,
        values: Dict[str, Any],
        constraint: str = None,
        commit: bool = True,
    ) -> Optional[UUID]:
        """
        This proxy method exists so that repository code only has to import
        this base class and not the function below. The function will get
        absorbed into this class once the callers have been updated to use
        repositories.
        """
        return upsert_and_return_id(conn, table, values, constraint, commit)


def upsert_and_return_id(
    conn,
    table,
    values: Dict[str, Any],
    constraint: str = None,
    commit: bool = True,
) -> Optional[UUID]:
    try:
        insert_stmt = insert(table).values(**values)
        if constraint:
            insert_stmt = insert_stmt.on_conflict_do_update(
                constraint=constraint, set_=values
            )
        insert_stmt = insert_stmt.returning(table.primary_key.columns)
        results = conn.execute(insert_stmt)
        id_value = results.first()[0]

        if commit:
            conn.commit()
    except (IntegrityError, InternalError) as exc:
        id_value = None
        if commit:
            logger.error(exc)
            conn.rollback()
        else:
            raise

    return id_value
