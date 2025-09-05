"""
Experiment Manifest Parser

This module provides functionality for parsing and validating experiment manifest
files in TOML format anf converting them into domain concept objects. The manifest
files define experiment configurations including phases, user groups, recommenders,
and assignments.
"""

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
    Parses and validates experiment manifest files that have been converted
    from TOML to Dict[str,Any] (e.g. using tomli).

    Attributes:
        experiment: Experiment metadata and configuration
        owner: Experiment team owner
        users: Specification of user groups participating in the experiment
        recommenders: Dictionary mapping recommender names to their configurations
        phases: Sequence of experiment phases
    """

    experiment: ManifestExperiment
    owner: ManifestTeam
    users: ManifestGroupSpec
    recommenders: dict[str, ManifestRecommender]
    phases: ManifestPhases


class ManifestExperiment(BaseModel):
    """
    Experiment metadata and configuration.

    Defines the basic properties of an experiment including its id,
    description, duration, and optional
    start date.

    Attributes:
        id: Unique identifier for the experiment
        description: Human-readable description of the experiment
        duration: Experiment duration in string format (e.g., "2 weeks", "5 days")
        start_date: Optional start date. If None, defaults to tomorrow
    """

    id: UUID
    description: str
    duration: str
    start_date: date | None = None


class ManifestTeam(BaseModel):
    """
    Information of the team that owns and manages the experiment,
    including team id and members.

    Attributes:
        team_id: Unique identifier for the team
        team_name: Human-readable team name
        members: List of UUIDs representing team members
    """

    team_id: UUID
    team_name: str
    members: list[UUID]


class ManifestPhases(BaseModel):
    """
    Container for experiment phase configuration.

    Manages the sequence of phases and their individual configurations.

    Attributes:
        sequence: List of phase names
        phases: Dictionary mapping phase names to their configurations
    """

    sequence: list[str]
    phases: dict[str, ManifestPhase]


class ManifestPhase(BaseModel):
    """
    Configuration for a single experiment phase.

    Defines the duration and group assignments for a specific phase
    of the experiment.

    Attributes:
        duration: Phase duration in string format (e.g., "1 week", "3 days")
        assignments: Dictionary mapping group names to their phase assignments
    """

    duration: str
    assignments: dict[str, ManifestPhaseAssignment]


class ManifestPhaseAssignment(BaseModel):
    """
    Assignment of a group to a recommender during a phase.

    Specifies which recommender a particular group will use during
    a phase, along with optional template configuration.

    Attributes:
        recommender: Name of the recommender to use for this assignment
        template: Optional template specification for the recommender
    """

    recommender: str
    template: str | None = Field(default=None)


class ManifestRecommender(BaseModel):
    """
    Configuration for a recommender system.

    Attributes:
        url: URL endpoint for the recommender
    """

    url: str


class ManifestGroupSpec(BaseModel):
    """
    Specification of user groups for the experiment.

    Attributes:
        groups: Dictionary mapping group names to their specifications
    """

    groups: dict[str, ManifestUserGroup]


class ManifestUserGroup(BaseModel):
    """
    Specification for a single user group.

    Defines the configuration for a user group, including size constraints
    and the ability to create identical copies of existing groups.

    Attributes:
        minimum_size: Optional minimum number of users required in the group
        identical_to: Optional name of another group to copy configuration from
    """

    minimum_size: PositiveInt | None = None
    identical_to: str | None = None


def manifest_to_experiment(manifest: ManifestFile) -> Experiment:
    """
    Convert parsed manifest file to domain concept objects.

    Resolves manifest fields into their corresponding domain
    fields, including duration into dates and identical groups
    into copies. Doesn't assign users to groups, which would
    require additional information about the state of the system
    beyond what's contained in the manifest.

    Args:
        manifest: A parsed experiment manifest as a Pydantic model

    Returns:
        Experiment: A transformed version of the manifest file as a domain object
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
    """
    Convert duration string to timedelta object.

    Supported formats:
    - "N week" or "N weeks" (where N is an integer)
    - "N day" or "N days" (where N is an integer)

    Args:
        duration: Duration on string format (e.g., "2 weeks", "5 days")

    Returns:
        timedelta: Equvalent timedelta object
    """
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
    """
    Takes raw TOML content as a string, parses it, and restructures the
    phases section to match the expected ManifestFile schema.

    Args:
        manifest_file: Raw TOML content as a string

    Returns:
        ManifestFile: Validated and parsed manifest file object
    """
    manifest_dict = tomli.loads(manifest_file)
    phases = {"sequence": manifest_dict["phases"]["sequence"], "phases": {}}
    for name, phase in manifest_dict["phases"].items():
        if name != "sequence":
            phases["phases"][name] = phase

    manifest_dict["phases"] = phases

    return ManifestFile.model_validate(manifest_dict)
