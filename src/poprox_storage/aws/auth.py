from boto3 import Session


class Auth:
    __session = None

    @classmethod
    def get_boto3_session(
        cls,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
        region_name=None,
    ) -> Session:
        return cls.__get_boto3_session(
            aws_access_key_id, aws_secret_access_key, aws_session_token, region_name
        )

    @classmethod
    def __get_boto3_session(
        cls,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
        region_name=None,
    ) -> Session:
        if cls.__session is None:
            cls.__session = Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
            )
        return cls.__session
