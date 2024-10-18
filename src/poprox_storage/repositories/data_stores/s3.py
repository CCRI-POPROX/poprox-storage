from datetime import datetime
from functools import wraps
from io import BytesIO
from typing import get_type_hints

import pandas as pd
from smart_open import open as smart_open


def inject_s3_repos(handler):
    @wraps(handler)
    def wrapper(event, context):
        params: dict[str, type] = get_type_hints(handler)
        # remove event, context, and return type if they were annotated.
        params.pop("event", None)
        params.pop("context", None)
        params.pop("return", None)

        repos = dict()
        for param, class_obj in params.items():
            if class_obj in S3Repository._repository_types:
                repos[param] = class_obj()

        return handler(event, context, **repos)

    return wrapper


class S3Repository:
    _repository_types = set()

    def __init__(self, bucket_name):
        self.bucket_name: str = bucket_name

    def __init_subclass__(cls, *args, **kwargs):
        """
        Gets called once for each loaded class that sub-classes DatabaseRepository
        """

        cls._repository_types.add(cls)

    def _get_s3_file(self, key):
        load_path = f"s3://{self.bucket_name}/{key}"

        with smart_open(load_path, "r") as f:
            return f.read()

    def _write_dataframe_as_parquet(
        self,
        dataframe: pd.DataFrame,
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        # Export dataframe as Parquet
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html
        data = BytesIO()

        # FastParquet closes the "file"; temporarily stubbing out the close method prevents that
        orig_close = data.close
        data.close = lambda: None
        try:
            dataframe.to_parquet(data)
        finally:
            data.close = orig_close

        # reset the BytesIO for reading
        data.seek(0)

        start_time = start_time or datetime.now()
        file_name = f"{file_prefix}_{start_time.strftime('%Y%m%d-%H%M%S')}.parquet"

        with smart_open(f"s3://{bucket_name}/{file_name}", "wb") as out_file:
            out_file.write(data.read())

        return file_name
