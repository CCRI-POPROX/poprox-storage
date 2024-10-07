from poprox_storage.repositories import DbNewsletterRepository, S3ArticleRepository, inject_repos


@inject_repos
def example(event, context, article: S3ArticleRepository, newsletter_repo: DbNewsletterRepository):
    return article, newsletter_repo


def test_repositories():
    retval = example({}, {})
    assert isinstance(retval, tuple)
    assert len(retval) == 2
    assert isinstance(retval[0], S3ArticleRepository)
    assert isinstance(retval[1], DbNewsletterRepository)
