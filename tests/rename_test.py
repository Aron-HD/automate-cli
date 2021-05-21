import pytest
from automate.service.rename import WafeFilenames as WF


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
        [
            "758844_1714426_Entrypaper.jpg",
            # "758844_1714478_CaseFilm.mp4",
            # "759126_1710376_Appendix.pdf",
            # "759126_1735578_CaseFilm.mp4",
            # "759126_1735618_SupportingContent.mp4",
            # "759126_1735683_SupportingContent.mp4",
            # "759418_1719665_Appendix.pdf",
        ],
        {
            '137444': {
                '1714424': {
                    'type': 'SupportingContent',
                    'ext': '.mk4'
                },
                '1714425': {
                    'type': 'SupportingContent',
                    'ext': '.mp4'
                },
                '1714426': {
                    'type': 'CaseFilm',
                    'ext': '.mov'
                },
                '1714427': {
                    'type': 'Entrypaper',
                    'ext': '.docx'
                },
                '1714428': {
                    'type': 'Appendix',
                    'ext': '.pdf'
                },
                '1714429': {
                    'type': 'SupportingContent',
                    'ext': '.jpg'
                }
            }
        }
    ]


@pytest.fixture
def wf(example_data):
    return WF(**example_data[0])


def test_lookup_wafe_id(wf):

    assert wf.lookup_wafe_id(123456) == 654321
    assert wf.lookup_wafe_id(1) == None
    assert wf.lookup_wafe_id('123456') == None


def test_split_stem(wf):
    assert wf.analyse_parts([758844, 1714426,
                             'Entrypaper']) == [136623, 1714426, 'Entrypaper']


def test_order_filenames(wf, example_data):
    assert wf.order_filenames(example_data[2]) == [
        '137444a01-SupportingContent.mk4', '137444v02.mp4', '137444v01.mov',
        '137444a02-SupportingContent.jpg'
    ]
    assert wf.order_filenames({}) == []
