from datetime import date

from pydantic import BaseModel


class DailyStat(BaseModel):
    day: date
    newsletters_sent: int = 0
    clicks: int = 0