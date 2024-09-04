from uuid import UUID

from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root
from poprox_storage.repositories import DbExperimentRepository
from poprox_storage.repositories.data_stores.db import inject_repos


@inject_repos
def test_store_experiment(experiment_repo: DbExperimentRepository):
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    experiment_id = experiment_repo.store_experiment(experiment)

    assert isinstance(experiment_id, UUID)
