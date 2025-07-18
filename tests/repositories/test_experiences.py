import datetime
from uuid import uuid4

from sqlalchemy import insert

from poprox_concepts.domain.experience import Experience
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
            "newsletters",
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

        today = datetime.date.today()

        experience = Experience(
            recommender_id=rec.recommender_id, team_id=team.team_id, name="test name", start_date=today
        )
        experience_repo.store_experience(experience)

        results = experience_repo.fetch_active_experiences(today)

        assert 1 == len(results)


def test_store_experience(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "experiences",
            "expt_treatments",
            "recommenders",
            "team_memberships",
            "clicks",
            "account_aliases",
            "newsletters",
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

        # Should be 0 before first insert
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        results = experience_repo.fetch_active_experiences(today)
        assert 0 == len(results)

        team = Team(team_id=uuid4(), team_name="test", members=[])
        rec = Recommender(recommender_id=uuid4(), name="test_rec", url="http://example.org")
        experience = Experience(
            recommender_id=rec.recommender_id, team_id=team.team_id, name="test name", start_date=today
        )
        team_repo.store_team(team)

        # FIXME -- create a general repo function for inserting team recommenders
        insert_query = insert(exp_repo.tables["recommenders"]).values(
            {
                "recommender_id": rec.recommender_id,
                "recommender_name": rec.name,
                "endpoint_url": rec.url,
                "team_id": team.team_id,
            }
        )
        conn.execute(insert_query)

        result_uuid = experience_repo.store_experience(experience)
        assert result_uuid is not None
        assert experience.experience_id == result_uuid

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=2))
        assert 1 == len(results)
        assert experience.experience_id == results[0].experience_id
        assert results[0].end_date is None

        tomorrow = today + datetime.timedelta(days=1)
        experience.end_date = tomorrow
        result_uuid = experience_repo.store_experience(experience)

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=2))
        assert 0 == len(results)

        results = experience_repo.fetch_active_experiences(today)
        assert 1 == len(results)
        assert experience.experience_id == results[0].experience_id
