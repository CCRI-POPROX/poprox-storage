import datetime
from uuid import uuid4

from poprox_concepts.domain.experience import Experience
from poprox_storage.concepts.experiment import Recommender, Team
from poprox_storage.repositories.experience import DbExperiencesRepository
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
            "impressed_sections",
            "section_types",
            "newsletters",
            "demographics",
            "account_interest_log",
            "account_consent_log",
            "accounts",
            "expt_phases",
            "expt_groups",
            "experiments",
            "datasets",
            "teams",
        )

        experience_repo = DbExperiencesRepository(conn)
        team_repo = DbTeamRepository(conn)

        today = datetime.date.today()
        team = Team(team_id=uuid4(), team_name="test", members=[])
        rec = Recommender(recommender_id=uuid4(), name="test_rec", url="http://example.org")
        experience = Experience(
            recommender_id=rec.recommender_id, team_id=team.team_id, name="test name", start_date=today
        )

        team_repo.store_team(team)
        team_repo.store_team_recommender(team.team_id, rec)
        experience_repo.store_experience(experience)

        results = experience_repo.fetch_active_experiences(today)

        assert 1 == len(results)


def test_end_date_is_active(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "experiences",
            "expt_treatments",
            "recommenders",
            "team_memberships",
            "clicks",
            "account_aliases",
            "impressed_sections",
            "section_types",
            "newsletters",
            "demographics",
            "account_interest_log",
            "account_consent_log",
            "accounts",
            "expt_phases",
            "expt_groups",
            "experiments",
            "datasets",
            "teams",
        )

        experience_repo = DbExperiencesRepository(conn)
        team_repo = DbTeamRepository(conn)

        today = datetime.date.today()
        team = Team(team_id=uuid4(), team_name="test", members=[])
        rec = Recommender(recommender_id=uuid4(), name="test_rec", url="http://example.org")
        experience = Experience(
            recommender_id=rec.recommender_id,
            team_id=team.team_id,
            name="test name",
            start_date=today,
            end_date=today + datetime.timedelta(days=2),
        )

        team_repo.store_team(team)
        team_repo.store_team_recommender(team.team_id, rec)
        experience_repo.store_experience(experience)

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=1))
        assert 1 == len(results)

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=3))
        assert 0 == len(results)


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
            "impressed_sections",
            "section_types",
            "newsletters",
            "demographics",
            "account_interest_log",
            "account_consent_log",
            "accounts",
            "expt_phases",
            "expt_groups",
            "experiments",
            "datasets",
            "teams",
        )

        experience_repo = DbExperiencesRepository(conn)
        team_repo = DbTeamRepository(conn)

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
        team_repo.store_team_recommender(team.team_id, rec)

        result_uuid = experience_repo.store_experience(experience)
        assert result_uuid is not None
        assert experience.experience_id == result_uuid

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=2))
        assert 1 == len(results)
        assert experience.experience_id == results[0].experience_id
        assert results[0].end_date is None

        # Test that we can update experience end dates (the most important update)
        tomorrow = today + datetime.timedelta(days=1)
        experience.end_date = tomorrow
        result_uuid = experience_repo.store_experience(experience)

        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=2))
        assert 0 == len(results)

        results = experience_repo.fetch_active_experiences(today)
        assert 1 == len(results)
        assert experience.experience_id == results[0].experience_id


def test_store_template(db_engine):
    with db_engine.connect() as conn:
        clear_tables(
            conn,
            "experiences",
            "expt_treatments",
            "recommenders",
            "team_memberships",
            "clicks",
            "account_aliases",
            "impressed_sections",
            "section_types",
            "newsletters",
            "demographics",
            "account_interest_log",
            "account_consent_log",
            "accounts",
            "expt_phases",
            "expt_groups",
            "experiments",
            "datasets",
            "teams",
        )

        experience_repo = DbExperiencesRepository(conn)
        team_repo = DbTeamRepository(conn)

        # Should be 0 before first insert
        today = datetime.date.today()
        results = experience_repo.fetch_active_experiences(today)
        assert 0 == len(results)

        team = Team(team_id=uuid4(), team_name="test", members=[])
        rec = Recommender(recommender_id=uuid4(), name="test_rec", url="http://example.org")
        experience = Experience(
            recommender_id=rec.recommender_id,
            team_id=team.team_id,
            name="test name",
            start_date=today,
            template="test.html",
        )
        team_repo.store_team(team)
        team_repo.store_team_recommender(team.team_id, rec)

        experience_repo.store_experience(experience)
        results = experience_repo.fetch_active_experiences(today + datetime.timedelta(days=2))
        assert "test.html" == results[0].template

        results = experience_repo.fetch_experiences_by_team(team.team_id)
        assert "test.html" == results[0].template

        result = experience_repo.fetch_experience_by_id(experience.experience_id)
        assert "test.html" == result.template
