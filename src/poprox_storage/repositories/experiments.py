import datetime
from uuid import UUID

from sqlalchemy import Connection, Table, and_, select, update

from poprox_concepts import Account
from poprox_storage.concepts.experiment import (
    Assignment,
    Experiment,
    Group,
    Phase,
    Recommender,
    Team,
    Treatment,
)
from poprox_storage.concepts.manifest import ManifestFile, parse_manifest_toml
from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.data_stores.s3 import S3Repository


class DbExperimentRepository(DatabaseRepository):
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.tables: dict[str, Table] = self._load_tables(
            "account_aliases",
            "datasets",
            "experiments",
            "expt_assignments",
            "expt_groups",
            "expt_phases",
            "expt_recommenders",
            "expt_treatments",
            "teams",
            "team_memberships",
        )

    def store_experiment(
        self,
        experiment: Experiment,
        assignments: dict[str, list[Account]] | None = None,
    ):
        assignments = assignments or {}
        self.conn.commit()
        with self.conn.begin():
            experiment.owner.team_id = self._insert_expt_team(experiment.owner)
            dataset_id = self._insert_expt_dataset(experiment.owner)
            experiment_id = self._insert_experiment(dataset_id, experiment)

            for group in experiment.groups:
                group.group_id = self._insert_expt_group(experiment_id, group)
                for account in assignments.get(group.name, []):
                    self._insert_account_alias(dataset_id, account)

                    assignment = Assignment(account_id=account.account_id, group_id=group.group_id)
                    self._insert_expt_assignment(assignment)

            for recommender in experiment.recommenders:
                recommender.recommender_id = self._insert_expt_recommender(
                    experiment_id,
                    recommender,
                )

            for phase in experiment.phases:
                phase.phase_id = self._insert_expt_phase(experiment_id, phase)
                for treatment in phase.treatments:
                    self._insert_expt_treatment(phase.phase_id, treatment)

        return experiment_id

    def fetch_active_expt_group_ids(self, date: datetime.date | None = None) -> list[UUID]:
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

    def fetch_active_treatments_by_group(self, date: datetime.date | None = None) -> dict[UUID, UUID]:
        phases_tbl = self.tables["expt_phases"]
        treatments_tbl = self.tables["expt_treatments"]

        # Find the groups and associated recommenders for the active experiment phases
        date = date or datetime.date.today()

        group_treatment_query = (
            select(treatments_tbl.c.group_id, treatments_tbl.c.treatment_id).join(
                phases_tbl, phases_tbl.c.phase_id == treatments_tbl.c.phase_id
            )
        ).where(
            and_(
                phases_tbl.c.start_date <= date,
                date < phases_tbl.c.end_date,
            )
        )

        result = self.conn.execute(group_treatment_query).fetchall()
        treatment_lookup_by_group = {row[0]: row[1] for row in result}

        return treatment_lookup_by_group

    def fetch_treatment_endpoint_urls(self, treatment_ids: list[UUID]) -> dict[UUID, str]:
        recommenders_tbl = self.tables["expt_recommenders"]
        treatments_tbl = self.tables["expt_treatments"]

        treatment_endpoint_query = (
            select(treatments_tbl.c.treatment_id, recommenders_tbl.c.endpoint_url)
            .where(treatments_tbl.c.treatment_id.in_(treatment_ids))
            .join(
                recommenders_tbl,
                recommenders_tbl.c.recommender_id == treatments_tbl.c.recommender_id,
            )
        )

        result = self.conn.execute(treatment_endpoint_query).fetchall()
        endpoints_by_treatment = {row[0]: row[1] for row in result}

        return endpoints_by_treatment

    def fetch_active_expt_endpoint_urls(self, date: datetime.date | None = None) -> dict[UUID, str]:
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

    def fetch_active_expt_assignments(self, date: datetime.date | None = None) -> dict[UUID, Assignment]:
        assignments_tbl = self.tables["expt_assignments"]

        group_ids = self.fetch_active_expt_group_ids(date)

        group_query = select(
            assignments_tbl.c.assignment_id,
            assignments_tbl.c.account_id,
            assignments_tbl.c.group_id,
        ).where(
            and_(
                assignments_tbl.c.group_id.in_(group_ids),
                assignments_tbl.c.opted_out is not True,
            )
        )
        result = self.conn.execute(group_query).fetchall()
        group_lookup_by_account = {
            row.account_id: Assignment(
                assignment_id=row.assignment_id,
                account_id=row.account_id,
                group_id=row.group_id,
            )
            for row in result
        }

        return group_lookup_by_account

    def update_expt_assignment_to_opt_out(self, account_id: UUID) -> UUID | None:
        assignments_tbl = self.tables["expt_assignments"]

        group_ids = self.fetch_active_expt_group_ids()

        assignment_query = (
            update(assignments_tbl)
            .where(
                and_(
                    assignments_tbl.c.account_id == account_id,
                    assignments_tbl.c.group_id.in_(group_ids),
                    assignments_tbl.c.opted_out is False,
                )
            )
            .values(opted_out=True)
        )
        self.conn.execute(assignment_query)

    def fetch_dataset_by_assignment(self, assignment_id):
        dataset_table = self.tables["datasets"]
        experiment_table = self.tables["experiments"]
        group_table = self.tables["expt_groups"]
        assignment_table = self.tables["expt_assignments"]
        query = (
            select(dataset_table.c.dataset_id)
            .join(
                experiment_table,
                dataset_table.c.dataset_id == experiment_table.c.dataset_id,
            )
            .join(
                group_table,
                group_table.c.experiment_id == experiment_table.c.experiment_id,
            )
            .join(assignment_table, assignment_table.c.group_id == group_table.c.group_id)
            .where(assignment_table.c.assignment_id == assignment_id)
        )

        return self._id_query(query)[0]

    def fetch_account_alias(self, dataset_id, account_id):
        alias_table = self.tables["account_aliases"]
        query = select(alias_table.c.alias_id).where(
            and_(
                alias_table.c.account_id == account_id,
                alias_table.c.dataset_id == dataset_id,
            )
        )
        return self._id_query(query)[0]

    def _insert_experiment(self, dataset_id: UUID, experiment: Experiment) -> UUID | None:
        return self._insert_model(
            "experiments",
            experiment,
            addl_fields={
                "dataset_id": dataset_id,
                "team_id": experiment.owner.team_id,
            },
            exclude={"owner", "phases"},
            commit=False,
        )

    def _insert_expt_team(self, team: Team) -> UUID | None:
        team_id = self._insert_model("teams", team, exclude={"members"}, commit=False)
        for account_id in team.members:
            self._insert_team_membership(team_id, account_id)
        return team_id

    def _insert_team_membership(self, team_id: UUID, account_id: UUID) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["team_memberships"],
            {"team_id": team_id, "account_id": account_id},
            commit=False,
        )

    def _insert_expt_dataset(self, team: Team) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["datasets"],
            {"team_id": team.team_id},
            commit=False,
        )

    def _insert_expt_group(
        self,
        experiment_id: UUID,
        group: Group,
    ) -> UUID | None:
        return self._insert_model(
            "expt_groups",
            group,
            {"experiment_id": experiment_id, "group_name": group.name},
            exclude={"minimum_size", "name"},
            commit=False,
        )

    def _insert_expt_recommender(
        self,
        experiment_id: UUID,
        recommender: Recommender,
    ) -> UUID | None:
        return self._insert_model(
            "expt_recommenders",
            recommender,
            {
                "recommender_name": recommender.name,
                "experiment_id": experiment_id,
            },
            exclude={"name"},
            commit=False,
        )

    def _insert_expt_phase(
        self,
        experiment_id: UUID,
        phase: Phase,
    ) -> UUID | None:
        return self._insert_model(
            "expt_phases",
            phase,
            {"phase_name": phase.name, "experiment_id": experiment_id},
            exclude={"name", "treatments"},
            commit=False,
        )

    def _insert_expt_treatment(
        self,
        phase_id: UUID,
        treatment: Treatment,
    ) -> UUID | None:
        return self._insert_model(
            "expt_treatments",
            treatment,
            {
                "phase_id": phase_id,
                "group_id": treatment.group.group_id,
                "recommender_id": treatment.recommender.recommender_id,
            },
            exclude={"group", "recommender"},
            commit=False,
        )

    def _insert_account_alias(self, dataset_id: UUID, account: Account) -> UUID | None:
        return self._upsert_and_return_id(
            self.conn,
            self.tables["account_aliases"],
            values={
                "dataset_id": dataset_id,
                "account_id": account.account_id,
            },
            commit=False,
        )

    def _insert_expt_assignment(
        self,
        assignment: Assignment,
    ) -> UUID | None:
        return self._insert_model(
            "expt_assignments",
            assignment,
            commit=False,
        )


class S3ExperimentRepository(S3Repository):
    def fetch_manifest(self, manifest_file_key) -> ManifestFile:
        manifest_toml = self._get_s3_file(manifest_file_key)
        return parse_manifest_toml(manifest_toml)
