from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from uuid import UUID, uuid4

import tomli
from pydantic import BaseModel, Field, PositiveInt

from poprox_storage.concepts.experiment import (
    Experiment,
    Group,
    Phase,
    Recommender,
    Team,
    Treatment,
)


class ManifestFile(BaseModel):
    """
    Parses and validates experiment manifest files that have
    been converted from TOML to Dict[str,Any] (e.g. using tomli)
    """

    experiment: ManifestExperiment
    owner: ManifestTeam
    users: ManifestGroupSpec
    recommenders: dict[str, ManifestRecommender]
    phases: ManifestPhases


class ManifestExperiment(BaseModel):
    id: UUID
    description: str
    duration: str
    start_date: date | None = None


class ManifestTeam(BaseModel):
    team_id: UUID
    team_name: str
    members: list[UUID]


class ManifestPhases(BaseModel):
    sequence: list[str]
    phases: dict[str, ManifestPhase]


class ManifestPhase(BaseModel):
    duration: str
    assignments: dict[str, ManifestPhaseAssignment]


class ManifestPhaseAssignment(BaseModel):
    recommender: str
    template: str | None = Field(default=None)


class ManifestRecommender(BaseModel):
    url: str


class ManifestGroupSpec(BaseModel):
    groups: dict[str, ManifestUserGroup]


class ManifestUserGroup(BaseModel):
    minimum_size: PositiveInt | None = None
    identical_to: str | None = None


def manifest_to_experiment(manifest: ManifestFile) -> Experiment:
    """
    Converts parsed manifest file to domain concept objects

    Resolves manifest fields into their corresponding domain
    fields, including duration into dates and identical groups
    into copies. Doesn't assign users to groups, which would
    require additional information about the state of the system
    beyond what's contained in the manifest.

    Parameters
    ----------
    manifest : ManifestFile
        A parsed experiment manifest as a Pydantic model

    Returns
    -------
    Experiment
        A transformed version of the manifest file as a domain object
    """
    # XXX: we probably should actually fix this later.
    start_date = manifest.experiment.start_date or (date.today() + timedelta(days=1))  # noqa: DTZ011
    # Include start date in the total duration
    end_date = start_date - timedelta(days=1) + convert_duration(manifest.experiment.duration) 

    owner = Team(
        team_id=manifest.owner.team_id,
        team_name=manifest.owner.team_name,
        members=manifest.owner.members,
    )

    experiment = Experiment(
        experiment_id=manifest.experiment.id,
        owner=owner,
        start_date=start_date,
        end_date=end_date,
        description=manifest.experiment.description,
        phases=[],
    )

    recommenders = {
        rec_name: Recommender(recommender_id=uuid4(), name=rec_name, url=recommender.url)
        for rec_name, recommender in manifest.recommenders.items()
    }

    groups = {}
    for group_name, group in manifest.users.groups.items():
        if group.identical_to:
            new_group = deepcopy(groups[group.identical_to])
            new_group.group_id = uuid4()
            new_group.name = group_name
            groups[group_name] = new_group
        else:
            groups[group_name] = Group(group_id=uuid4(), name=group_name, minimum_size=group.minimum_size)

    phase_start = start_date
    for phase_name in manifest.phases.sequence:
        manifest_phase = manifest.phases.phases[phase_name]
        duration = convert_duration(manifest_phase.duration)
        phase_start = start_date + sum([phase.duration for phase in experiment.phases], start=timedelta(0))
        phase_end = phase_start + duration
        phase = Phase(phase_id=uuid4(), name=phase_name, start_date=phase_start, end_date=phase_end, treatments=[])
        for group_name, assignment in manifest_phase.assignments.items():
            recommender_name = assignment.recommender
            phase.treatments.append(
                Treatment(
                    group=groups[group_name], recommender=recommenders[recommender_name], template=assignment.template
                )
            )
        experiment.phases.append(phase)

    return experiment


def convert_duration(duration: str) -> timedelta:
    quantity, unit = duration.split(" ")
    match unit:
        case unit if "week" in unit:
            delta = timedelta(weeks=int(quantity))
        case unit if "day" in unit:
            delta = timedelta(days=int(quantity))
        case _:
            msg = f"Unsupported duration unit: {unit}"
            raise ValueError(msg)
    return delta


def parse_manifest_toml(manifest_file: str):
    manifest_dict = tomli.loads(manifest_file)
    phases = {"sequence": manifest_dict["phases"]["sequence"], "phases": {}}
    for name, phase in manifest_dict["phases"].items():
        if name != "sequence":
            phases["phases"][name] = phase

    manifest_dict["phases"] = phases

    return ManifestFile.model_validate(manifest_dict)
