from sqlalchemy import Connection, Table, select

from poprox_concepts.domain.experience import Experience
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbExperiencesRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables("experiences")

    def fetch_experience_by_id(self, experience_id: str) -> Experience | None:
        experiences_table = self.tables.get("experiences")

        experience_query = select(experiences_table).where(experiences_table.c.experience_id == experience_id)
        result = self.conn.execute(experience_query).first()

        if not result:
            return None

        experience = Experience(
            experience_id=result.experience_id,
            recommender_id=result.recommender_id,
            team_id=result.team_id,
            name=result.name,
            start_date=result.start_date,
            end_date=result.end_date,
            created_at=result.created_at,
        )

        return experience
