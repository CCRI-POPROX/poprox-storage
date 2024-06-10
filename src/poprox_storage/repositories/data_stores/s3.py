from smart_open import open as smart_open


class S3Repository:
    def __init__(self, bucket_name):
        self.bucket_name: str = bucket_name

    def _get_s3_file(self, key):
        load_path = f"s3://{self.bucket_name}/{key}"

        with smart_open(load_path, "r") as f:
            return f.read()
