import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Connection,
    select,
)

from poprox_concepts.domain import Account
from poprox_storage.concepts.qualtrics_survey import (
    QualtricsSurvey,
    QualtricsSurveyInstance,
    QualtricsSurveyResponse,
)
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"


class DbQualtricsSurveyRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "qualtrics_surveys",
            "qualtrics_survey_calendar",
            "qualtrics_survey_instances",
            "qualtrics_survey_responses",
        )

    def fetch_survey(self, survey_id: UUID) -> QualtricsSurvey:
        survey_table = self.tables["qualtrics_surveys"]

        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
        ).where(survey_table.c.survey_id == survey_id)
        row = self.conn.execute(query).fetchone()
        return QualtricsSurvey(
            survey_id=row.survey_id,
            qualtrics_id=row.qualtrics_id,
            base_url=row.base_url,
            continuation_token=row.continuation_token,
            active=row.active,
        )

    def fetch_active_surveys(self) -> list[QualtricsSurvey]:
        survey_table = self.tables["qualtrics_surveys"]
        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
        ).where(survey_table.c.active)
        results = self.conn.execute(query).fetchall()
        return [
            QualtricsSurvey(
                survey_id=row.survey_id,
                qualtrics_id=row.qualtrics_id,
                base_url=row.base_url,
                continuation_token=row.continuation_token,
                active=row.active,
            )
            for row in results
        ]

    def update_survey(self, survey: QualtricsSurvey) -> UUID | None:
        survey_table = self.tables["qualtrics_surveys"]
        return self._upsert_and_return_id(
            self.conn,
            survey_table,
            survey.model_dump(),
            constraint="uq_qualtrics_id",
        )

    def store_survey_instance(self, survey: QualtricsSurvey, account_id: UUID) -> UUID | None:
        survey_instance_table = self.tables["qualtrics_survey_instances"]
        return self._upsert_and_return_id(
            self.conn,
            survey_instance_table,
            {"survey_id": survey.survey_id, "account_id": account_id},
        )

    def store_survey_response(self, response: QualtricsSurveyResponse) -> UUID | None:
        survey_responses_table = self.tables["qualtrics_survey_responses"]
        return self._upsert_and_return_id(
            self.conn,
            survey_responses_table,
            {
                "survey_instance_id": response.survey_instance_id,
                "qualtrics_response_id": response.qualtrics_response_id,
                "raw_data": response.raw_data,
            },
            constraint="uq_qualtrics_response_id",
        )

    def fetch_survey_responses(
        self, account: Account, survey_ids: list[UUID] | None = None
    ) -> list[tuple[QualtricsSurveyInstance, QualtricsSurveyResponse]]:
        survey_instance_table = self.tables["qualtrics_survey_instances"]
        survey_responses_table = self.tables["qualtrics_survey_responses"]

        survey_ids = survey_ids or []

        instance_query = select(survey_instance_table).where(survey_instance_table.c.account_id == account.account_id)

        if survey_ids:
            instance_query = instance_query.where(survey_instance_table.c.survey_id.in_(survey_ids))

        response_query = instance_query.join(
            survey_responses_table,
            survey_instance_table.c.survey_instance_id == survey_responses_table.c.survey_instance_id,
        )
        results = self.conn.execute(response_query).fetchall()

        return [
            (
                QualtricsSurveyInstance(row.survey_instance_id, row.survey_id, row.account_id),
                QualtricsSurveyResponse(
                    row.survey_response_id,
                    survey_instance_id=row.survey_instance_id,
                    qualtrics_response_id=row.qualtrics_response_id,
                    raw_data=row.raw_data,
                ),
            )
            for row in results
        ]

    def store_latest_survey_sent(self, survey: QualtricsSurvey) -> UUID:
        survey_calendar_table = self.tables["qualtrics_survey_calendar"]

        return self._upsert_and_return_id(
            self.conn,
            survey_calendar_table,
            {"survey_id": survey.survey_id},
        )

    def fetch_latest_survey_sent(self, date: datetime.date = None) -> UUID:
        survey_table = self.tables["qualtrics_surveys"]
        survey_calendar_table = self.tables["qualtrics_survey_calendar"]

        date = date or datetime.date.today()

        query = (
            select(survey_table)
            .join(survey_calendar_table, survey_table.c.survey_id == survey_calendar_table.c.survey_id)
            .where(survey_calendar_table.c.created_at <= date)
            .order_by(survey_calendar_table.c.created_at.desc())
            .limit(1)
        )
        row = self.conn.execute(query).fetchone()

        return QualtricsSurvey(
            survey_id=row.survey_id,
            qualtrics_id=row.qualtrics_id,
            continuation_token=row.continuation_token,
            active=row.active,
        )
