import logging
from functools import wraps
from typing import Annotated, Any, get_type_hints
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, create_model
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


DbRepositories: type[BaseModel] | None = None


def db_repositories(*args):
    create_repository_model()

    if len(args) == 1 and not isinstance(args[0], list):
        names = [args[0]]
    else:
        names = args

    def inner_decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            type_hints = get_type_hints(DbRepositories)
            with DB_ENGINE.connect() as conn:
                # create Repositories object and pre-construct all requested repository objects
                repos = DbRepositories(conn=conn)
                for name in names:
                    repo_type = type_hints[name]
                    setattr(repos, name, repo_type(conn))
                return handler(event, context, repos)

        return wrapper

    return inner_decorator


def create_repository_model():
    global DbRepositories

    if DbRepositories is None:
        # Convert the attribute names and classes to fields
        fields = {
            name: Annotated[type_, Field(default=None)] for name, type_ in DatabaseRepository._repository_types.items()
        }

        # Dynamically create a Pydantic model with those fields
        DbRepositories = create_model(
            "DbRepositories",
            conn=(Connection, None),
            **fields,
            __config__=ConfigDict(arbitrary_types_allowed=True),
        )


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


class DatabaseRepository:
    _repository_types = {}

    def __init__(self, connection: Connection):
        self.conn: Connection = connection

    def __init_subclass__(cls, *args, **kwargs):
        """
        Gets called once for each loaded class that sub-classes DatabaseRepository
        """

        # Register the attribute name and corresponding class
        concept_name = camel_to_snake(cls.__name__.removeprefix("Db").removesuffix("Repository"))
        cls._repository_types[concept_name] = cls

    def _load_tables(self, *args) -> dict[str, Table]:
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
