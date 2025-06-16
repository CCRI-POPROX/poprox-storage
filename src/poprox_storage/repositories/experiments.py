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
            "expt_treatments",
            "recommenders",
            "teams",
            "team_memberships",
        )

    def store_experiment(
        self,
        experiment: Experiment,
        assignments: dict[str, list[Account]],
        dataset_id: UUID,
    ):
        assignments = assignments or {}
        experiment_id = self._insert_experiment(dataset_id, experiment)

        for group in experiment.groups:
            group.group_id = self._insert_expt_group(experiment_id, group)
            for account in assignments.get(group.name, []):
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

    def fetch_experiment_by_id(self, experiment_id: str) -> Experiment | None:
        expt_table = self.tables["experiments"]

        expt_query = select(expt_table).where(expt_table.c.experiment_id == experiment_id)

        result = self.conn.execute(expt_query).first()
        if not result:
            return None

        expt = Experiment(
            experiment_id=result.experiment_id,
            dataset_id=result.dataset_id,
            description=result.description,
            start_date=result.start_date,
            end_date=result.end_date,
            team=None,
            phases=[],
        )

        # add team and phases
        expt.owner = self.fetch_team(result.team_id)
        expt.phases = self.fetch_experiment_phases(experiment_id)
        return expt

    def fetch_experiments_by_team(self, team_ids: list[UUID]) -> dict[UUID, Experiment]:
        expt_table = self.tables["experiments"]

        expt_query = select(expt_table).where(expt_table.c.team_id.in_(team_ids))

        result = self.conn.execute(expt_query).all()
        retval = {}
        for row in result:
            expt = Experiment(
                experiment_id=row.experiment_id,
                dataset_id=row.dataset_id,
                description=row.description,
                start_date=row.start_date,
                end_date=row.end_date,
                team=None,
                phases=[],
            )
            expt.owner = self.fetch_team(row.team_id)
            expt.phases = self.fetch_experiment_phases(row.experiment_id)
            retval[row.experiment_id] = expt
        return retval

    def fetch_experiment_phases(self, experiment_id: UUID) -> list[Phase]:
        treatment_table = self.tables["expt_treatments"]
        recommenders_table = self.tables["recommenders"]
        phases_table = self.tables["expt_phases"]

        recommenders = self.fetch_experient_recommenders(experiment_id)
        groups = self.fetch_experiment_groups(experiment_id)

        phase_query = select(phases_table).where(phases_table.c.experiment_id == experiment_id)
        phase_rows = self.conn.execute(phase_query).all()
        phases = {
            row.phase_id: Phase(
                phase_id=row.phase_id,
                name=row.phase_name,
                start_date=row.start_date,
                end_date=row.end_date,
                treatments=[],
            )
            for row in phase_rows
        }

        # build the treatments and add to phases
        treatment_query = (
            select(treatment_table)
            .join(
                recommenders_table,
                treatment_table.c.recommender_id == recommenders_table.c.recommender_id,
            )
            .where(recommenders_table.c.experiment_id == experiment_id)
        )
        treatment_rows = self.conn.execute(treatment_query).all()

        for row in treatment_rows:
            phases[row.phase_id].treatments.append(
                Treatment(
                    treatment_id=row.treatment_id,
                    group=groups.get(row.group_id),
                    recommender=recommenders.get(row.recommender_id),
                    template=row.template,
                )
            )

        return list(phases.values())

    def fetch_team(self, team_id: UUID) -> Team:
        team_table = self.tables["teams"]
        team_member_table = self.tables["team_memberships"]

        team_query = select(team_table).where(team_table.c.team_id == team_id)
        team_result = self.conn.execute(team_query).first()

        team_member_query = select(team_member_table).where(team_member_table.c.team_id == team_id)
        team_member_results = self.conn.execute(team_member_query).all()

        if team_result:
            return Team(
                team_id=team_id,
                team_name=team_result.team_name,
                members=[row.account_id for row in team_member_results],
            )
        else:
            return None

    def fetch_experiment_groups(self, experiment_id: UUID) -> dict[UUID, Group]:
        """Fetches all Group objects for an experiment.
        Returned dictionary maps group_id to recommender object."""
        groups_table = self.tables["expt_groups"]

        group_query = select(groups_table).where(groups_table.c.experiment_id == experiment_id)
        group_rows = self.conn.execute(group_query).all()
        # XXX: we do not currently store the minium size after ingesting an experiment.
        return {row.group_id: Group(group_id=row.group_id, name=row.group_name, minimum_size=1) for row in group_rows}

    def fetch_experient_recommenders(self, experiment_id: UUID) -> dict[UUID, Recommender]:
        """Fetches all Recommender objects for an experiment.
        Returned dictionary maps recommender_id to recommender object."""

        recommenders_table = self.tables["recommenders"]

        # get recommenders
        recommender_query = select(recommenders_table).where(recommenders_table.c.experiment_id == experiment_id)
        recommender_rows = self.conn.execute(recommender_query).all()
        return {
            row.recommender_id: Recommender(
                recommender_id=row.recommender_id, name=row.recommender_name, url=row.endpoint_url
            )
            for row in recommender_rows
        }

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

    def fetch_treatment_ids_by_experiment_id(self, experiment_id: UUID):
        treatments_tbl = self.tables["expt_treatments"]
        recommenders_tbl = self.tables["recommenders"]
        query = (
            select(treatments_tbl.c.treatment_id)
            .join(
                recommenders_tbl,
                treatments_tbl.c.recommender_id == recommenders_tbl.c.recommender_id,
            )
            .where(recommenders_tbl.c.experiment_id == experiment_id)
        )
        return self._id_query(query)

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

    def fetch_treatment_recommender_urls(self, treatment_ids: list[UUID]) -> dict[UUID, str]:
        recommenders_tbl = self.tables["recommenders"]
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

    def fetch_treatment_templates(self, treatment_ids: list[UUID]) -> dict[UUID, str]:
        treatments_tbl = self.tables["expt_treatments"]

        treatment_template_query = select(treatments_tbl.c.treatment_id, treatments_tbl.c.templates).where(
            treatments_tbl.c.treatment_id.in_(treatment_ids)
        )

        result = self.conn.execute(treatment_template_query).fetchall()
        templates_by_treatment = {row[0]: row[1] for row in result}

        return templates_by_treatment

    def fetch_active_expt_recommender_urls(self, date: datetime.date | None = None) -> dict[UUID, str]:
        groups_tbl = self.tables["expt_groups"]
        phases_tbl = self.tables["expt_phases"]
        recommenders_tbl = self.tables["recommenders"]
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
        group_ids = self.fetch_active_expt_group_ids(date)
        group_lookup_by_account = self._fetch_assignments_by_group_ids(group_ids)

        return group_lookup_by_account

    def fetch_assignments_by_experiment_id(self, experiment_id: UUID) -> dict[UUID, Assignment]:
        experiment = self.fetch_experiment_by_id(experiment_id)
        group_ids = [group.group_id for group in experiment.groups]
        group_lookup_by_account = self._fetch_assignments_by_group_ids(group_ids)

        return group_lookup_by_account

    def _fetch_assignments_by_group_ids(self, group_ids: list[UUID]) -> dict[UUID, Assignment]:
        assignments_tbl = self.tables["expt_assignments"]
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
            "recommenders",
            recommender,
            {
                "recommender_name": recommender.name,
                "experiment_id": experiment_id,
                "endpoint_url": recommender.url,
            },
            exclude={"name", "url"},
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
                "template": treatment.template,
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
        manifest_toml = self.fetch_file_contents(manifest_file_key)
        return parse_manifest_toml(manifest_toml)

    def store_as_parquet(
        self,
        experiment: Experiment,
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ) -> str:
        records = self._extract_and_flatten(experiment)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def _extract_and_flatten(self, experiment: Experiment) -> list[dict]:
        records = []
        for phase in experiment.phases:
            for treatment in phase.treatments:
                record = {}
                record["treatment_id"] = str(treatment.treatment_id)
                record["phase_id"] = str(phase.phase_id)
                record["phase_name"] = str(phase.name)
                record["group_id"] = str(treatment.group.group_id)
                record["group_name"] = str(treatment.group.name)
                record["recommender_id"] = str(treatment.recommender.recommender_id)
                record["recommender_name"] = str(treatment.recommender.name)
                record["recommender_url"] = str(treatment.recommender.url)
                records.append(record)

        return records


class S3AssignmentsRepository(S3Repository):
    def store_as_parquet(
        self,
        assignments: list[Assignment],
        bucket_name: str,
        file_prefix: str,
        start_time: datetime = None,
    ) -> str:
        records = self._extract_and_flatten(assignments)
        return self._write_records_as_parquet(records, bucket_name, file_prefix, start_time)

    def _extract_and_flatten(self, assignments: list[Assignment]) -> list[dict]:
        records = []
        for assignment in assignments:
            record = {}
            record["profile_id"] = str(assignment.account_id)
            record["group_id"] = str(assignment.group_id)
            record["opted_out"] = int(assignment.opted_out or False)
            records.append(record)

        return records
