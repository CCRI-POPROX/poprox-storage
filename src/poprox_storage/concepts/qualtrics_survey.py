from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class QualtricsSurvey(BaseModel):
    survey_id: UUID | None = None
    qualtrics_id: str
    base_url: str
    continuation_token: str | None
    active: bool
    question_metadata_raw: dict[str, Any] | None = None


class QualtricsSurveyInstance(BaseModel):
    survey_instance_id: UUID | None = None
    survey_id: UUID
    account_id: UUID
    created_at: datetime | None = None


class QualtricsSurveyResponse(BaseModel):
    survey_response_id: UUID | None = None
    survey_instance_id: UUID | None
    qualtrics_response_id: str
    raw_data: dict
    created_at: datetime | None = None


class QualtricsCleanResponse(BaseModel):
    account_id: UUID
    survey_id: UUID
    qualtrics_id: str
    survey_code: str | None = None
    survey_response_id: UUID
    survey_instance_id: UUID | None = None
    response_values: dict[str, Any]
    created_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        self.created_at = self.created_at or datetime.now(timezone.utc)

        deny_list = [
            "ipAddress",
            "locationLatitude",
            "locationLongitude",
            "_recordId",
            "status",
            "distributionChannel",
            "survey_instance_id",
            "newsletter_html",
        ]

        for denied_key in deny_list:
            if denied_key in self.response_values:
                del self.response_values[denied_key]
