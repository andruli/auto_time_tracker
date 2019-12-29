import pync

from os import path
from enum import Enum, auto

APPLICATION_NAME = 'TimeTracker'
ASSETS_FOLDER = 'assets'
ASSETS_PATH = path.join(path.dirname(path.abspath(__file__)), ASSETS_FOLDER)


class NotificationKind(Enum):
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


class NotificationLogo(Enum):
    SUCCESS = path.join(ASSETS_PATH, 'tt-logo.png')
    WARNING = path.join(ASSETS_PATH, 'tt-logo-warning.png')
    ERROR = path.join(ASSETS_PATH, 'tt-logo-error.png')


class NotificationSound(Enum):
    SUCCESS = 'Purr'
    WARNING = 'Sosumi'
    ERROR = 'Basso'

def notify(
    message: str,
    kind: NotificationKind = NotificationKind.SUCCESS,
):
    titleSuffix = kind.name.lower().capitalize() if kind != NotificationKind.SUCCESS else ''

    pync.notify(
        message,
        title=f'{APPLICATION_NAME}{f" - {titleSuffix}" if titleSuffix else ""}',
        appIcon=getattr(NotificationLogo, kind.name).value,
        sound=getattr(NotificationSound, kind.name).value,
    )
