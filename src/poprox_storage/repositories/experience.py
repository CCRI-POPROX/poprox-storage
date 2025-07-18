from datetime import date
from uuid import UUID

from sqlalchemy import Connection, Table, and_, or_, select

from poprox_concepts.domain.experience import Experience
from poprox_storage.repositories.data_stores.db import DatabaseRepository


class DbExperiencesRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "recommenders",
            "experiences",
        )

    def store_experience(self, experience: Experience) -> UUID | None:
        experiences_table = self.tables["experiences"]
        return self._upsert_and_return_id(
            self.conn,
            experiences_table,
            {
                "experience_id": experience.experience_id,
                "recommender_id": experience.recommender_id,
                "team_id": experience.team_id,
                "name": experience.name,
                "start_date": experience.start_date,
                "end_date": experience.end_date,
                "template": experience.template,
            },
            constraint="experiences_pkey",
            commit=False,
        )

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

    def fetch_active_experiences(self, current_date: date) -> list[Experience]:
        experiences_table = self.tables.get("experiences")
        query = select(experiences_table).where(
            and_(
                experiences_table.c.start_date <= current_date,
                or_(experiences_table.c.end_date >= current_date, experiences_table.c.end_date.is_(None)),
            )
        )
        results = self.conn.execute(query).fetchall()
        return [Experience(**row._asdict()) for row in results]

    def fetch_recommender_url_by_id(self, recommender_id: UUID) -> str | None:
        # Fetch the endpoint_url for a given recommender_id.
        recommenders_table = self.tables["recommenders"]
        query = select(recommenders_table.c.endpoint_url).where(recommenders_table.c.recommender_id == recommender_id)
        result = self.conn.execute(query).first()
        return result[0] if result else None
