# AutoTimeTracker
Are you tired of manually submiting TT entries every day? Well, so am I :) . Auto Time Tracker will automatically submit a time tracker entry using the JIRA tickets you've been working on.

## How to use?
- Install dependecies
```
pip install -r requirements.txt
```
- Fill the `config.json` file with information about your Jira account and your TimeTracker.
- Execute the script `auto_time_tracker.py`
- [Optional] add this script to a cron job that runs every day close to your EOD.

## Jira token
#### Why do we need them?
To use JIRA API with basic auth.

#### How to generate it
https://confluence.atlassian.com/cloud/api-tokens-938839638.html

## Google Calendar
AutoTimeTracker can pull your events from google calendar and include that information in the time tracker entry. To
enable the google calendar integration you have to follow these steps:
1. Go https://developers.google.com/calendar/quickstart/python and click on the `ENABLE GOOGLE CALENDAR API` entry.
2. Download the `credentials.json` file and store it in your machine.
3. Add an entry in the `config.json` pointing to the downloaded credentials file:
```
  ...
  "calendar": {
    "credentials_file": "my/credentials/file/path.json"
  }
  ...
```
4. Enable the google calendar API for your project. To to this you need to access the following link https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview?project=[projectID] replacing `projectID` with the ID of the project you created in step 1. If you are not sure what the id of your project is please examine the `credentials.json` file you downloaded in step 2 and look for the `client_id` property, the format of the property is `<projectId>-<extraData>`.
5. While running the application for the first time a web browser will be opened with an account selector. Select the account you want to use and grant read-only permissions to your calendar.
