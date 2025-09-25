import json
import logging
from datetime import datetime
from uuid import UUID

import boto3
from sqlalchemy import (
    Connection,
    select,
)
from tqdm import tqdm

from poprox_concepts.domain import Image
from poprox_storage.aws import DEV_BUCKET_NAME
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbImageRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables("images")

    def store_images(self, images: list[Image], *, progress=False):
        failed = 0

        if progress:
            images = tqdm(images, total=len(images), desc="Ingesting images")

        for image in images:
            try:
                image_id = self.store_image(image)
                if image_id is None:
                    msg = f"Insert failed for image {image}"
                    raise RuntimeError(msg)
            except RuntimeError as exc:
                logger.error(exc)
                failed += 1

        return failed

    def store_image(self, image: Image) -> UUID | None:
        return self._insert_model("images", image, exclude={"image_id"}, constraint="uq_images")

    def fetch_image_by_external_id(self, external_id: str) -> Image | None:
        image_table = self.tables["images"]

        image_query = select(image_table).where(image_table.c.external_id == external_id)

        result = self.conn.execute(image_query).first()
        if not result:
            return None
        else:
            return Image(
                image_id=result.image_id,
                url=result.url,
                source=result.source,
                external_id=result.external_id,
                raw_data=result.raw_data,
                caption=result.caption,
            )

    def fetch_image_by_id(self, image_id: str) -> Image | None:
        image_table = self.tables["images"]

        image_query = select(image_table).where(image_table.c.image_id == image_id)

        result = self.conn.execute(image_query).first()
        if not result:
            return None
        else:
            return Image(
                image_id=result.image_id,
                url=result.url,
                source=result.source,
                external_id=result.external_id,
                raw_data=result.raw_data,
                caption=result.caption,
            )


def extract_and_flatten_images(images):
    def flatten(image):
        result = image.__dict__
        result["image_id"] = str(result["image_id"])
        return result

    return [flatten(image) for image in images]


class S3ImageRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)
        self.s3_client = boto3.client("s3")

    def fetch_image_file_keys(self, prefix, days_back=None):
        """
        Retrieve the names of AP image files from S3 in sorted order

        Parameters
        ----------
        prefix : str
            The S3 key prefix to list
        days_back : int, optional
            How many days worth of files to retrieve, by default None

        Returns
        -------
        List[str]
            A list of the names of each retrieved file
            in reverse chronological order
        """
        response = self.s3_client.list_objects_v2(Bucket=DEV_BUCKET_NAME, Prefix=prefix)

        files = sorted(response.get("Contents", []), key=lambda d: d["LastModified"], reverse=True)

        if days_back:
            files = files[:days_back]

        return [f["Key"] for f in files]

    def fetch_images_from_file(self, file_key):
        file_contents = self.fetch_file_contents(file_key)
        return extract_images(file_contents)

    def fetch_images_from_files(self, file_keys):
        images = []

        for key in file_keys:
            extracted = self.fetch_images_from_file(key)
            images.extend(extracted)

        return images

    def store_as_parquet(
        self,
        images: list[Image],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = extract_and_flatten_images(images)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def extract_images(img_file_content) -> list[Image]:
    lines = img_file_content.splitlines()
    images = []

    for line in lines:
        line_obj = json.loads(line)
        ap_item = line_obj["data"]["item"]
        if ap_item["type"] == "picture":
            extracted_image = create_ap_image(ap_item)
            images.append(extracted_image)

    return images


def create_ap_image(ap_item):
    item_id = ap_item.get("altids", {}).get("itemid", None)

    preview_url = ap_item.get("renditions", {}).get("preview", {}).get("href", None)
    description_caption = ap_item.get("description_caption", None)
    ap_image = Image(
        url=preview_url,
        source="AP",
        external_id=item_id,
        raw_data=ap_item,
        caption=description_caption,
    )
    return ap_image
