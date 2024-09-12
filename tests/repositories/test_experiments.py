from uuid import UUID

import sqlalchemy

from poprox_concepts.domain import Account
from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root
from poprox_storage.repositories import DbAccountRepository, DbExperimentRepository
from poprox_storage.repositories.data_stores.db import DB_ENGINE
from tests import clear_tables


def test_store_experiment():
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    with DB_ENGINE.connect() as conn:
        clear_tables(
            conn,
            "team_memberships",
            "expt_assignments",
            "expt_treatments",
            "expt_groups",
            "expt_phases",
            "expt_recommenders",
            "experiments",
            "datasets",
            "teams",
            "clicks",
            "web_logins",
            "newsletters",
            "accounts",
        )

        account_repo = DbAccountRepository(conn)
        experiment_repo = DbExperimentRepository(conn)

        try:
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
        except sqlalchemy.exc.IntegrityError:
            ...

        experiment_id = experiment_repo.store_experiment(experiment)

        assert isinstance(experiment_id, UUID)
