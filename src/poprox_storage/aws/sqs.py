import json
from typing import Dict, List, Optional, Union

import boto3
from botocore import exceptions

from .exceptions import PoproxAwsUtilitiesException


class SQS:
    __DEFAULT_REGION = "us-east-1"

    def __init__(self, session: boto3.Session, region_name: Optional[str] = None):
        self.__session = session
        region_name = region_name if region_name is not None else self.__DEFAULT_REGION
        self._sqs_client = self.__session.client("sqs", region_name=region_name)

    def receive_message(self, queue_url: str, max_number_of_messages: int = 1) -> List[Dict]:
        try:
            response = self._sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=max_number_of_messages)
            if "Messages" in response:
                return response["Messages"]

            return []

        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(f"Error receiving message from SQS: {e}") from e

    def send_message(self, queue_url: str, message_body: Union[str, dict]) -> Dict:
        try:
            if isinstance(message_body, dict):
                message_body = json.dumps(message_body)

            response = self._sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)
            if "MessageId" in response:
                return response

            raise PoproxAwsUtilitiesException(f"Could not send message to SQS: {response}")

        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(f"Error sending message to SQS: {e}") from e

    def send_message_batch(self, queue_url: str, message_bodies: List[Dict]) -> Dict:
        """
        You can send up to 10 messages in a single batch.
        If any message in the batch was sent successfully, the function will not raise exception.
        User should check response object for Failed messages.

        Response looks like:
            ```
            {
                    'Successful': []
                    'Failed': []
            }
            ```
        """
        try:
            response = self._sqs_client.send_message_batch(
                QueueUrl=queue_url,
                Entries=[
                    {"Id": str(message_id), "MessageBody": message_body}
                    for message_id, message_body in zip(range(len(message_bodies)), message_bodies)
                ],
            )
            if "Successful" in response:
                return response

            raise PoproxAwsUtilitiesException(f"Could not send message batch to SQS: {response}")

        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(f"Error sending message batch to SQS: {e}") from e
