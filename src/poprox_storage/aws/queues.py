import json
import logging
import os
from uuid import UUID

from poprox_concepts.api.recommendations.versions import ProtocolVersions
from poprox_concepts.domain import Account
from poprox_storage.aws import sqs

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RECS_QUEUE_URL = os.getenv("GENERATE_RECS_QUEUE_URL")
SEND_EMAIL_QUEUE_URL = os.getenv("SEND_EMAIL_QUEUE_URL")
EMAIL_FROM = ("POPROX News", "no-reply@poprox.ai")

DEFAULT_API_VERSION = ProtocolVersions.VERSION_2_0
DEFAULT_ENDPOINT_URL = os.getenv("POPROX_DEFAULT_ENDPOINT_URL")


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def enqueue_newsletter_request(
    account_id: UUID,
    profile_id: UUID,
    group_id: UUID,
    recommender_url: str,
    treatment_id: UUID | None = None,
    /,
    experience_id: UUID | None = None,
    endpoint_warm: bool = False,
    api_version: ProtocolVersions = DEFAULT_API_VERSION,
    compensation_banner: bool = False,
    template: str = None,
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
            "template": template,
            experience_id: experience_id,
        }
    )

    if RECS_QUEUE_URL:
        sqs.send_message(queue_url=RECS_QUEUE_URL, message_body=message)
    else:
        logger.warning("Skipping newsletter request since queue URL isn't configured.")


def enqueue_email(newsletter_id, account: Account, email_subject, html, unsubscribe_link):
    message = json.dumps(
        {
            "newsletter_id": str(newsletter_id),
            "account_id": str(account.account_id),
            "email_to": account.email,
            "email_subject": email_subject,
            "email_body": html,
            "unsubscribe_link": unsubscribe_link,
        }
    )

    if SEND_EMAIL_QUEUE_URL:
        sqs.send_message(queue_url=SEND_EMAIL_QUEUE_URL, message_body=message)
    else:
        logger.error(
            "No SEND_EMAIL_QUEUE_URL is provided. This is OK in development, "
            "but if you see this in production something terrible has happened."
        )
        logger.error("Email not sent:")
        logger.warning("to: " + account.email)
        logger.warning("subject: " + email_subject)
        logger.warning(html)
