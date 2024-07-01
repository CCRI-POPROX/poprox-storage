import datetime
from uuid import UUID

import tomli
from poprox_concepts import Account
from sqlalchemy import Connection, Table, and_, select

from poprox_storage.concepts.experiment import (
    Experiment,
    Group,
    Phase,
    Recommender,
    Treatment,
)
from poprox_storage.concepts.manifest import ManifestFile
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbExperimentRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "experiments",
            "expt_allocations",
            "expt_groups",
            "expt_phases",
            "expt_recommenders",
            "expt_treatments",
        )

    def store_experiment(self, experiment: Experiment, assignments: dict[str, list[Account]] | None = None):
        assignments = assignments or {}
        self.conn.rollback()
        with self.conn.begin():
            experiment_id = self.insert_experiment(self.conn, self.tables["experiments"], experiment)

            for group in experiment.groups:
                group.group_id = self.insert_expt_group(
                    self.conn,
                    self.tables["expt_groups"],
                    experiment_id,
                    group,
                )
                for account in assignments.get(group.name, []):
                    self.insert_expt_assignment(
                        self.conn,
                        self.tables["expt_allocations"],
                        account.account_id,
                        group.group_id,
                    )

            for recommender in experiment.recommenders:
                recommender.recommender_id = self.insert_expt_recommender(
                    self.conn,
                    self.tables["expt_recommenders"],
                    experiment_id,
                    recommender,
                )

            for phase in experiment.phases:
                phase.phase_id = self.insert_expt_phase(
                    self.conn,
                    self.tables["expt_phases"],
                    experiment_id,
                    phase,
                )
                for treatment in phase.treatments:
                    self.insert_expt_treatment(
                        self.conn,
                        self.tables["expt_treatments"],
                        phase.phase_id,
                        treatment,
                    )

        return experiment_id

    def get_active_expt_group_ids(self, date: datetime.date | None = None) -> list[UUID]:
        groups_tbl = self.tables["expt_groups"]
        phases_tbl = self.tables["expt_phases"]
        treatments_tbl = self.tables["expt_treatments"]

        date = date or datetime.date.today()

        groups_query = (
            select(groups_tbl.c.group_id)
            .join(treatments_tbl, treatments_tbl.c.group_id == groups_tbl.c.group_id)
            .join(phases_tbl, phases_tbl.c.phase_id == treatments_tbl.c.phase_id)
        ).where(
            and_(
                phases_tbl.c.start_date <= date,
                date < phases_tbl.c.end_date,
            )
        )

        return self._id_query(groups_query)

    def get_active_expt_endpoint_urls(self, date: datetime.date | None = None) -> dict[UUID, str]:
        groups_tbl = self.tables["expt_groups"]
        phases_tbl = self.tables["expt_phases"]
        recommenders_tbl = self.tables["expt_recommenders"]
        treatments_tbl = self.tables["expt_treatments"]

        # Find the groups and associated recommenders for the active experiment phases
        date = date or datetime.date.today()

        group_recommender_query = (
            select(groups_tbl.c.group_id, recommenders_tbl.c.endpoint_url)
            .join(treatments_tbl, treatments_tbl.c.group_id == groups_tbl.c.group_id)
            .join(
                recommenders_tbl,
                recommenders_tbl.c.recommender_id == treatments_tbl.c.recommender_id,
            )
            .join(phases_tbl, phases_tbl.c.phase_id == treatments_tbl.c.phase_id)
        ).where(
            and_(
                phases_tbl.c.start_date <= date,
                date < phases_tbl.c.end_date,
            )
        )

        result = self.conn.execute(group_recommender_query).fetchall()
        recommender_lookup_by_group = {row[0]: row[1] for row in result}

        return recommender_lookup_by_group

    def get_active_expt_assignments(self, date: datetime.date | None = None) -> dict[UUID, UUID]:
        allocations_tbl = self.tables["expt_allocations"]

        group_ids = self.get_active_expt_group_ids(date)

        # Find accounts allocated to the groups that are assigned the active recommenders above
        group_query = select(allocations_tbl.c.account_id, allocations_tbl.c.group_id).where(
            allocations_tbl.c.group_id.in_(group_ids)
        )
        result = self.conn.execute(group_query).fetchall()
        group_lookup_by_account = {row[0]: row[1] for row in result}

        return group_lookup_by_account

    def insert_experiment(
        self,
        conn: Connection,
        experiments_table: Table,
        experiment: Experiment,
    ) -> UUID | None:
        return self._upsert_and_return_id(
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
        self,
        conn: Connection,
        expt_groups_table: Table,
        experiment_id: UUID,
        group: Group,
    ) -> UUID | None:
        return self._upsert_and_return_id(
            conn,
            expt_groups_table,
            {
                "experiment_id": experiment_id,
                "group_name": group.name,
            },
            commit=False,
        )

    def insert_expt_recommender(
        self,
        conn: Connection,
        expt_recommenders_table: Table,
        experiment_id: UUID,
        recommender: Recommender,
    ) -> UUID | None:
        return self._upsert_and_return_id(
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
        self,
        conn: Connection,
        expt_phases_table: Table,
        experiment_id: UUID,
        phase: Phase,
    ) -> UUID | None:
        return self._upsert_and_return_id(
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
        self,
        conn: Connection,
        expt_treatments_table: Table,
        phase_id: UUID,
        treatment: Treatment,
    ) -> UUID | None:
        return self._upsert_and_return_id(
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
        self,
        conn: Connection,
        expt_allocations_table: Table,
        account_id: UUID,
        group_id: UUID,
    ) -> UUID | None:
        return self._upsert_and_return_id(
            conn,
            expt_allocations_table,
            {
                "account_id": account_id,
                "group_id": group_id,
            },
            commit=False,
        )


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
