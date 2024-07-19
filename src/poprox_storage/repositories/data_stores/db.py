import logging
from typing import Any
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

    def _insert_model(
        self,
        table_name: str,
        model,
        addl_fields: dict[str, Any] | None = None,
        *,
        constraint: str | None = None,
        exclude=None,
        commit: bool = True,
    ):
        fields: dict[str, Any] = model.model_dump(exclude=exclude)

        if addl_fields:
            fields.update(addl_fields)

        return self._upsert_and_return_id(
            self.conn,
            self.tables[table_name],
            fields,
            constraint=constraint,
            commit=commit,
        )

    def _upsert_and_return_id(
        self,
        conn,
        table,
        values: dict[str, Any],
        constraint: str | None = None,
        *,
        commit: bool = True,
    ) -> UUID | None:
        try:
            insert_stmt = insert(table).values(**values)
            if constraint:
                insert_stmt = insert_stmt.on_conflict_do_update(constraint=constraint, set_=values)
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
