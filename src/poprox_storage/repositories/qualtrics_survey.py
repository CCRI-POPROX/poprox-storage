import logging
from datetime import datetime, timedelta
from uuid import UUID

import boto3
from sqlalchemy import (
    Connection,
    and_,
    select,
)

from poprox_concepts.domain import Account
from poprox_storage.concepts.qualtrics_survey import (
    QualtricsCleanResponse,
    QualtricsSurvey,
    QualtricsSurveyInstance,
    QualtricsSurveyResponse,
)
from poprox_storage.repositories.data_stores import DatabaseRepository, S3Repository

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
            "qualtrics_clean_responses",
        )

    def store_qualtrics_survey(self, qualtrics_id: str, survey_url: str) -> UUID | None:
        survey_table = self.tables["qualtrics_surveys"]
        return self._upsert_and_return_id(
            self.conn,
            survey_table,
            {"qualtrics_id": qualtrics_id, "base_url": survey_url},
            constraint="uq_qualtrics_id",
        )

    def fetch_survey(self, survey_id: UUID) -> QualtricsSurvey:
        survey_table = self.tables["qualtrics_surveys"]

        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
            survey_table.c.question_metadata_raw,
        ).where(survey_table.c.survey_id == survey_id)
        row = self.conn.execute(query).fetchone()
        return QualtricsSurvey(
            survey_id=row.survey_id,
            qualtrics_id=row.qualtrics_id,
            base_url=row.base_url,
            continuation_token=row.continuation_token,
            active=row.active,
            question_metadata_raw=row.question_metadata_raw,
        )

    def fetch_active_surveys(self) -> list[QualtricsSurvey]:
        survey_table = self.tables["qualtrics_surveys"]
        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
            survey_table.c.question_metadata_raw,
        ).where(survey_table.c.active)
        results = self.conn.execute(query).fetchall()
        return [
            QualtricsSurvey(
                survey_id=row.survey_id,
                qualtrics_id=row.qualtrics_id,
                base_url=row.base_url,
                continuation_token=row.continuation_token,
                active=row.active,
                question_metadata_raw=row.question_metadata_raw,
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

    def fetch_survey_instance(self, survey_instance_id: UUID) -> QualtricsSurveyInstance | None:
        survey_instance_table = self.tables["qualtrics_survey_instances"]

        query = select(survey_instance_table).where(survey_instance_table.c.survey_instance_id == survey_instance_id)
        row = self.conn.execute(query).fetchone()

        if row is None:
            return None
        return QualtricsSurveyInstance(
            survey_instance_id=row.survey_instance_id,
            survey_id=row.survey_id,
            account_id=row.account_id,
            created_at=row.created_at,
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

        where_clause = survey_instance_table.c.account_id == account.account_id

        survey_ids = survey_ids or []
        if survey_ids:
            where_clause = and_(where_clause, survey_instance_table.c.survey_id.in_(survey_ids))

        return self._fetch_survey_responses(where_clause)

    def fetch_survey_responses_since(
        self,
        days_ago: int,
        accounts: list[Account] | None = None,
    ) -> list[tuple[QualtricsSurveyInstance, QualtricsSurveyResponse]]:
        instances_table = self.tables["qualtrics_survey_instances"]

        cutoff = datetime.now() - timedelta(days=days_ago)
        where_clause = instances_table.c.created_at >= cutoff

        if accounts:
            account_ids = [acct.account_id for acct in accounts]
            where_clause = and_(where_clause, instances_table.c.account_id.in_(account_ids))

        return self._fetch_survey_responses(where_clause)

    def _fetch_survey_responses(
        self, where_clause=None
    ) -> list[tuple[QualtricsSurveyInstance, QualtricsSurveyResponse]]:
        survey_instance_table = self.tables["qualtrics_survey_instances"]
        survey_responses_table = self.tables["qualtrics_survey_responses"]

        instance_query = select(survey_instance_table, survey_responses_table)

        response_query = instance_query.join(
            survey_responses_table,
            survey_instance_table.c.survey_instance_id == survey_responses_table.c.survey_instance_id,
        )

        if where_clause is not None:
            response_query = response_query.where(where_clause)

        response_query = response_query.order_by(survey_responses_table.c.created_at.desc())
        results = self.conn.execute(response_query).fetchall()

        return [
            (
                QualtricsSurveyInstance(
                    survey_instance_id=row.survey_instance_id, survey_id=row.survey_id, account_id=row.account_id
                ),
                QualtricsSurveyResponse(
                    survey_response_id=row.survey_response_id,
                    survey_instance_id=row.survey_instance_id,
                    qualtrics_response_id=row.qualtrics_response_id,
                    raw_data=row.raw_data,
                ),
            )
            for row in results
        ]

    def store_clean_response(self, response: QualtricsCleanResponse):
        clean_table = self.tables["qualtrics_clean_responses"]

        return self._upsert_and_return_id(self.conn, clean_table, response.model_dump())

    def fetch_clean_responses_since(
        self, days_ago=1, accounts: list[Account] | None = None
    ) -> list[QualtricsCleanResponse]:
        surveys_table = self.tables["qualtrics_surveys"]
        instances_table = self.tables["qualtrics_survey_instances"]
        responses_table = self.tables["qualtrics_clean_responses"]

        cutoff = datetime.now() - timedelta(days=days_ago)

        response_query = (
            select(responses_table, instances_table, surveys_table)
            .join(
                instances_table,
                responses_table.c.survey_instance_id == instances_table.c.survey_instance_id,
            )
            .join(surveys_table, instances_table.c.survey_id == surveys_table.c.survey_id)
            .where(responses_table.c.created_at >= cutoff)
        )

        if accounts:
            account_ids = [acct.account_id for acct in accounts]
            response_query = response_query.where(instances_table.c.account_id.in_(account_ids))

        results = self.conn.execute(response_query).fetchall()

        return [
            QualtricsCleanResponse(
                account_id=row.account_id,
                survey_id=row.survey_id,
                qualtrics_id=row.qualtrics_id,
                survey_code=row.survey_code,
                survey_response_id=row.survey_response_id,
                survey_instance_id=row.survey_instance_id,
                response_values=row.response_values,
                created_at=row.created_at,
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

    def fetch_latest_survey_sent(self, date: datetime.date = None) -> QualtricsSurvey | None:
        latest_survey = self._fetch_latest_survey_sent(date=date)

        return latest_survey

    def fetch_latest_survey_sent_from_collection(
        self, survey_ids: list[UUID], date: datetime.date = None
    ) -> QualtricsSurvey | None:
        survey_calendar_table = self.tables["qualtrics_survey_calendar"]

        where_clause = survey_calendar_table.c.survey_id.in_(survey_ids)
        latest_survey = self._fetch_latest_survey_sent(where_clause, date)

        return latest_survey

    def _fetch_latest_survey_sent(self, where_clause=None, date: datetime.date = None) -> QualtricsSurvey | None:
        survey_table = self.tables["qualtrics_surveys"]
        survey_calendar_table = self.tables["qualtrics_survey_calendar"]

        date = date or datetime.today().date()

        query = select(survey_table).join(
            survey_calendar_table,
            survey_table.c.survey_id == survey_calendar_table.c.survey_id,
        )

        if where_clause is not None:
            query = query.where(and_(where_clause, survey_calendar_table.c.created_at <= date))
        else:
            query = query.where(survey_calendar_table.c.created_at <= date)

        query = query.order_by(survey_calendar_table.c.created_at.desc()).limit(1)
        row = self.conn.execute(query).fetchone()

        if row is None:
            return None

        return QualtricsSurvey(
            survey_id=row.survey_id,
            qualtrics_id=row.qualtrics_id,
            base_url=row.base_url,
            continuation_token=row.continuation_token,
            active=row.active,
            question_metadata_raw=row.question_metadata_raw,
        )

    def fetch_survey_metadata(self, survey_ids: list[UUID]) -> list[QualtricsSurvey]:
        survey_table = self.tables["qualtrics_surveys"]

        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
            survey_table.c.question_metadata_raw,
        ).where(survey_table.c.survey_id.in_(survey_ids))

        results = self.conn.execute(query).fetchall()
        return [
            QualtricsSurvey(
                survey_id=row.survey_id,
                qualtrics_id=row.qualtrics_id,
                base_url=row.base_url,
                continuation_token=row.continuation_token,
                active=row.active,
                question_metadata_raw=row.question_metadata_raw,
            )
            for row in results
        ]


class S3QualtricsSurveyRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)
        self.s3_client = boto3.client("s3")

    def fetch_survey(self, survey_file_key):
        return self._get_s3_file(survey_file_key)

    def store_as_parquet(
        self,
        responses: list[QualtricsCleanResponse],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = extract_and_flatten(responses)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def extract_and_flatten(responses: list[QualtricsCleanResponse]):
    non_question_fields = [
        "status",
        "endDate",
        "duration",
        "finished",
        "progress",
        "startDate",
        "recordedDate",
        "userLanguage",
    ]

    def flatten(response: QualtricsCleanResponse):
        """
        Flatten each response into multiple rows to create tall format

        survey_response_id, qid, response_value
        1, 1, -2
        1, 2, 1
        1, 3, 4

        Parameters
        ----------
        response : QualtricsCleanResponse
            A Qualtrics survey response that has already been sanitized of PII

        Returns
        -------
        list[dict]
            The records/rows produced by flattening the response
        """
        survey_response_id = response.survey_response_id
        response_values = response.response_values

        return [
            {
                "account_id": str(response.account_id),
                "survey_id": str(response.survey_id),
                "qualtrics_id": response.qualtrics_id,
                "survey_code": response.survey_code,
                "survey_response_id": str(survey_response_id),
                "qid": key,
                "response_value": val,
                "finished": response_values["finished"],
                "progress": response_values["progress"],
                "recorded_date": response_values["recordedDate"],
            }
            for key, val in response_values.items()
            if key not in non_question_fields
        ]

    rows = []
    for response in responses:
        rows.extend(flatten(response))

    return rows
