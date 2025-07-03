from uuid import UUID

from sqlalchemy import Connection, Table, select

from poprox_storage.concepts.experiment import Team
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbTeamRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "teams",
            "team_memberships",
        )

    def fetch_teams(self) -> dict[UUID, Team]:
        """Note -- this does not return members of teams"""
        team_table = self.tables["teams"]
        team_query = select(team_table)
        results = self.conn.execute(team_query).all()
        return {row.team_id: Team(team_id=row.team_id, team_name=row.team_name, members=[]) for row in results}

    def fetch_team_by_id(self, team_id: UUID) -> Team:
        team_table = self.tables["teams"]
        team_member_table = self.tables["team_memberships"]

        member_query = select(team_member_table).where(team_member_table.c.team_id == team_id)
        member_query_result = self.conn.execute(member_query).all()
        members = [row.account_id for row in member_query_result]

        team_query = select(team_table).where(team_table.c.team_id == team_id)
        result = self.conn.execute(team_query).one()
        return Team(team_id=result.team_id, team_name=result.team_name, members=members)

    def fetch_teams_for_account(self, account_id: UUID) -> dict[UUID, Team]:
        """Note -- this does not return other members of teams the current account is in."""
        team_table = self.tables["teams"]
        team_member_table = self.tables["team_memberships"]
        team_member_query = (
            select(team_member_table, team_table)
            .join(team_table, team_member_table.c.team_id == team_table.c.team_id)
            .where(team_member_table.c.account_id == account_id)
        )
        team_member_results = self.conn.execute(team_member_query).all()
        return {
            row.team_id: Team(team_id=row.team_id, team_name=row.team_name, members=[]) for row in team_member_results
        }

    def store_team(
        self,
        team: Team,
    ):
        team_id = self._insert_model("teams", team, exclude={"members"}, constraint="teams_pkey", commit=False)
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
