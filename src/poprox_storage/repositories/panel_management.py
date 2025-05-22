from datetime import datetime

from poprox_storage.repositories.data_stores.s3 import S3Repository


class S3PanelManagementRepository(S3Repository):
    def store_as_parquet(
        self,
        records: list[dict],
        file_prefix: str,
        start_time: datetime = None,
    ):
        return self._write_records_as_parquet(records, self.bucket_name, file_prefix, start_time)
