import json
from pathlib import Path
import click

DEFAULTS = {
    "CODES": {
        'effectiveness': 'WARC-AWARDS-EFFECTIVENESS',
        'mena': 'WARC-PRIZE-MENA',
        'asia': 'WARC-AWARDS-ASIA',
        'media': 'WARC-AWARDS-MEDIA'
    },
    "AWARDS": {
        # 'effectiveness': 'WARC Awards for Effectiveness',
        'mena': 'WARC Prize for MENA Strategy',
        'asia': 'WARC Awards for Asian Strategy',
        'media': 'WARC Awards for Media'
    },

    # set these to a test folder with example data

    # COMMANDS
    # command.metadata
    "METADATA_INFILE": r"C:\Users\arondavidson\Scripts\Python\automate\_incomplete\campaigndetails\testdata\Asia 2021 EDIT.xlsx",
    "METADATA_DESTINATION": r"C:\Users\arondavidson\OneDrive - Ascential\Desktop\TEST_metadata",
    # command.scoring
    "SCORING_INFILE": r'C:\Users\arondavidson\Scripts\Python\automate\_incomplete\campaigndetails\testdata\Asia 2021 EDIT.xlsx',
    "SCORING_FILEPATH": r'C:\Users\arondavidson\OneDrive - Ascential\Desktop\TEST_scoring',
    "SCORING_SCORESHEETS": r'T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2021 Awards\3. Asia Awards\Returned scoresheets',
    "SCORING_OUTFILE": 'Consolidated_marks.xlsx',
    "SCORING_CREATE": 'marks',
    # command.rename
    "RENAME_INFILE": r"T:\Ascential Events\WARC\Backup Server\Loading\Monthly content for Newgen\Project content - May 2021\2021 Effectiveness Awards\WAFE_2021_EDIT.xlsx",
    "RENAME_FILESPATH": r'C:\Users\arondavidson\Scripts\Test\_innovation',
    "RENAME_FILE": r'C:\Users\arondavidson\Scripts\Test\_innovation\758844_1714426_Entrypaper.docx',
    # SERVICE
    # service.rename class
    "WAFE_VTYPES": ["CaseFilm", "SupportingContent"],
    "WAFE_VFORMATS": [".mov", ".mp4"],
    "WAFE_IMGTYPE": "Entrypaper",
    # service.rename class
    "VFORMATS": [".mov", ".mp4", ".mk4", ".m4v"],
    "IMGFORMATS": [".jpg", ".png", ".jpeg", ".gif"],
    "DOCFORMATS": [".docx", ".htm", ".html"],
}


class Settings:
    _config_location = f'{Path(__file__).parents[0]}/config.json'

    def __init__(self):
        if Path(self._config_location).exists():
            DEFAULTS.update(json.load(open(self._config_location)))
            self.__dict__ = DEFAULTS
        else:
            print("Config doesn't exist - using DEFAULTS..")
            self.__dict__ = DEFAULTS


SETTINGS = Settings()
cs = SETTINGS.__dict__.copy()

[
    cs.pop(x) for x in [
        "AWARDS", "CODES",
        "WAFE_VTYPES", "WAFE_VFORMATS", "WAFE_IMGTYPE",
        "VFORMATS", "IMGFORMATS", "DOCFORMATS"
    ]
]


click.echo(click.style('\n### CUSTOM INPUTS ###', fg="cyan"))
[click.echo(click.style(f"\n -> {k} = {v}", fg="cyan")) for k, v in cs.items()]
