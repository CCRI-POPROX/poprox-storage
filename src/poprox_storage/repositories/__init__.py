from poprox_storage.repositories.account_interest_log import DbAccountInterestRepository, S3AccountInterestRepository
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.articles import (
    DbArticleRepository,
    S3ArticleRepository,
)
from poprox_storage.repositories.clicks import DbClicksRepository, S3ClicksRepository
from poprox_storage.repositories.compensation import S3CompensationRepository
from poprox_storage.repositories.datasets import DbDatasetRepository
from poprox_storage.repositories.demographics import DbDemographicsRepository, S3DemographicsRepository
from poprox_storage.repositories.experiments import (
    DbExperimentRepository,
    S3AssignmentsRepository,
    S3ExperimentRepository,
)
from poprox_storage.repositories.images import DbImageRepository, S3ImageRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository, S3NewsletterRepository
from poprox_storage.repositories.placements import DbPlacementRepository
from poprox_storage.repositories.pools import DbCandidatePoolRepository
from poprox_storage.repositories.qualtrics_survey import DbQualtricsSurveyRepository, S3QualtricsSurveyRepository
from poprox_storage.repositories.teams import DbTeamRepository


def inject_repos(handler):
    from functools import wraps
    from typing import get_type_hints

    from poprox_storage.aws import DB_ENGINE, DEV_BUCKET_NAME
    from poprox_storage.repositories.data_stores.db import DatabaseRepository
    from poprox_storage.repositories.data_stores.s3 import S3Repository

    @wraps(handler)
    def wrapper(event, context):
        params: dict[str, type] = get_type_hints(handler)
        # remove event, context, and return type if they were annotated.
        params.pop("event", None)
        params.pop("context", None)
        params.pop("return", None)

        with DB_ENGINE.connect() as conn:
            repos = dict()
            for param, class_obj in params.items():
                if class_obj in DatabaseRepository._repository_types:
                    repos[param] = class_obj(conn)
                elif class_obj in S3Repository._repository_types:
                    repos[param] = class_obj(DEV_BUCKET_NAME)

            return handler(event, context, **repos)

    return wrapper


__all__ = [
    "DbAccountInterestRepository",
    "DbAccountRepository",
    "DbArticleRepository",
    "DbCandidatePoolRepository",
    "DbClicksRepository",
    "DbDatasetRepository",
    "DbDemographicsRepository",
    "DbExperimentRepository",
    "DbImageRepository",
    "DbNewsletterRepository",
    "DbPlacementRepository",
    "DbQualtricsSurveyRepository",
    "DbTeamRepository",
    "S3AccountInterestRepository",
    "S3ArticleRepository",
    "S3AssignmentsRepository",
    "S3ClicksRepository",
    "S3CompensationRepository",
    "S3DemographicsRepository",
    "S3ExperimentRepository",
    "S3ImageRepository",
    "S3NewsletterRepository",
    "S3QualtricsSurveyRepository",
]
