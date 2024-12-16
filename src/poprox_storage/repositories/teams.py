from uuid import UUID

from sqlalchemy import Connection, Table

from poprox_storage.concepts.experiment import Team
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbTeamRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "teams",
            "team_memberships",
        )

    def store_team(
        self,
        team: Team,
    ):
        team_id = self._insert_model("teams", team, exclude={"members"}, commit=False)
        for account_id in team.members:
            self._insert_team_membership(team_id, account_id)
        return team_id

    def _insert_team_membership(self, team_id: UUID, account_id: UUID) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["team_memberships"],
            {"team_id": team_id, "account_id": account_id},
            commit=False,
        )
