from uuid import UUID

import sqlalchemy

from poprox_concepts.domain import Account
from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root
from poprox_storage.repositories import (
    DbAccountRepository,
    DbDatasetRepository,
    DbExperimentRepository,
    DbTeamRepository,
)
from poprox_storage.repositories.data_stores.db import DB_ENGINE
from tests import clear_tables


def test_store_and_load_experiment():
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    with DB_ENGINE.connect() as conn:
        clear_tables(
            conn,
            "account_consent_log",
            "account_interest_log",
            "demographics",
            "account_aliases",
            "team_memberships",
            "expt_assignments",
            "expt_treatments",
            "expt_groups",
            "expt_phases",
            "experiences",
            "recommenders",
            "experiments",
            "datasets",
            "teams",
            "clicks",
            "web_logins",
            "newsletters",
            "accounts",
        )

        account_repo = DbAccountRepository(conn)
        dataset_repo = DbDatasetRepository(conn)
        experiment_repo = DbExperimentRepository(conn)
        team_repo = DbTeamRepository(conn)

        account = Account(
            account_id=experiment.owner.members[0],
            email="example@example.com",
            source="test",
            status="test",
        )

        try:
            account_id = account_repo.store_account(account)
            assert isinstance(account_id, UUID)
            assert str(account_id) == "1936ac91-daf0-4af8-9aa1-53a170c514aa"
        except sqlalchemy.exc.IntegrityError:
            ...

        experiment.owner.team_id = team_repo.store_team(experiment.owner)
        experiment.dataset_id = dataset_repo.store_new_dataset([account], experiment.owner.team_id)
        experiment_id = experiment_repo.store_experiment(experiment, [], experiment.dataset_id)

        assert isinstance(experiment_id, UUID)

        conn.commit()

        loaded_experiment = experiment_repo.fetch_experiment_by_id(experiment_id)

        # force sorting for equality...
        loaded_experiment.phases.sort(key=lambda x: x.name)
        experiment.phases.sort(key=lambda x: x.name)
        loaded_experiment.owner.members.sort()
        experiment.owner.members.sort()
        for phase in loaded_experiment.phases:
            phase.treatments.sort(key=lambda x: x.treatment_id)

        for phase in experiment.phases:
            phase.treatments.sort(key=lambda x: x.treatment_id)

        # set group minimum sizes equal -- this is not currently stored.
        for group in loaded_experiment.groups:
            group.minimum_size = 5
        for group in experiment.groups:
            group.minimum_size = 5

        # with those adjustments -- assert the stored data matches the loaded
        assert loaded_experiment == experiment


def _store_experiment(conn, path):
    with open(path) as f:
        manifest = f.read()
    manifest = parse_manifest_toml(manifest)
    experiment = manifest_to_experiment(manifest)
    clear_tables(
        conn,
        "account_consent_log",
        "account_interest_log",
        "demographics",
        "account_aliases",
        "team_memberships",
        "expt_assignments",
        "expt_treatments",
        "expt_groups",
        "expt_phases",
        "experiences",
        "recommenders",
        "experiments",
        "datasets",
        "teams",
        "clicks",
        "web_logins",
        "newsletters",
        "accounts",
    )

    account_repo = DbAccountRepository(conn)
    dataset_repo = DbDatasetRepository(conn)
    experiment_repo = DbExperimentRepository(conn)
    team_repo = DbTeamRepository(conn)

    for member in experiment.owner.members:
        account = Account(
            account_id=member,
            email=f"example+{member}@example.com",
            source="test",
            status="test",
        )
        account_repo.store_account(account)

    experiment.owner.team_id = team_repo.store_team(experiment.owner)
    experiment.dataset_id = dataset_repo.store_new_dataset([account], experiment.owner.team_id)
    experiment_id = experiment_repo.store_experiment(experiment, [], experiment.dataset_id)

    conn.commit()

    return experiment_repo.fetch_experiment_by_id(experiment_id)


def test_fetch_treatment_templates(db_engine):
    with DB_ENGINE.connect() as conn:
        experiment = _store_experiment(conn, project_root() / "tests" / "data" / "sample_manifest.toml")

        experiment_repo = DbExperimentRepository(conn)

        treatment_ids = [treatment.treatment_id for phase in experiment.phases for treatment in phase.treatments]
        treatment_templates = experiment_repo.fetch_treatment_templates(treatment_ids)
        assert len(treatment_templates) == 9

        for phase in experiment.phases:
            for treatment in phase.treatments:
                if treatment.recommender.name == "x":
                    assert treatment_templates[treatment.treatment_id] == "funkyTemplate.html"

                else:
                    assert treatment_templates[treatment.treatment_id] is None


def test_fetch_datasets_by_group(db_engine):
    with DB_ENGINE.connect() as conn:
        experiment = _store_experiment(conn, project_root() / "tests" / "data" / "sample_manifest.toml")

        experiment_repo = DbExperimentRepository(conn)

        group_ids = [group.group_id for group in experiment.groups]
        assert len(group_ids) == 3

        datasets_by_group = experiment_repo.fetch_datasets_by_group(group_ids)
        assert len(datasets_by_group) == 3

        assert all(dataset_id == experiment.dataset_id for dataset_id in datasets_by_group.values())
