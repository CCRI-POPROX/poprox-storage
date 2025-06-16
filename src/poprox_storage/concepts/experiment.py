from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PositiveInt


class Team(BaseModel):
    team_id: UUID = Field(default_factory=uuid4)
    team_name: str
    members: list[UUID]


class Experiment(BaseModel):
    experiment_id: UUID = Field(default_factory=uuid4)
    dataset_id: UUID | None = None
    owner: Team | None = None
    description: str
    start_date: date
    end_date: date
    phases: list[Phase]

    @property
    def recommenders(self):
        """
        Deduplicates the experiment recommenders

        Since dictionaries maintain insertion order, adding the
        recommenders to a dictionary and then grabbing the values
        de-duplicates them without changing the order

        Returns
        -------
        List[Recommender]
            Unique experiment recommenders
        """
        return list(
            {
                treatment.recommender.name: treatment.recommender
                for phase in self.phases
                for treatment in phase.treatments
            }.values()
        )

    @property
    def groups(self):
        """
        Deduplicates the experiment groups

        Since dictionaries maintain insertion order, adding the
        groups to a dictionary and then grabbing the values
        de-duplicates them without changing the order

        Returns
        -------
        List[Group]
            Unique experiment groups
        """
        return list(
            {treatment.group.name: treatment.group for phase in self.phases for treatment in phase.treatments}.values()
        )


class Treatment(BaseModel):
    treatment_id: UUID = Field(default_factory=uuid4)
    group: Group
    recommender: Recommender
    template: str | None = Field(default=None)


class Group(BaseModel):
    group_id: UUID = Field(default_factory=uuid4)
    name: str
    minimum_size: PositiveInt


class Recommender(BaseModel):
    recommender_id: UUID = Field(default_factory=uuid4)
    name: str
    url: str


class Phase(BaseModel):
    phase_id: UUID = Field(default_factory=uuid4)
    name: str
    start_date: date
    end_date: date
    treatments: list[Treatment]

    @property
    def duration(self) -> timedelta:
        return self.end_date - self.start_date


class Assignment(BaseModel):
    assignment_id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    group_id: UUID
    opted_out: bool = Field(default=False)
