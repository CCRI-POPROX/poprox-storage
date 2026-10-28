from collections import Counter
from datetime import date, datetime, time, timedelta

from poprox_concepts.api.click_filtering import filter_click_histories
from poprox_storage.concepts.daily_stats import DailyStat

from poprox_storage.repositories.data_stores.db import DatabaseRepository
from poprox_storage.repositories.newsletters import DbNewsletterRepository
from poprox_storage.repositories.accounts import DbAccountRepository
from poprox_storage.repositories.clicks import DbClicksRepository

class DbDailyStatsRepository(DatabaseRepository):
    def __init__(self, connection):
        super().__init__(connection)
        self.account_repo = DbAccountRepository(connection)
        self.newsletter_repo = DbNewsletterRepository(connection)
        self.click_repo = DbClicksRepository(connection)

    def fetch_daily_stats(self, start: date, end: date, include_all: bool = False) -> list[DailyStat]:
        if end < start:
            raise ValueError("Provide a valid date range")
        
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        empty = [DailyStat(day=d) for d in days]

        accounts = self.account_repo.fetch_accounts()
        if not include_all:
            accounts = [a for a in accounts if a.external]
        if not accounts:
            return empty
        
        newsletters = self.newsletter_repo.fetch_newsletter_dates_between(
            start_date=datetime.combine(start, time.min),
            end_date=datetime.combine(end, time.max),
            account_ids=[a.account_id for a in accounts],
        )
        if not newsletters:
            return empty
        

        clicks_by_account = self.click_repo.fetch_clicks_by_newsletter_ids(
            [newsletter.newsletter_id for newsletter in newsletters]
        )
        clicks_by_account = filter_click_histories(clicks_by_account)

        clicks_per_newsletter = Counter(
            click.newsletter_id for clicks in clicks_by_account.values() for click in clicks
        )

        sent = Counter()
        clicks_by_day = Counter()
        for newsletter in newsletters:
            day = newsletter.created_at.date()
            sent[day] += 1
            clicks_by_day[day] += clicks_per_newsletter[newsletter.newsletter_id]

        return [DailyStat(day=d, newsletter_sent=sent[d], clicks=clicks_by_day[d]) for d in days]
        



