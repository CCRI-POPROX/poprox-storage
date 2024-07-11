import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import boto3
from sqlalchemy import (
    select,
    Connection,
)
from tqdm import tqdm

from poprox_concepts import Article, Mention, Entity
from poprox_storage.concepts.qualtrics_survey import (
    QualtricsSurveyInstance,
    QualtricsSurvey,
    QualtricsSurveyResponse,
)
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"


class DbQualtricsSurveyRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "qualtrics_surveys",
            "qualtrics_survey_instances",
            "qualtrics_survey_responses",
        )

    def get_active_surveys(self) -> List[QualtricsSurvey]:
        survey_table = self.tables["qualtrics_surveys"]
        query = select(
            survey_table.c.survey_id,
            survey_table.c.qualtrics_id,
            survey_table.c.base_url,
            survey_table.c.continuation_token,
            survey_table.c.active,
        ).where(survey_table.c.active == True)
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

    def update_survey(self, survey: QualtricsSurvey) -> Optional[UUID]:
        survey_table = self.tables["qualtrics_surveys"]
        return self._upsert_and_return_id(
            self.conn,
            survey_table,
            survey.model_dump(),
            constraint="uq_qualtrics_id",
        )

    def create_survey_instance(
        self, survey: QualtricsSurvey, account_id: UUID
    ) -> Optional[UUID]:
        survey_instance_table = self.tables["qualtrics_survey_instances"]
        return self._upsert_and_return_id(
            self.conn,
            survey_instance_table,
            {"survey_id": survey.survey_id, "account_id": account_id},
        )

    def create_or_update_survey_response(
        self, response: QualtricsSurveyResponse
    ) -> Optional[UUID]:
        survey_responses_table = self.tables["qualtrics_survey_responses"]
        return self._upsert_and_return_id(
            self.conn,
            survey_responses_table,
            {
                "survey_instance_id": response.survey_instance_id,
                "qualtrics_response_id": response.qualtrics_response_id,
                "raw": response.raw,
            },
            constraint="uq_qualtrics_response_id",
        )
