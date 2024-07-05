from __future__ import annotations

from typing import Dict
from uuid import UUID

from pydantic import BaseModel


class Qualtrics_survey(BaseModel):
    survey_id: UUID | None = None
    qualtrics_id: str
    base_url: str
    continuation_token: str
    active: bool


class Qualtrics_survey_instance(BaseModel):
    survey_instance_id: UUID | None = None
    survey_instance_id: UUID
    account_id: UUID


class Qualtrics_survey_response(BaseModel):
    survey_response_id: UUID | None = None
    survey_instance_id: UUID
    qualtrics_response_id: str
    raw: Dict
