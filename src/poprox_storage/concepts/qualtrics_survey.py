from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class QualtricsSurvey(BaseModel):
    survey_id: UUID | None = None
    qualtrics_id: str
    base_url: str
    continuation_token: str | None
    active: bool


class QualtricsSurveyInstance(BaseModel):
    survey_instance_id: UUID | None = None
    survey_instance_id: UUID
    account_id: UUID


class QualtricsSurveyResponse(BaseModel):
    survey_response_id: UUID | None = None
    survey_instance_id: UUID | None
    qualtrics_response_id: str
    raw_data: dict
