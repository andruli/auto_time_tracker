"""Google Calendar API.

This file is based on the official google calendar API samples: https://developers.google.com/calendar/quickstart/python
"""

import pickle
from os import path
from typing import List
from datetime import date, datetime, timezone, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_FILE = path.join(path.dirname(__file__), '.gcaltoken.pickle')

STATUS_CONFIRMED = 'confirmed'


class CalendarEvent:
    def __init__(self, raw_event: dict):
        self.id: str = raw_event['id']
        self.status: str = raw_event['status']
        self.link: str = raw_event.get('htmlLink')
        self.summary: str = raw_event.get('summary')
        self.description: str = raw_event.get('description')
        self.start_date: datetime = datetime.fromisoformat(raw_event['start']['dateTime'])
        self.end_date: datetime = datetime.fromisoformat(raw_event['end']['dateTime'])
        self._raw_event = raw_event

    @property
    def duration(self) -> timedelta:
        return self.end_date - self.start_date

    @property
    def human_readable_duration(self):
        def remove_unnecessary_decimal_places(n):
            if int(n) == n:
                return int(n)
            return n

        duration_minutes = remove_unnecessary_decimal_places(self.duration.total_seconds() / 60)
        duration_hours = remove_unnecessary_decimal_places(duration_minutes / 60)

        if duration_minutes < 60:
            return f'{duration_minutes} minute{"s" if duration_minutes != 1 else ""}'
        else:
            return f'{duration_hours} hour{"s" if duration_hours != 1 else ""}'

    def __repr__(self):
        return f'CalendarEvent(status={self.status}, summary={self.summary}, duration={self.human_readable_duration})'


class Calendar:
    def __init__(self, secrets_file):
        self.creds = None
        self.service = None

        self._load_credentials(secrets_file)

    def _load_credentials(self, secrets_file):
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time
        if path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)

        self.calendar = build('calendar', 'v3', credentials=self.creds)

    def list_events(self, day: date = date.today()) -> List[CalendarEvent]:
        min_date_local = datetime.combine(day, datetime.min.time()).astimezone()
        min_date = (min_date_local + min_date_local.tzinfo.utcoffset(min_date_local)).astimezone(timezone.utc)
        max_date = min_date + timedelta(days=1)

        events_result = self.calendar.events().list(
            calendarId='primary',
            timeMin=min_date.isoformat(),
            timeMax=max_date.isoformat(),
            showDeleted=False,
            singleEvents=True,
        ).execute()

        return [CalendarEvent(e) for e in events_result.get('items', [])]
