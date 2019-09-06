# AutoTimeTracker
Are you tired of manually submiting TT entries every day? Well, so am I :) . Auto Time Tracker will automatically submit a time tracker entry using the JIRA tickets you've been working on.

### How to use?
1. Fill the `config.json` file with information about your Jira account and your TimeTracker.
2. Execute the script `auto_time_tracker.py`
3. [Optional] add this script to a cron job that runs every day close to your EOD.

### Jira token
#### Why do we need them?
To use JIRA API with basic auth.

#### How to generate it
https://confluence.atlassian.com/cloud/api-tokens-938839638.html

### Next steps
- Google calendar sync. Log all your meetings to TT.
