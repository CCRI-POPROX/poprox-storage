import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import boto3
from sqlalchemy import (
    select,
    Connection,
)
from tqdm import tqdm

from poprox_concepts import Article, Mention, Entity
from poprox_storage.aws import s3, DEV_BUCKET_NAME
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"


class DbArticleRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables = self._load_tables(
            "articles",
            "entities",
            "mentions",
            "impressions",
        )

    def get_todays_articles(self) -> List[Article]:
        article_table = self.tables["articles"]
        return self._get_articles(
            article_table,
            article_table.c.published_at > datetime.now() - timedelta(days=1),
        )

    def get_past_articles(self) -> List[Article]:
        article_table = self.tables["articles"]
        return self._get_articles(
            article_table,
            article_table.c.published_at < datetime.now() - timedelta(days=1),
        )

    def get_articles_by_id(self, ids: List[UUID]) -> List[Article]:
        article_table = self.tables["articles"]
        return self._get_articles(article_table, article_table.c.article_id.in_(ids))

    def get_article_mentions(self, articles: List[Article]) -> List[Article]:
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

    def lookup_article_by_url(
        self, article_url: str, newsletter_id: UUID = None
    ) -> Optional[UUID]:
        impression_table = self.tables["impressions"]
        article_table = self.tables["articles"]

        article_query = select(article_table.c.article_id).where(
            article_table.c.url == article_url
        )
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

    def insert_articles(self, articles: List[Article], progress=False):
        failed = 0

        if progress:
            articles = tqdm(articles, total=len(articles), desc="Ingesting articles")

        for article in articles:
            try:
                article_id = self.insert_article(article)
                if article_id is None:
                    raise RuntimeError(f"Article insert failed for article {article}")
                for mention in article.mentions:
                    entity_id = self.insert_entity(mention.entity)
                    mention.article_id = article_id
                    mention.entity.entity_id = entity_id
                    mention.mention_id = self.insert_mention(mention)
            except RuntimeError as exc:
                logger.error(exc)
                failed += 1

        return failed

    def insert_article(self, article: Article) -> Optional[UUID]:
        article_table = self.tables["articles"]
        return self._upsert_and_return_id(
            self.conn,
            article_table,
            {
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "published_at": article.published_at,
            },
            constraint="uq_articles",
        )

    def insert_entity(self, entity: Entity) -> Optional[UUID]:
        entity_table = self.tables["entities"]
        return self._upsert_and_return_id(
            self.conn,
            entity_table,
            {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "source": entity.source,
                "external_id": entity.external_id,
                "raw_data": entity.raw_data,
            },
            constraint="uq_entities",
        )

    def insert_mention(self, mention: Mention) -> Optional[UUID]:
        mention_table = self.tables["mentions"]
        return self._upsert_and_return_id(
            self.conn,
            mention_table,
            {
                "article_id": mention.article_id,
                "entity_id": mention.entity.entity_id,
                "source": mention.source,
                "relevance": mention.relevance,
            },
            constraint="uq_mentions",
        )

    def _get_articles(self, article_table, where_clause=None) -> List[Article]:
        query = article_table.select()
        if where_clause is not None:
            query = query.where(where_clause)
        result = self.conn.execute(query).fetchall()
        return [
            Article(
                article_id=article[0],
                title=article[1],
                content=article[2],
                url=article[3],
            )
            for article in result
        ]


class S3ArticleRepository(S3Repository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)
        self.s3_client = boto3.client("s3")

    def list_news_files(self, prefix, days_back=None):
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

        files = sorted(
            response.get("Contents", []), key=lambda d: d["LastModified"], reverse=True
        )

        return [f["Key"] for f in files]

    def get_articles_from_file(self, file_key):
        file_contents = self._get_s3_file(file_key)
        articles = extract_articles(file_contents)
        return articles

    def get_articles_from_files(self, file_keys):
        articles = []

        for key in file_keys:
            extracted = self.get_articles_from_file(key)
            articles.extend(extracted)

        return articles

    def get_historical_articles(self) -> List[Article]:
        response = (
            s3.get_object(bucket_name=DEV_BUCKET_NAME, key=NEWS_FILE_KEY)
            .get("Body")
            .read()
        )
        raw_articles = json.loads(response)
        articles = [
            Article(
                title=raw["title"],
                content=raw.get("description", None),
                url=raw["url"],
                published_at=datetime.strptime(
                    raw.get("published_time", "1970-01-01T00:00:00")[:19],
                    "%Y-%m-%dT%H:%M:%S",
                ),
            )
            for raw in raw_articles
        ]

        return articles


def extract_articles(news_file_content) -> List[Article]:
    lines = news_file_content.splitlines()
    articles = []
    num_items = 0
    for line in lines:
        line_obj = json.loads(line)
        items = line_obj["data"]["items"]
        num_items += len(items)
        for item in items:
            if item["item"]["type"] == "text":
                article = item["item"]
                editorial_role = article.get("editorialrole", "not specified")

                extracted_article = create_ap_article(article)
                if extracted_article.url and editorial_role == "FullStory":
                    articles.append(extracted_article)

    return articles


def create_ap_article(article):
    links = article.get("links", [])
    canonical_link = [link["href"] for link in links if link["rel"] == "canonical"]
    if canonical_link:
        canonical_link = canonical_link[0]

    subjects = article.get("subject", [])
    mentions = []
    for subject in subjects:
        if len(subject["name"]) > 1:
            mention = create_ap_subject_mention(subject)
            mentions.append(mention)

    article = Article(
        title=article["headline"],
        content=article["headline_extended"],
        url=canonical_link or None,
        published_at=article["firstcreated"],
        mentions=mentions,
    )

    return article


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
