from uuid import UUID
from typing import Dict, List, Optional

import tomli
from sqlalchemy import Connection, Table

from poprox_concepts import Account
from poprox_storage.concepts.experiment import (
    Experiment,
    Group,
    Phase,
    Recommender,
    Treatment,
)
from poprox_storage.concepts.manifest import ManifestFile
from poprox_storage.repositories.data_stores.db import (
    DatabaseRepository,
    upsert_and_return_id,
)
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbExperimentRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: Dict[str, Table] = self._load_tables(
            "experiments",
            "expt_allocations",
            "expt_groups",
            "expt_phases",
            "expt_recommenders",
            "expt_treatments",
        )

    def store_experiment(
        self, experiment: Experiment, assignments: Dict[str, List[Account]] = None
    ):
        assignments = assignments or {}
        with self.conn.begin():
            experiment_id = insert_experiment(
                self.conn, self.tables["experiments"], experiment
            )

            for group in experiment.groups:
                group.group_id = insert_expt_group(
                    self.conn,
                    self.tables["expt_groups"],
                    experiment_id,
                    group,
                )
                for account in assignments.get(group.name, []):
                    insert_expt_assignment(
                        self.conn,
                        self.tables["expt_allocations"],
                        account.account_id,
                        group.group_id,
                    )

            for recommender in experiment.recommenders:
                recommender.recommender_id = insert_expt_recommender(
                    self.conn,
                    self.tables["expt_recommenders"],
                    experiment_id,
                    recommender,
                )

            for phase in experiment.phases:
                phase.phase_id = insert_expt_phase(
                    self.conn,
                    self.tables["expt_phases"],
                    experiment_id,
                    phase,
                )
                for treatment in phase.treatments:
                    insert_expt_treatment(
                        self.conn,
                        self.tables["expt_treatments"],
                        phase.phase_id,
                        treatment,
                    )

        return experiment_id


class S3ExperimentRepository(S3Repository):
    def fetch_manifest(self, manifest_file_key) -> ManifestFile:
        manifest_toml = self._get_s3_file(manifest_file_key)
        manifest_dict = tomli.loads(manifest_toml)

        phases = {"sequence": manifest_dict["phases"]["sequence"], "phases": {}}
        for name, phase in manifest_dict["phases"].items():
            if name != "sequence":
                phases["phases"][name] = phase

        manifest_dict["phases"] = phases

        return ManifestFile.model_validate(manifest_dict)


def insert_experiment(
    conn: Connection,
    experiments_table: Table,
    experiment: Experiment,
) -> Optional[UUID]:
    return upsert_and_return_id(
        conn,
        experiments_table,
        {
            "description": experiment.description,
            "start_date": experiment.start_date,
            "end_date": experiment.end_date,
        },
        commit=False,
    )


def insert_expt_group(
    conn: Connection,
    expt_groups_table: Table,
    experiment_id: UUID,
    group: Group,
) -> Optional[UUID]:
    return upsert_and_return_id(
        conn,
        expt_groups_table,
        {
            "experiment_id": experiment_id,
            "group_name": group.name,
        },
        commit=False,
    )


def insert_expt_recommender(
    conn: Connection,
    expt_recommenders_table: Table,
    experiment_id: UUID,
    recommender: Recommender,
):
    return upsert_and_return_id(
        conn,
        expt_recommenders_table,
        {
            "experiment_id": experiment_id,
            "recommender_name": recommender.name,
            "endpoint_url": recommender.endpoint_url,
        },
        commit=False,
    )


def insert_expt_phase(
    conn: Connection,
    expt_phases_table: Table,
    experiment_id: UUID,
    phase: Phase,
):
    return upsert_and_return_id(
        conn,
        expt_phases_table,
        {
            "experiment_id": experiment_id,
            "phase_name": phase.name,
            "start_date": phase.start_date,
            "end_date": phase.end_date,
        },
        commit=False,
    )


def insert_expt_treatment(
    conn: Connection,
    expt_treatments_table: Table,
    phase_id: UUID,
    treatment: Treatment,
):
    return upsert_and_return_id(
        conn,
        expt_treatments_table,
        {
            "phase_id": phase_id,
            "group_id": treatment.group.group_id,
            "recommender_id": treatment.recommender.recommender_id,
        },
        commit=False,
    )


def insert_expt_assignment(
    conn: Connection,
    expt_allocations_table: Table,
    account_id: UUID,
    group_id: UUID,
):
    return upsert_and_return_id(
        conn,
        expt_allocations_table,
        {
            "account_id": account_id,
            "group_id": group_id,
        },
        commit=False,
    )
