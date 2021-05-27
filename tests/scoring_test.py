import pytest
from automate.service.scoring import CollateScores, JudgeScores, CreateAsset


@pytest.fixture
def wf(example_data):
    pass
    # return WF(**example_data[0])


@pytest.fixture
def example_data():
    return [
        {
            "path": "",
            "ids": {
                123456: 654321,
                758844: 136623,
            },
            "name_format": "v0",
        },
    ]
