import datetime
from uuid import uuid4

from sqlalchemy import insert

from poprox_storage.concepts.experiment import Recommender, Team
from poprox_storage.repositories.experience import DbExperiencesRepository
from poprox_storage.repositories.experiments import DbExperimentRepository
from poprox_storage.repositories.teams import DbTeamRepository
from tests import clear_tables


def test_non_ending_experience_is_active(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "experiences",
            "expt_treatments",
            "recommenders",
            "team_memberships",
            "clicks",
            "account_aliases",
            "accounts",
            "expt_phases",
            "expt_groups",
            "experiments",
            "datasets",
            "teams",
        )

        experience_repo = DbExperiencesRepository(conn)
        team_repo = DbTeamRepository(conn)
        # rec_repo = DbRecommenderRepository(conn)
        exp_repo = DbExperimentRepository(conn)
        team = Team(team_id=uuid4(), team_name="test", members=[])
        team_repo.store_team(team)

        # FIXME -- create a general repo function for inserting team recommenders
        rec = Recommender(recommender_id=uuid4(), name="test_rec", url="http://example.org")
        insert_query = insert(exp_repo.tables["recommenders"]).values(
            {
                "recommender_id": rec.recommender_id,
                "recommender_name": rec.name,
                "endpoint_url": rec.url,
                "team_id": team.team_id,
            }
        )
        conn.execute(insert_query)

        # FIXME -- create a function for making experiences
        today = datetime.date.today()
        experience_id = uuid4()
        insert_query = insert(experience_repo.tables["experiences"]).values(
            {
                "experience_id": experience_id,
                "recommender_id": rec.recommender_id,
                "name": "test name",
                "team_id": team.team_id,
                "start_date": today,
            }
        )
        conn.execute(insert_query)

        results = experience_repo.fetch_active_experiences(today)

        assert 1 == len(results)
