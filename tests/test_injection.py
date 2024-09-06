from poprox_storage.repositories import DbArticleRepository
from poprox_storage.repositories.data_stores.db import inject_repos
from poprox_storage.repositories.newsletters import DbNewsletterRepository


@inject_repos
def example(event, context, article: DbArticleRepository, newsletter_repo: DbNewsletterRepository):
    return article, newsletter_repo


def test_repositories():
    retval = example({}, {})
    assert isinstance(retval, tuple)
    assert len(retval) == 2
    assert isinstance(retval[0], DbArticleRepository)
    assert isinstance(retval[1], DbNewsletterRepository)
