import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TypeAlias
from uuid import UUID

import boto3
from sqlalchemy import (
    Connection,
    Table,
    and_,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

from poprox_concepts.domain import Article, Entity, Mention, TopNewsHeadline
from poprox_storage.aws import DEV_BUCKET_NAME, s3
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NEWS_FILE_KEY = "mockObjects/ap_scraped_data.json"

HeadlinePackage: TypeAlias = dict[str, dict[str, TopNewsHeadline]]


class DbArticleRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "articles",
            "article_image_associations",
            "candidate_articles",
            "entities",
            "impressions",
            "mentions",
            "top_stories",
            "article_links",
        )

    def fetch_articles_since(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        query = select(article_table).where(article_table.c.published_at > cutoff)
        return _fetch_articles(self.conn, query, links_table)

    def fetch_articles_before(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        query = select(article_table).where(article_table.c.published_at < cutoff)
        return _fetch_articles(self.conn, query, links_table)

    def fetch_articles_ingested_since(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        query = select(article_table).where(article_table.c.created_at > cutoff)
        return _fetch_articles(self.conn, query, links_table)

    def fetch_articles_ingested_before(self, days_ago=1) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]
        cutoff = datetime.now() - timedelta(days=days_ago)
        query = select(article_table).where(article_table.c.created_at < cutoff)
        return _fetch_articles(self.conn, query, links_table)

    def fetch_articles_ingested_between(self, start_date, end_date) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]

        query = select(article_table).where(
            and_(
                article_table.c.created_at <= end_date,
                article_table.c.created_at >= start_date,
            )
        )
        return _fetch_articles(self.conn, query, links_table)

    def fetch_articles_by_id(self, ids: list[UUID]) -> list[Article]:
        article_table = self.tables["articles"]
        links_table = self.tables["article_links"]
        query = select(article_table).where(article_table.c.article_id.in_(ids))
        return _fetch_articles(self.conn, query, links_table)

    def fetch_article_by_external_id(self, id_: str) -> Article | None:
        article_table = self.tables["articles"]
        deduped = self._get_deduped_articles(article_table, article_table.c.external_id == id_)
        return deduped[0] if deduped else None

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

    def fetch_associated_image_ids(self, articles: list[Article]) -> dict[UUID, list[UUID]]:
        association_table = self.tables["article_image_associations"]

        article_ids = [a.article_id for a in articles]
        association_query = select(association_table.c.article_id, association_table.c.image_id).where(
            association_table.c.article_id.in_(article_ids)
        )

        association_result = self.conn.execute(association_query).fetchall()

        # Converting association_result into a dictionary
        article_image_dict = defaultdict(list)
        for article_id, image_id in association_result:
            if article_id not in article_image_dict:
                article_image_dict[article_id] = []
            article_image_dict[article_id].append(image_id)

        return article_image_dict

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

    def fetch_entity_by_name(self, entity_name: str) -> Entity | None:
        entity_table = self.tables["entities"]

        entity_query = select(entity_table).where(entity_table.c.name == entity_name)
        row = self.conn.execute(entity_query).first()

        if not row:
            return None

        return Entity(
            entity_id=row.entity_id,
            external_id=row.external_id,
            name=row.name,
            entity_type=row.entity_type,
            source=row.source,
            raw_data=row.raw_data,
        )

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
                if article.images:
                    for image in article.images:
                        self.store_image_association(article.article_id, image.image_id)
                if article.linked_articles:
                    for article_uuid, link_text in article.linked_articles.items():
                        self.store_article_link(article.article_id, article_uuid, link_text)

            except RuntimeError as exc:
                logger.error(exc)
                failed += 1

        return failed

    def store_article_link(self, source_article_id: UUID, target_article_id: UUID, link_text: str):
        links_table = self.tables["article_links"]
        insert_stmt = (
            insert(links_table)
            .values(
                {"source_article_id": source_article_id, "target_article_id": target_article_id, "link_text": link_text}
            )
            .on_conflict_do_nothing(constraint="uq_article_links")
        )
        self.conn.execute(insert_stmt)

    def store_headline_packages(self, headline_packages: list[HeadlinePackage]):
        for headline_package in headline_packages:
            self.store_top_headlines(headline_package)

    def store_top_headlines(self, headline_package: HeadlinePackage):
        for topic, headlines in headline_package.items():
            for external_id, headline in headlines.items():
                self.store_top_headline(external_id, headline)

    def store_top_headline(self, external_id: str, top_headline: TopNewsHeadline):
        top_stories_table = self.tables["top_stories"]

        if not top_headline.article_id:
            article = self.fetch_article_by_external_id(external_id)
            if article:
                top_headline.article_id = article.article_id

        if not top_headline.entity_id:
            topic = self.fetch_entity_by_name(top_headline.topic)
            if topic:
                top_headline.entity_id = topic.entity_id

        insert_stmt = insert(top_stories_table).values(
            {
                "article_id": top_headline.article_id,
                "entity_id": top_headline.entity_id,
                "headline": top_headline.headline,
                "position": top_headline.position,
                "as_of": top_headline.as_of,
            }
        )
        self.conn.execute(insert_stmt)

    def store_image_association(self, article_id: str, image_id: str):
        associations_table = self.tables["article_image_associations"]
        insert_stmt = (
            insert(associations_table)
            .values({"article_id": article_id, "image_id": image_id})
            .on_conflict_do_nothing(constraint="uq_article_image_associations")
        )
        self.conn.execute(insert_stmt)

    def store_article(self, article: Article) -> UUID | None:
        return self._insert_model(
            "articles",
            article,
            exclude={"article_id", "mentions", "images"},
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

    def _get_deduped_articles(self, article_table: Table, where_clause=None) -> list[Article]:
        links_table = self.tables["article_links"]
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
                inner_query.c.updated_at == article_table.c.created_at,
            ),
        )
        query = select(article_table).select_from(join_query)

        if where_clause is not None:
            query = query.where(where_clause)

        return _fetch_articles(self.conn, query, links_table)


def _fetch_articles(conn, article_query, links_table: Table) -> list[Article]:
    result = conn.execute(article_query).fetchall()
    articles = [
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

    article_ids = [a.article_id for a in articles]
    linked_articles_query = select(links_table).where(links_table.c.source_article_id.in_(article_ids))
    linked_articles = conn.execute(linked_articles_query).fetchall()

    lookup_table = defaultdict(dict)
    for row in linked_articles:
        lookup_table[row.source_article_id][row.target_article_id] = row.link_text

    for article in articles:
        article.linked_articles = lookup_table[article.article_id]

    return articles


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
        file_contents = self.fetch_file_contents(file_key)
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


def extract_and_flatten(articles):
    def flatten(article):
        result = article.__dict__
        result["article_id"] = str(result["article_id"])
        del result["mentions"]
        del result["preview_image_id"]
        del result["source"]
        del result["external_id"]
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
