from uuid import UUID

from sqlalchemy import Connection, Table, and_, select

from poprox_concepts import Account
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbDatasetRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "account_aliases", "datasets", "experiments", "expt_assignments", "expt_groups", "teams"
        )

    def store_new_dataset(self, accounts: list[Account], team_id: UUID) -> UUID:
        dataset_id = self._insert_dataset(team_id)

        for account in accounts:
            self._insert_account_alias(dataset_id, account)

        return dataset_id

    def fetch_dataset_id_by_assignment(self, assignment_id: UUID) -> UUID:
        dataset_table = self.tables["datasets"]
        experiment_table = self.tables["experiments"]
        group_table = self.tables["expt_groups"]
        assignment_table = self.tables["expt_assignments"]
        query = (
            select(dataset_table.c.dataset_id)
            .join(
                experiment_table,
                dataset_table.c.dataset_id == experiment_table.c.dataset_id,
            )
            .join(
                group_table,
                group_table.c.experiment_id == experiment_table.c.experiment_id,
            )
            .join(assignment_table, assignment_table.c.group_id == group_table.c.group_id)
            .where(assignment_table.c.assignment_id == assignment_id)
        )

        return self._id_query(query)[0]

    def fetch_account_alias(self, dataset_id, account_id) -> UUID:
        alias_table = self.tables["account_aliases"]
        query = select(alias_table.c.alias_id).where(
            and_(
                alias_table.c.account_id == account_id,
                alias_table.c.dataset_id == dataset_id,
            )
        )
        return self._id_query(query)[0]

    def fetch_account_aliases(self, dataset_id: UUID) -> dict[UUID, UUID]:
        alias_table = self.tables["account_aliases"]
        query = select(alias_table.c.account_id, alias_table.c.alias_id).where(alias_table.c.dataset_id == dataset_id)
        rows = self.conn.execute(query).fetchall()
        return {row.account_id: row.alias_id for row in rows}

    def _insert_dataset(self, team_id: UUID) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["datasets"],
            {"team_id": team_id},
            commit=False,
        )

    def _insert_account_alias(self, dataset_id: UUID, account: Account) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["account_aliases"],
            values={
                "dataset_id": dataset_id,
                "account_id": account.account_id,
            },
            commit=False,
        )
