from typing import List, Dict, Optional

import boto3
from botocore import exceptions
from .exceptions import PoproxAwsUtilitiesException


class S3:
    def __init__(self, session: boto3.Session):
        self.__session = session
        self.s3_client = self.__session.client("s3")

    def list_buckets(self) -> List[Dict]:
        """List all buckets in the account"""
        try:
            return self.s3_client.list_buckets().get("Buckets")
        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(f"Error listing buckets: {e}") from e

    def get_object(self, bucket_name: str, key: str, **kwargs) -> Optional[Dict]:
        """Get the object from the bucket. kwargs are passed to the underlying boto3 get_object method"""
        try:
            return self.s3_client.get_object(Bucket=bucket_name, Key=key, **kwargs)
        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(
                f"Error getting object {key} from {bucket_name}: {e}"
            ) from e

    def list_objects(self, bucket_name: str) -> List[Dict]:
        """List all objects in the bucket"""
        objects = []
        next_token = None
        while True:
            try:
                if next_token is not None:
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket_name, ContinuationToken=next_token
                    )
                else:
                    response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            except exceptions.ClientError as e:
                raise PoproxAwsUtilitiesException(
                    f"Error listing objects in {bucket_name}: {e}"
                ) from e

            objects.extend(response.get("Contents", []))
            next_token = response.get("NextContinuationToken")
            if next_token is None:
                return objects

    def put_object(self, bucket_name: str, key: str, body: bytes) -> Dict:
        """Put the object in the bucket"""
        try:
            return self.s3_client.put_object(Bucket=bucket_name, Key=key, Body=body)
        except exceptions.ClientError as e:
            raise PoproxAwsUtilitiesException(
                f"Error putting object {key} in {bucket_name}: {e}"
            ) from e
