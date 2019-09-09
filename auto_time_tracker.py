#!/usr/bin/env python3

import sys
from os import path
from datetime import date

from utils import get_config

from services.time_tracker import TimeTracker
from services.google_calendar import Calendar
from services.jira import Jira


def get_clients():
    config = get_config()

    jira_config = config['jira']
    tt_config = config['time_tracker']
    calendar_config = config.get('google_calendar', {})

    # Create the clients.
    jira_client = Jira(
        email=jira_config['email'],
        user=jira_config['user'],
        token=jira_config['token'],
    )
    tt_client = TimeTracker(
        user=tt_config['user'],
        password=tt_config['password'],
    )

    # Conditionally initialize google calendar if we have google calendar config.
    calendar_client = None

    if calendar_config and calendar_config.get('credentials'):
        secrets_file_path = calendar_config.get('credentials')
        secrets_file_path = secrets_file_path if \
            path.isabs(secrets_file_path) else path.join(path.dirname(__file__), secrets_file_path)

        calendar_client = Calendar(secrets_file_path)

    return tt_client, jira_client, calendar_client


def submit_time_tracker_entry():
    config = get_config()
    tt_config = config['time_tracker']

    tt_client, jira_client, calendar_client = get_clients()

    today = date.today()
    week_day = today.strftime('%a').lower()
    project = tt_config['project']
    assignment = tt_config['assignment']
    focal_point = tt_config['focal_point']
    hours = config.get('hours_per_day_override', {}).get(week_day, config['hours_per_day'])

    # Short circuit the script if this is not a working day.
    if week_day not in config['working_days']:
        print('Today is not a working day, bye bye')
        sys.exit(-1)

    # Short circuit the script if there's another entry already presnet.
    tt_entries = tt_client.list_entries(start_date=today, end_date=today)
    if any((e for e in tt_entries if e.date == today and e.assignment == assignment)):
        print('There is already an entry with the same assignment for this day')
        sys.exit(-1)

    # Use JIRA tickets to start the message.
    tickets = jira_client.search_tickets()

    # Add a line for each ticket we've been working on.
    tt_entry_description = '\n'.join([
        f'- {t.id}: {t.summary}'
        for t in tickets
    ])

    # If google calendar was configured, append the meetings we've attended to the tt description.
    if calendar_client:
        events = [evt for evt in calendar_client.list_events(today) if evt.accepted]
        # Add an entry for each meeting we've accepted.
        tt_entry_description = '\n'.join(
            [tt_entry_description] +
            [
                f'- Meeting "{evt.summary}" ({evt.human_readable_duration})'
                for evt in events
            ]
        )

    # Submit a tracker entry.
    tt_client.submit_entry(
        hours=hours,
        description=tt_entry_description,
        project=project,
        assignment=assignment,
        focal_point=focal_point,
        day=today,
    )

    print('Your hard work has been logged ;)')


if __name__ == '__main__':
    submit_time_tracker_entry()
