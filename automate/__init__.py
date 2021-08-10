import json
from config import CUSTOM_INPUTS
from automate.settings import SETTINGS


with open('config.json', 'w') as j:
    jstr = json.dumps(CUSTOM_INPUTS, indent=4)
    j.write(jstr)
