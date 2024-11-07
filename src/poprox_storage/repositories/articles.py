import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

import boto3
from sqlalchemy import (
    Connection,
    Table,
    and_,
    func,
    select,
)
from tqdm import tqdm

from poprox_concepts import Article, Entity, Mention
from poprox_storage.aws import DEV_BUCKET_NAME, s3
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"


class DbArticleRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "articles",
            "entities",
            "mentions",
            "impressions",
        )

    def fetch_articles_since(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        return self._get_articles(
            article_table,
            article_table.c.published_at > cutoff,
        )

    def fetch_articles_before(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        return self._get_articles(
            article_table,
            article_table.c.published_at < cutoff,
        )

    def fetch_articles_ingested_since(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        return self._get_articles(
            article_table,
            article_table.c.created_at > cutoff,
        )

    def fetch_articles_ingested_before(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        return self._get_articles(
            article_table,
            article_table.c.created_at < cutoff,
        )

    def fetch_articles_ingested_between(self, start_date, end_date) -> list[Article]:
        article_table = self.tables["articles"]
        return self._get_articles(
            article_table,
            and_(
                article_table.c.created_at <= end_date,
                article_table.c.created_at >= start_date,
            ),
        )

    def fetch_articles_by_id(self, ids: list[UUID]) -> list[Article]:
        article_table = self.tables["articles"]
        return self._get_articles(article_table, article_table.c.article_id.in_(ids))

    def fetch_article_by_external_id(self, id_: str) -> Article:
        article_table = self.tables["articles"]
        return self._get_articles(article_table, article_table.c.external_id == id_)[0]

    def fetch_article_mentions(self, articles: list[Article]) -> list[Article]:
        article_lookup = {article.article_id: article for article in articles}
        article_ids = [article.article_id for article in articles]

        entity_table = self.tables["entities"]
        mention_table = self.tables["mentions"]

        query = (
            select(
                entity_table.c.entity_id,
                entity_table.c.external_id,
                entity_table.c.name,
                entity_table.c.entity_type,
                entity_table.c.source,
                entity_table.c.raw_data,
                mention_table.c.mention_id,
                mention_table.c.article_id,
                mention_table.c.source,
                mention_table.c.relevance,
            )
            .where(mention_table.c.article_id.in_(article_ids))
            .join(entity_table, mention_table.c.entity_id == entity_table.c.entity_id)
        )
        results = self.conn.execute(query).fetchall()

        for row in results:
            entity = Entity(
                entity_id=row[0],
                external_id=row[1],
                name=row[2],
                entity_type=row[3],
                source=row[4],
                raw_data=row[5],
            )
            mention = Mention(
                mention_id=row[6],
                article_id=row[7],
                source=row[8],
                relevance=row[9],
                entity=entity,
            )
            article_lookup[mention.article_id].mentions.append(mention)

        return_val = list(article_lookup.values())
        return return_val

    def fetch_mentions(self) -> list[Mention]:
        entity_table = self.tables["entities"]
        mention_table = self.tables["mentions"]

        query = select(
            entity_table.c.entity_id,
            entity_table.c.external_id,
            entity_table.c.name,
            entity_table.c.entity_type,
            entity_table.c.source,
            entity_table.c.raw_data,
            mention_table.c.mention_id,
            mention_table.c.article_id,
            mention_table.c.source,
            mention_table.c.relevance,
        ).join(entity_table, mention_table.c.entity_id == entity_table.c.entity_id)
        results = self.conn.execute(query).fetchall()
        mentions = []
        for row in results:
            entity = Entity(
                entity_id=row[0],
                external_id=row[1],
                name=row[2],
                entity_type=row[3],
                source=row[4],
                raw_data=row[5],
            )
            mention = Mention(
                mention_id=row[6],
                article_id=row[7],
                source=row[8],
                relevance=row[9],
                entity=entity,
            )
            mentions.append(mention)
        return mentions

    def fetch_article_by_url(self, article_url: str, newsletter_id: UUID | None = None) -> UUID | None:
        impression_table = self.tables["impressions"]
        article_table = self.tables["articles"]

        article_query = select(article_table.c.article_id).where(article_table.c.url == article_url)
        if newsletter_id:
            article_query = article_query.join(
                impression_table,
                impression_table.c.article_id == article_table.c.article_id,
            ).where(impression_table.c.newsletter_id == newsletter_id)

        article_result = self.conn.execute(article_query).first()
        if article_result:
            return article_result[0]
        else:
            return None

    def store_articles(self, articles: list[Article], *, mentions=False, progress=False):
        failed = 0

        if progress:
            articles = tqdm(articles, total=len(articles), desc="Ingesting articles")

        for article in articles:
            try:
                article_id = self.store_article(article)
                if article_id is None:
                    msg = f"Article insert failed for article {article}"
                    raise RuntimeError(msg)
                if mentions:
                    for mention in article.mentions:
                        entity_id = self.store_entity(mention.entity)
                        mention.article_id = article_id
                        mention.entity.entity_id = entity_id
                        mention.mention_id = self.store_mention(mention)
            except RuntimeError as exc:
                logger.error(exc)
                failed += 1

        return failed

    def store_article(self, article: Article) -> UUID | None:
        return self._insert_model(
            "articles",
            article,
            exclude={"article_id", "mentions"},
            constraint="uq_articles",
        )

    def store_entity(self, entity: Entity) -> UUID | None:
        return self._insert_model("entities", entity, exclude={"entity_id"}, constraint="uq_entities")

    def store_mention(self, mention: Mention) -> UUID | None:
        return self._insert_model(
            "mentions",
            mention,
            exclude={"mention_id", "entity"},
            addl_fields={"entity_id": mention.entity.entity_id},
            constraint="uq_mentions",
        )

    def _get_articles(self, article_table: Table, where_clause=None) -> list[Article]:
        # Select only the most recent article row for each source/external id pair
        inner_query = (
            select(
                article_table.c.source,
                article_table.c.external_id,
                func.max(article_table.c.created_at).label("updated_at"),
            )
            .where(article_table.c.external_id.is_not(None))
            .group_by(article_table.c.source, article_table.c.external_id)
            .order_by("updated_at")
        )
        # Select all columns for that subset of the articles
        join_query = article_table.join(
            inner_query,
            and_(
                inner_query.c.source == article_table.c.source,
                inner_query.c.external_id == article_table.c.external_id,
            ),
        )
        query = select(article_table).select_from(join_query)

        if where_clause is not None:
            query = query.where(where_clause)
        result = self.conn.execute(query).fetchall()
        return [
            Article(
                article_id=row.article_id,
                headline=row.headline,
                subhead=row.subhead,
                body=row.body,
                url=row.url,
                preview_image_id=row.preview_image_id,
                source=row.source,
                external_id=row.external_id,
                raw_data=row.raw_data,
                published_at=row.published_at,
                created_at=row.created_at,
            )
            for row in result
        ]


class S3ArticleRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)
        self.s3_client = boto3.client("s3")

    def fetch_news_files(self, prefix, days_back=None):
        """
        Retrieve the names of AP news files from S3 in sorted order

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

    def fetch_articles_from_file(self, file_key):
        file_contents = self._get_s3_file(file_key)
        articles = extract_articles(file_contents)
        return articles

    def fetch_articles_from_files(self, file_keys):
        articles = []

        for key in file_keys:
            extracted = self.fetch_articles_from_file(key)
            articles.extend(extracted)

        return articles

    def fetch_historical_articles(self) -> list[Article]:
        response = s3.get_object(bucket_name=DEV_BUCKET_NAME, key=NEWS_FILE_KEY).get("Body").read()
        raw_articles = json.loads(response)
        articles = [
            Article(
                headline=raw["title"],
                subhead=raw.get("description", None),
                url=raw["url"],
                published_at=datetime.strptime(
                    raw.get("published_time", "1970-01-01T00:00:00")[:19],
                    "%Y-%m-%dT%H:%M:%S",
                ),
            )
            for raw in raw_articles
        ]

        return articles

    def fetch_nitf_file_keys(self, prefix):
        """
        Retrieve the names of AP NITF XML files from S3 in sorted order

        Parameters
        ----------
        prefix : str
            The S3 key prefix to list

        Returns
        -------
        List[str]
            A list of the names of each retrieved file
            in reverse chronological order
        """
        response = self.s3_client.list_objects_v2(Bucket=DEV_BUCKET_NAME, Prefix=prefix)

        files = sorted(response.get("Contents", []), key=lambda d: d["LastModified"], reverse=True)

        return [f["Key"] for f in files]

    def fetch_nitf_file_contents(self, file_key):
        file_contents = self._get_s3_file(file_key)
        return file_contents

    def store_as_parquet(
        self,
        articles: list[Article],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = extract_and_flatten(articles)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def store_mentions_as_parquet(
        self,
        mentions: list[Mention],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ):
        records = extract_and_flatten_mentions(mentions)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)


def extract_articles(news_file_content) -> list[Article]:
    lines = news_file_content.splitlines()
    articles = []
    num_items = 0
    for line in lines:
        line_obj = json.loads(line)
        items = line_obj["data"]["items"]
        num_items += len(items)
        for item in items:
            if item["item"]["type"] == "text":
                ap_item = item["item"]
                editorial_role = ap_item.get("editorialrole", "not specified")

                extracted_article = create_ap_article(ap_item)
                if extracted_article.url and editorial_role == "FullStory":
                    articles.append(extracted_article)

    return articles


def create_ap_article(ap_item):
    links = ap_item.get("links", [])
    canonical_link = [link["href"] for link in links if link["rel"] == "canonical"]
    if canonical_link:
        canonical_link = canonical_link[0]

    subjects = ap_item.get("subject", [])
    mentions = []
    for subject in subjects:
        if len(subject["name"]) > 1:
            mention = create_ap_subject_mention(subject)
            mentions.append(mention)

    item_id = ap_item.get("altids", {}).get("itemid", None)

    ap_item = Article(
        headline=ap_item["headline"],
        subhead=ap_item["headline_extended"],
        url=canonical_link or None,
        published_at=ap_item["firstcreated"],
        mentions=mentions,
        source="AP",
        external_id=item_id,
        raw_data=ap_item,
    )

    return ap_item


def create_ap_subject_mention(subject) -> Mention:
    entity = Entity(
        entity_type="subject",
        source=subject.get("scheme", "http://cv.ap.org/id/"),
        external_id=subject["code"],
        name=subject["name"],
        raw_data=subject,
    )

    source = f"AP-{subject['creator']}"
    relevance = subject.get("relevance", 0)
    mention = Mention(source=source, relevance=relevance, entity=entity)

    return mention


def extract_and_flatten(articles):
    def flatten(article):
        result = article.__dict__
        result["article_id"] = str(result["article_id"])
        mentions = result["mentions"]
        del result["mentions"]
        del result["preview_image_id"]
        del result["source"]
        del result["external_id"]
        mention_dict = {}
        for mention in mentions:
            key = mention.entity.entity_type + "_" + mention.entity.name
            if key not in mention_dict or (key in mention_dict and mention.source == "AP-Editorial"):
                mention_dict[key] = mention
        result["mentions"] = {}
        for key, value in mention_dict.items():
            result["mentions"][key] = value.relevance
        return result

    return [flatten(article) for article in articles]


def extract_and_flatten_mentions(mentions):
    def flatten(mention):
        result = mention.__dict__
        result["article_id"] = str(result["article_id"])
        result["mention_id"] = str(result["mention_id"])
        entity = result["entity"].__dict__
        entity["entity_id"] = str(entity["entity_id"])
        entity["external_id"] = str(entity["external_id"])
        result["entity"] = entity
        return result

    return [flatten(mention) for mention in mentions]
