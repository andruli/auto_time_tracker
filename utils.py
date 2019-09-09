import json
from os import path

__config = None


def get_config():
    if __config:
        return __config
    else:
        return json.load(
            open(
                path.join(
                    path.dirname(__file__),
                    'config.json'
                )
            )
        )
