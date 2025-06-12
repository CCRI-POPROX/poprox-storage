import logging
import os

from sqlalchemy import (
    create_engine,
)

from poprox_storage.aws.auth import Auth
from poprox_storage.aws.s3 import S3

from .sqs import SQS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SESSION = Auth.get_boto3_session(
    aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

s3 = S3(SESSION)
sqs = SQS(SESSION)

DEV_BUCKET_NAME = "poprox-dev"

db_user = os.environ.get("POPROX_DB_USER", "postgres")
db_password = os.environ.get("POPROX_DB_PASSWORD", "")
db_host = os.environ.get("POPROX_DB_HOST", "127.0.0.1")
db_port = os.environ.get("POPROX_DB_PORT", 5432)
db_name = os.environ.get("POPROX_DB_NAME", "poprox")

DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
DB_ENGINE = create_engine(DB_URL)
