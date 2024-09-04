from uuid import UUID

from poprox_concepts.domain import Account
from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root
from poprox_storage.repositories import DbAccountRepository, DbExperimentRepository
from poprox_storage.repositories.data_stores.db import DB_ENGINE


def test_store_experiment():
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    with DB_ENGINE.connect() as conn:
        account_repo = DbAccountRepository(conn)
        account_id = account_repo.store_account(
            Account(
                account_id=experiment.owner.members[0],
                email="example@example.com",
                source="test",
                status="test",
            )
        )
        assert isinstance(account_id, UUID)
        assert str(account_id) == "1936ac91-daf0-4af8-9aa1-53a170c514aa"

        experiment_repo = DbExperimentRepository(conn)
        experiment_id = experiment_repo.store_experiment(experiment)

        assert isinstance(experiment_id, UUID)
