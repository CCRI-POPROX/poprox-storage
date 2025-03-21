from datetime import datetime
from functools import wraps
from typing import get_type_hints

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

    def _write_records_as_parquet(
        self,
        records: list[dict],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from pyarrow import fs

        s3 = fs.S3FileSystem(region="us-east-1")

        start_time = start_time or datetime.now()
        file_name = f"{file_prefix}_{start_time.strftime('%Y%m%d-%H%M%S')}.parquet"

        arrow_table = pa.Table.from_pylist(records)

        with s3.open_output_stream(f"{bucket_name}/{file_name}") as file_:
            pq.write_table(arrow_table, file_)

        return file_name
