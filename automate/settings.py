import json
from pathlib import Path


DEFAULTS = {
    "CODES": {
        'effectiveness': 'WARC-AWARDS-EFFECTIVENESS',
        'mena': 'WARC-PRIZE-MENA',
        'asia': 'WARC-AWARDS-ASIA',
        'media': 'WARC-AWARDS-MEDIA'
    },
    "METADATA_INFILE": r"D:\2021 Awards\2021 2. MENA Prize\MENA 2021 EDIT.xlsx",
    # manually define DEFAULTS
}


class Settings:
    _config_location = 'config.json'

    def __init__(self):
        if Path(self._config_location).exists():
            self.__dict__ = json.load(open(self._config_location))
        else:
            print("Config doesn't exist - using DEFAULTS..")
            self.__dict__ = DEFAULTS


SETTINGS = Settings()
