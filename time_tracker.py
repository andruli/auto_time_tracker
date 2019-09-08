import re
import requests
from typing import List
from datetime import date, datetime, timedelta


ENDPOINT_LOGIN = 'default.aspx'
ENDPOINT_SUBMIT = 'CargaTimeTracker.aspx'
ENDPOINT_LIST = 'ListaTimeTracker.aspx'

LOGIN_KEY_USERNAME = 'ctl00$ContentPlaceHolder$UserNameTextBox'
LOGIN_KEY_PASSWORD = 'ctl00$ContentPlaceHolder$PasswordTextBox'
LOGIN_KEY_BUTTON = 'ctl00$ContentPlaceHolder$LoginButton'

SUBMIT_KEY_PROJECT = 'ctl00$ContentPlaceHolder$idProyectoDropDownList'
SUBMIT_KEY_DATE = 'ctl00$ContentPlaceHolder$txtFrom'
SUBMIT_KEY_HOURS = 'ctl00$ContentPlaceHolder$TiempoTextBox'
SUBMIT_KEY_ASSIGNMENT = 'ctl00$ContentPlaceHolder$idTipoAsignacionDropDownList'
SUBMIT_KEY_DESCRIPTION = 'ctl00$ContentPlaceHolder$DescripcionTextBox'
SUBMIT_KEY_FOCAL_POINT = 'ctl00$ContentPlaceHolder$idFocalPointClientDropDownList'
SUBMIT_KEY_SCRIPT_MANAGER = 'ctl00$ContentPlaceHolder$ScriptManager'
SUBMIT_KEY_PANEL = 'ctl00$ContentPlaceHolder$UpdatePanel1'
SUBMITE_KEY_BUTTON = 'ctl00$ContentPlaceHolder$btnAceptar'
SUBMIT_KEY_ASYNC_POST = '__ASYNCPOST'

LIST_KEY_START_DATE = 'ctl00$ContentPlaceHolder$txtFrom'
LIST_KEY_END_DATE = 'ctl00$ContentPlaceHolder$txtTo'

BUTTON_LOGGIN = 'Login'
BUTTON_ACCEPT = 'Accept'

DATE_FORMAT = '%d/%m/%Y'


class TimeTrackerException(Exception):
    pass


class TimeTrackerEntry:
    def __init__(self, date_str: str, hours: str, project: str, assignment: str, description: str, *args):
        try:
            self.date = datetime.strptime(date_str, DATE_FORMAT).date()
        except Exception:
            self.date = None
        self.hours = float(hours)
        self.project = project
        self.assignment = assignment
        self.description = description

    def __repr__(self):
        return (
            'TimeTrackerEntry'
            f'(hours={self.hours}, date={self.date}, project={self.project}, assignment={self.assignment})'
        )


class TimeTracker:
    def __init__(self, user, password):
        self.auth = (user, password)
        self._session = requests.Session()
        self._logged_in = False
        self._secrets = {}
        # Automatically log in
        self.login()

    def login(self):
        if self._logged_in:
            return

        response = self._call(ENDPOINT_LOGIN)
        data = {
            LOGIN_KEY_USERNAME: self.auth[0],
            LOGIN_KEY_PASSWORD: self.auth[1],
            LOGIN_KEY_BUTTON: BUTTON_LOGGIN,
        }

        response = self._call(ENDPOINT_LOGIN, method='post', form_data=data)

        if response.status_code != 200 or response.url.endswith(ENDPOINT_LOGIN):
            raise TimeTrackerException('Couldn\'t authenticate user')

        self._logged_in = True

    def submit_entry(
        self,
        hours: float,
        description: str,
        project: str,
        assignment: str,
        focal_point: str,
        day: date = date.today()
    ):
        """Creates a new entry in TT with the supplied parameters

        Example:
        self.submit(
            8,
            description="I've done a lot today",
            project='AdRoll - AdRoll',
            assignment='Software Development',
            focal_point='Robbie Holmes'
        )
        """
        response = self._call(ENDPOINT_SUBMIT)

        # Step 1: make sure the user can select the project.
        available_projects = self._get_select_options(SUBMIT_KEY_PROJECT, response.content)
        if project not in available_projects:
            raise TimeTrackerException(f'Project {project} is not available for the user')

        data = {
            SUBMIT_KEY_DATE: day.strftime(DATE_FORMAT),
            SUBMIT_KEY_PROJECT: available_projects[project],
            SUBMIT_KEY_HOURS: '',
            SUBMIT_KEY_ASSIGNMENT: '',
            SUBMIT_KEY_DESCRIPTION: '',
            SUBMIT_KEY_FOCAL_POINT: '',
        }

        validate_extra_data = {
            SUBMIT_KEY_SCRIPT_MANAGER: f'{SUBMIT_KEY_PANEL}|{SUBMIT_KEY_PROJECT}',
            SUBMIT_KEY_ASYNC_POST: True,
        }

        # Step 2: do a partial validation selecting the project.
        response = self._call(ENDPOINT_SUBMIT, method='post', form_data={**data, **validate_extra_data})

        # Step 3: validate user can select the assignment and focal point.
        available_assignments = self._get_select_options(SUBMIT_KEY_ASSIGNMENT, response.content)
        if assignment not in available_assignments:
            raise TimeTrackerException(f'Assignment {assignment} is not available for the user')

        available_focal_points = self._get_select_options(SUBMIT_KEY_FOCAL_POINT, response.content)
        if focal_point not in available_focal_points:
            raise TimeTrackerException(f'Focal point {focal_point} is not available for the user')

        data.update({
            SUBMIT_KEY_ASSIGNMENT: available_assignments[assignment],
            SUBMIT_KEY_FOCAL_POINT: available_focal_points[focal_point],
            SUBMIT_KEY_HOURS: hours,
            SUBMIT_KEY_DESCRIPTION: description,
            SUBMITE_KEY_BUTTON: BUTTON_ACCEPT,
        })

        # Submit the worked hours.
        response = self._call(ENDPOINT_SUBMIT, method='post', form_data=data)

        if response.status_code != 200 or not response.url.endswith(ENDPOINT_LIST):
            raise TimeTrackerException('Unable to submit worked hours')

    def list_entries(
        self,
        start_date: date = date.today() - timedelta(days = date.today().day),
        end_date: date = date.today()
    ) -> List[TimeTrackerEntry]:
        """Fetches all the submitted hours between the given dates.

        Example:
        self.list(
            date.today() - timedelta(days=10),
            date.today()
        )
        """
        self._call(ENDPOINT_LIST)
        response = self._call(
            ENDPOINT_LIST,
            method='post',
            form_data={
                LIST_KEY_START_DATE: start_date.strftime(DATE_FORMAT),
                LIST_KEY_END_DATE: end_date.strftime(DATE_FORMAT),
            }
        )

        content = str(response.content)
        table_re = re.compile('<table.*?>(.*?)</table>', re.DOTALL)
        table_row_re = re.compile('<tr.*?>(.*?)</tr>', re.DOTALL)
        table_column_re = re.compile('<td.*?>(.*?)</td>', re.DOTALL)

        rows = []

        table_content = next(table_re.finditer(content)).groups()[0]
        for i, row_match in enumerate(table_row_re.finditer(table_content)):
            if i == 0:
                # The first row contains the header
                continue
            row_content = row_match.groups()[0]
            row_data = [column_match.groups()[0] for column_match in table_column_re.finditer(row_content)]
            rows.append(TimeTrackerEntry(*row_data))

        # Remove the summary entry
        return rows[:-1]

    def _call(self, endpoint: str, query_params: dict = {}, form_data: dict = {}, method: str = 'get'):
        if method != 'get':
            # If we are using a method that accepts form data, send the secrets.
            form_data = {**self._secrets, **form_data}

        # We need to pass a user agent capable of loading web fragments.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/78.0.3891.0 Safari/537.36 Edg/78.0.266.0'
        }

        response = getattr(self._session, method)(
            f'https://timetracker.bairesdev.com/{endpoint}',
            params=query_params,
            data=form_data,
            headers=headers,
        )
        # Extract the secrets from the response
        self._extract_secrets(response.content)
        return response

    def _extract_secrets(self, response):
        response = str(response)
        input_re = re.compile('<input.*?/>')
        name_re = re.compile('name="([^\s]*)"')
        value_re = re.compile('value="([^\s]*)"')

        fields = {}

        for i in input_re.finditer(response):
            i = i.group()
            m = name_re.search(i)
            if m:
                name = m.groups()[0]
                value = ''

                m = value_re.search(i)
                if m:
                    value = m.groups()[0]

                fields[name] = value
        # Keep only the hidden items
        self._secrets = {k: v for k, v in fields.items() if k.startswith('__')}

    def _get_select_options(self, name, response):
        response = str(response)
        select_re = re.compile('<select.*?name="(.*?)".*?>(.*?)</select>', re.DOTALL)
        option_re = re.compile('<option.*?value="(.*?)".*?>(.*?)</option>', re.DOTALL)

        selects = {}

        for select_match in select_re.finditer(response):
            select_name, select_raw_options = select_match.groups()

            selects[select_name] = {}

            for option_match in option_re.finditer(select_raw_options):
                option_id, option_display_name = option_match.groups()

                selects[select_name][option_display_name] = option_id

        return selects.get(name, {})
