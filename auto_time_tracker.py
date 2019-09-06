#!/usr/bin/env python3

import sys
from datetime import date

from utils import get_config
from time_tracker import TimeTracker
from jira import Jira


def submit_time_tracker_entry():
    config = get_config()

    jira_client = Jira(
        email=config['jira']['email'],
        user=config['jira']['user'],
        token=config['jira']['token'],
    )
    tt_client = TimeTracker(
        user=config['time_tracker']['user'],
        password=config['time_tracker']['password'],
    )
    today = date.today()
    week_day = today.strftime('%a').lower()
    project = config['time_tracker']['project']
    assignment = config['time_tracker']['assignment']
    focal_point = config['time_tracker']['focal_point']

    hours = config.get('hours_per_day_override', {}).get(week_day, config['hours_per_day'])
    extra_task = config.get('tasks_append', {}).get(week_day)

    tickets = jira_client.search_tickets()

    tt_entry_description = '\n'.join([
        f'-[{t.id}]: {t.summary}'
        for t in tickets
    ])

    # Add a new entry for the extra task
    if extra_task:
        tt_entry_description = '\n'.join([tt_entry_description, extra_task])

    # Check this is a working day
    if week_day not in config['working_days']:
        print('Today is not a working day, bye bye')
        sys.exit(-1)

    # Check no other entries with the same assignment exists for this day
    tt_entries = tt_client.list_entries(start_date=today, end_date=today)

    if any((e for e in tt_entries if e.date == today and e.assignment == assignment)):
        print('There is already an entry with the same assignment for this day')
        sys.exit(-1)

    # Submit a tracker entry
    tt_client.submit_entry(
        hours=hours,
        description=tt_entry_description,
        project=project,
        assignment=assignment,
        focal_point=focal_point,
        day=today,
    )

    # Verify the entry was properly created
    tt_entries = tt_client.list_entries(start_date=today, end_date=today)

    if not any((e for e in tt_entries if e.date == today and e.assignment == assignment and e.hours == hours)):
        print('The entry does not seem to have been created properly')
        sys.exit(-1)

    print('Your hard work has been logged ;)')


if __name__ == '__main__':
    submit_time_tracker_entry()
