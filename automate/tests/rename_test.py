import pytest
from automate.service.rename import WafeFilenames as WF


@pytest.fixture
def example_data():
    return {
        "path": "",
        "ids": {
            123456: 654321
        },
        "name_format": "v0",
    }


def test_lookup_wafe_id(example_data):

    wf = WF(**example_data)
    wf.lookup_wafe_id(123456) == False