import json
import logging
import os
from uuid import UUID

from poprox_platform.aws import sqs

from poprox_concepts.api.recommendations.versions import ProtocolVersions

DEFAULT_API_VERSION = ProtocolVersions.VERSION_2_0
DEFAULT_ENDPOINT_URL = os.getenv("POPROX_DEFAULT_ENDPOINT_URL")
RECS_QUEUE_URL = os.getenv("GENERATE_RECS_QUEUE_URL")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def enqueue_newsletter_request(
    account_id: UUID,
    profile_id: UUID,
    group_id: UUID,
    recommender_url: str,
    treatment_id: UUID | None = None,
    endpoint_warm: bool = False,
    api_version: ProtocolVersions = DEFAULT_API_VERSION,
    compensation_banner: bool = False,
):
    message = json.dumps(
        {
            "account_id": str(account_id),
            "profile_id": str(profile_id),
            "group_id": str(group_id),
            "treatment_id": str(treatment_id) if treatment_id else None,
            "recs_endpoint": recommender_url,
            "endpoint_warm": endpoint_warm,
            "api_version": api_version.value,
            "compensation_banner": compensation_banner,
        }
    )

    if RECS_QUEUE_URL:
        sqs.send_message(queue_url=RECS_QUEUE_URL, message_body=message)
    else:
        logger.warning("Skipping newsletter request since queue URL isn't configured.")