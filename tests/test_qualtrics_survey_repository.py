import json
import os
from uuid import uuid4

import pytest
from poprox_storage.concepts.qualtrics_survey import QualtricsSurveyResponse
from poprox_storage.repositories.qualtrics_survey import DbQualtricsSurveyRepository
from sqlalchemy import create_engine, text

db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_port = os.environ.get("POPROX_DB_PORT", "")

DEFAULT_PG_URL = f"postgresql://postgres:{db_password}@127.0.0.1:{db_port}/poprox"


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return os.getenv("CI_POPROX_PG_URL", DEFAULT_PG_URL)


def test_get_active_survey(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from qualtrics_survey_responses;"))
        conn.execute(text("delete from qualtrics_survey_instances;"))
        conn.execute(text("delete from qualtrics_surveys;"))
        conn.execute(text("insert into qualtrics_surveys(qualtrics_id, base_url) values ('first', 'first');"))
        conn.execute(
            text("insert into qualtrics_surveys(qualtrics_id, base_url, active) values ('second', 'second', false);")
        )
        conn.commit()

        repo = DbQualtricsSurveyRepository(conn)
        results = repo.fetch_active_surveys()
        assert 1 == len(results)

        survey = results[0]

        assert "first" == survey.qualtrics_id
        assert None is survey.continuation_token


def test_update_survey(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from qualtrics_survey_responses;"))
        conn.execute(text("delete from qualtrics_survey_instances;"))
        conn.execute(text("delete from qualtrics_surveys;"))
        conn.execute(text("insert into qualtrics_surveys(qualtrics_id, base_url) values ('first', 'first');"))
        conn.commit()

        repo = DbQualtricsSurveyRepository(conn)
        results = repo.fetch_active_surveys()
        survey = results[0]

        survey.continuation_token = "apple"
        repo.update_survey(survey)

        results = repo.fetch_active_surveys()
        assert len(results) == 1

        survey = results[0]

        assert "first" == survey.qualtrics_id
        assert "apple" == survey.continuation_token


def test_store_survey_instance(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from qualtrics_survey_responses;"))
        conn.execute(text("delete from qualtrics_survey_instances;"))
        conn.execute(text("delete from qualtrics_surveys;"))
        conn.execute(text("insert into qualtrics_surveys(qualtrics_id, base_url) values ('first', 'first');"))
        uuid = uuid4()
        conn.execute(
            text(f"insert into accounts(account_id, email, status, source) values ('{uuid}', 'd@g.com', '', '');")  # noqa: S608
        )

        repo = DbQualtricsSurveyRepository(conn)
        results = repo.fetch_active_surveys()
        survey = results[0]
        repo.store_survey_instance(survey, uuid)
        results = conn.execute(text("select * from qualtrics_survey_instances;")).fetchall()
        assert 1 == len(results)
        assert survey.survey_id == results[0].survey_id
        assert uuid == results[0].account_id
        assert None is not results[0].survey_instance_id


def test_create_survey_response(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from qualtrics_survey_responses;"))
        conn.execute(text("delete from qualtrics_survey_instances;"))
        conn.execute(text("delete from qualtrics_surveys;"))
        conn.execute(text("insert into qualtrics_surveys(qualtrics_id, base_url) values ('first', 'first');"))
        account_uuid = uuid4()
        conn.execute(
            text(
                f"insert into accounts(account_id, email, status, source) values ('{account_uuid}', 'd@g.com', '', '');"  # noqa: S608
            )
        )

        repo = DbQualtricsSurveyRepository(conn)
        results = repo.fetch_active_surveys()
        survey = results[0]
        repo.store_survey_instance(survey, account_uuid)
        results = conn.execute(text("select * from qualtrics_survey_instances;")).fetchall()
        survey_instance_id = results[0].survey_instance_id
        raw_data = json.loads(
            '{"responseId": "R_1pKcm3b4BQjh6zF", "values": {"startDate": "2024-07-08T15:59:53Z", "endDate": "2024-07-08T16:00:23Z", "status": 0, "ipAddress": "131.212.251.236", "progress": 100, "duration": 29, "finished": 1, "recordedDate": "2024-07-08T16:00:23.994Z", "_recordId": "R_1pKcm3b4BQjh6zF", "locationLatitude": "44.9764", "locationLongitude": "-93.224", "distributionChannel": "anonymous", "userLanguage": "EN", "QID1718062235": 1, "QID1718062213_TEXT": "ds", "QID1718062212_TEXT": "adsf", "QID1718062218": 4, "QID1718062218_4_TEXT": "asd", "QID1718062220": 1, "QID1718062226": 1, "QID1718062227": 3, "QID1718062224": 1, "QID1718062219_TEXT": "agsd", "QID1718062222": 2, "QID1718062223": 2, "QID1718062231": 1, "QID1718062233": 5, "QID1718062234": 2, "QID1718062232": 6, "QID1718062229": 6, "QID1718062215_TEXT": "ger", "QID1718062214_TEXT": "asdf", "QID1718062228_NPS_GROUP": 2, "QID1718062228": 8, "QID1718062230": 4, "QID1718062221_TEXT": "e", "QID1718062225_TEXT": "wd", "survey_id": "whatever man today"}, "labels": {"status": "IP Address", "finished": "True", "QID1718062235": "Yes", "QID1718062218": "Other (specify)", "QID1718062220": "Yes", "QID1718062226": "Extremely easy", "QID1718062227": "Slightly easy", "QID1718062224": "Yes", "QID1718062222": "No", "QID1718062223": "No", "QID1718062231": "Extremely good", "QID1718062233": "Slightly difficult", "QID1718062234": "Moderately easy", "QID1718062232": "Moderately difficult", "QID1718062229": "Moderately disorganized", "QID1718062228_NPS_GROUP": "Passive", "QID1718062230": "Probably won\'t"}, "displayedFields": ["QID1718062215_TEXT", "QID1718062212_TEXT", "QID1718062218", "QID1718062229", "QID1718062227", "QID1718062213_TEXT", "QID1718062228", "QID1718062226", "QID1718062223", "QID1718062234", "QID1718062218_4_TEXT", "QID1718062224", "QID1718062235", "QID1718062232", "QID1718062222", "QID1718062233", "QID1718062221_TEXT", "QID1718062230", "QID1718062220", "QID1718062231", "QID1718062219_TEXT", "QID1718062225_TEXT", "QID1718062228_NPS_GROUP", "QID1718062214_TEXT"], "displayedValues": {"QID1718062218": [1, 2, 3, 4], "QID1718062229": [1, 2, 3, 4, 5, 6, 7], "QID1718062227": [1, 2, 3, 4, 5, 6, 7], "QID1718062228": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "QID1718062226": [1, 2, 3, 4, 5, 6, 7], "QID1718062223": [1, 2], "QID1718062234": [1, 2, 3, 4, 5, 6, 7], "QID1718062224": [1, 2], "QID1718062235": [1, 2], "QID1718062232": [1, 2, 3, 4, 5, 6, 7], "QID1718062222": [1, 2], "QID1718062233": [1, 2, 3, 4, 5, 6, 7], "QID1718062230": [1, 2, 3, 4, 5], "QID1718062220": [1, 2], "QID1718062231": [1, 2, 3, 4, 5, 6, 7], "QID1718062228_NPS_GROUP": [1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3]}}'  # noqa: E501
        )
        survey_response = QualtricsSurveyResponse(
            survey_instance_id=survey_instance_id,
            qualtrics_response_id="R_1pKcm3b4BQjh6zF",
            raw_data=raw_data,
        )
        repo.store_survey_response(survey_response)
        results = conn.execute(text("select * from qualtrics_survey_responses;")).fetchall()
        assert 1 == len(results)
        assert survey_instance_id == results[0].survey_instance_id
        assert "R_1pKcm3b4BQjh6zF" == results[0].qualtrics_response_id
        assert raw_data == results[0].raw_data


def test_update_survey_response(pg_url: str):
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        conn.execute(text("delete from qualtrics_survey_responses;"))
        conn.execute(text("delete from qualtrics_survey_instances;"))
        conn.execute(text("delete from qualtrics_surveys;"))
        conn.execute(text("insert into qualtrics_surveys(qualtrics_id, base_url) values ('first', 'first');"))
        account_uuid = uuid4()
        conn.execute(
            text(
                f"insert into accounts(account_id, email, status, source) values ('{account_uuid}', 'd@g.com', '', '');"  # noqa: S608
            )
        )

        repo = DbQualtricsSurveyRepository(conn)
        results = repo.fetch_active_surveys()
        survey = results[0]
        repo.store_survey_instance(survey, account_uuid)
        results = conn.execute(text("select * from qualtrics_survey_instances;")).fetchall()
        survey_instance_id = results[0].survey_instance_id
        raw_data = json.loads(
            '{"responseId": "R_1pKcm3b4BQjh6zF", "values": {"startDate": "2024-07-08T15:59:53Z", "endDate": "2024-07-08T16:00:23Z", "status": 0, "ipAddress": "131.212.251.236", "progress": 100, "duration": 29, "finished": 1, "recordedDate": "2024-07-08T16:00:23.994Z", "_recordId": "R_1pKcm3b4BQjh6zF", "locationLatitude": "44.9764", "locationLongitude": "-93.224", "distributionChannel": "anonymous", "userLanguage": "EN", "QID1718062235": 1, "QID1718062213_TEXT": "ds", "QID1718062212_TEXT": "adsf", "QID1718062218": 4, "QID1718062218_4_TEXT": "asd", "QID1718062220": 1, "QID1718062226": 1, "QID1718062227": 3, "QID1718062224": 1, "QID1718062219_TEXT": "agsd", "QID1718062222": 2, "QID1718062223": 2, "QID1718062231": 1, "QID1718062233": 5, "QID1718062234": 2, "QID1718062232": 6, "QID1718062229": 6, "QID1718062215_TEXT": "ger", "QID1718062214_TEXT": "asdf", "QID1718062228_NPS_GROUP": 2, "QID1718062228": 8, "QID1718062230": 4, "QID1718062221_TEXT": "e", "QID1718062225_TEXT": "wd", "survey_id": "whatever man today"}, "labels": {"status": "IP Address", "finished": "True", "QID1718062235": "Yes", "QID1718062218": "Other (specify)", "QID1718062220": "Yes", "QID1718062226": "Extremely easy", "QID1718062227": "Slightly easy", "QID1718062224": "Yes", "QID1718062222": "No", "QID1718062223": "No", "QID1718062231": "Extremely good", "QID1718062233": "Slightly difficult", "QID1718062234": "Moderately easy", "QID1718062232": "Moderately difficult", "QID1718062229": "Moderately disorganized", "QID1718062228_NPS_GROUP": "Passive", "QID1718062230": "Probably won\'t"}, "displayedFields": ["QID1718062215_TEXT", "QID1718062212_TEXT", "QID1718062218", "QID1718062229", "QID1718062227", "QID1718062213_TEXT", "QID1718062228", "QID1718062226", "QID1718062223", "QID1718062234", "QID1718062218_4_TEXT", "QID1718062224", "QID1718062235", "QID1718062232", "QID1718062222", "QID1718062233", "QID1718062221_TEXT", "QID1718062230", "QID1718062220", "QID1718062231", "QID1718062219_TEXT", "QID1718062225_TEXT", "QID1718062228_NPS_GROUP", "QID1718062214_TEXT"], "displayedValues": {"QID1718062218": [1, 2, 3, 4], "QID1718062229": [1, 2, 3, 4, 5, 6, 7], "QID1718062227": [1, 2, 3, 4, 5, 6, 7], "QID1718062228": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "QID1718062226": [1, 2, 3, 4, 5, 6, 7], "QID1718062223": [1, 2], "QID1718062234": [1, 2, 3, 4, 5, 6, 7], "QID1718062224": [1, 2], "QID1718062235": [1, 2], "QID1718062232": [1, 2, 3, 4, 5, 6, 7], "QID1718062222": [1, 2], "QID1718062233": [1, 2, 3, 4, 5, 6, 7], "QID1718062230": [1, 2, 3, 4, 5], "QID1718062220": [1, 2], "QID1718062231": [1, 2, 3, 4, 5, 6, 7], "QID1718062228_NPS_GROUP": [1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3]}}'  # noqa: E501
        )
        survey_response = QualtricsSurveyResponse(
            survey_instance_id=survey_instance_id,
            qualtrics_response_id="R_1pKcm3b4BQjh6zF",
            raw_data=raw_data,
        )
        repo.store_survey_response(survey_response)
        survey_response.raw_data = {"test": "yay"}
        repo.store_survey_response(survey_response)

        results = conn.execute(text("select * from qualtrics_survey_responses;")).fetchall()
        assert 1 == len(results)
        assert survey_instance_id == results[0].survey_instance_id
        assert "R_1pKcm3b4BQjh6zF" == results[0].qualtrics_response_id
        assert {"test": "yay"} == results[0].raw_data
