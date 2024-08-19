from sqlalchemy import Connection

from poprox_storage.repositories import DbArticleRepository
from poprox_storage.repositories.data_stores.db import db_repositories


@db_repositories("article")
def example(event, context, repos):
    return repos


def test_repositories():
    repos = example({}, {})
    fields = repos.model_fields
    assert fields != []

    assert "conn" in fields
    assert fields["conn"].annotation == Connection

    assert "article" in fields
    assert fields["article"].annotation == DbArticleRepository

    assert isinstance(repos.article, DbArticleRepository)
