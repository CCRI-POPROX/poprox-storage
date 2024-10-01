import logging
from datetime import datetime
from uuid import UUID

import sqlalchemy
from sqlalchemy import (
	Connection,
)

from poprox_concepts.domain import Demographics
from poprox_storage.repositories.data_stores.db import DatabaseRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DbDemographicsRepository(DatabaseRepository):
	def __init__(self, connection: Connection):
		super().__init__(connection)
		self.tables = self._load_tables(
			"demographics"
		)


	def store_demographics(self, demographic: Demographics) -> None:
		demographics_tbl = self.tables["demographics"]

		query = (
			sqlalchemy.insert(demographics_tbl)
			.values(
				account_id=demographic.account_id,
				gender=demographic.gender,
				birth_year=demographic.birth_year,
				zip5=demographic.zip5,
				education=demographic.education,
				race=demographic.race
			).returning(demographics_tbl.c.demographic_id)
		)
		row = self.conn.execute(query).fetchone()
		return row.demographic_id
		