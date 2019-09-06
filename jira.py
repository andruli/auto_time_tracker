import requests
from typing import List


class JiraTicket:
    def __init__(self, data):
        self.id: str = data['key']
        self.project: str = data['fields']['project']['name']
        self.status: str = data['fields']['status']['name']
        self.summary: str = data['fields']['summary'] or ''
        self.description: str = data['fields']['description'] or ''
        self._data = data

    def __repr__(self):
        return f'[{self.status}] {self.id}: {self.summary} '


class Jira:
    def __init__(self, user: str, email: str, token: str):
        self.auth = (email, token)
        self.user = user

    def search_tickets(self) -> List[JiraTicket]:
        # Queries are written in jira query language
        # https://www.atlassian.com/blog/jira-software/jql-the-most-flexible-way-to-search-jira-14
        response = self._call(
            'search', {
                'jql': f"""
                    assignee={self.user} AND
                    issuetype != Epic AND
                    resolution = Unresolved AND
                    status != Open AND
                    Sprint != EMPTY
                """
            }
        ).json()

        raw_issues = response.get('issues', [])

        return [JiraTicket(ri) for ri in raw_issues]

    def _call(self, endpoint: str, query_params: dict = {}, method: str = 'get'):
        return getattr(requests, method)(
            f'http://adroll.atlassian.net/rest/api/latest/{endpoint}',
            params=query_params,
            auth=self.auth,
        )
