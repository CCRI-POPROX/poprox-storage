from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, PositiveInt


class Experiment(BaseModel):
    experiment_id: Optional[UUID] = None
    description: str
    start_date: date
    end_date: date
    phases: List[Phase]

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
    group: Group
    recommender: Recommender


class Group(BaseModel):
    group_id: Optional[UUID] = None
    name: str
    minimum_size: PositiveInt


class Recommender(BaseModel):
    recommender_id: Optional[UUID] = None
    name: str
    endpoint_url: str


class Phase(BaseModel):
    phase_id: Optional[UUID] = None
    name: str
    start_date: date
    end_date: date
    treatments: List[Treatment]

    @property
    def duration(self) -> timedelta:
        return self.end_date - self.start_date


class Allocation(BaseModel):
    allocation_id: UUID
    account_id: UUID
    group_id: UUID
