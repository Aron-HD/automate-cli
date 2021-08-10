from pathlib import Path
from dataclasses import dataclass
from typing import ClassVar, List
import pandas as pd
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None


@dataclass
class CreateAsset:
    """docstring for CreateAsset"""
    JUDGES_COLS: ClassVar[List[str]] = ['Name', 'Surname', 'Company', 'Group']
    PAPER_COLS: ClassVar[List[str]] = ['PaperGroup', 'ID', 'Ref', 'Title']

    path: Path
    outfile: Path = r'C:\Users\arondavidson\OneDrive - Ascential\Desktop\2021 Asia Awards\test.csv'
    award: str
    create_type: str
    excel_file: Path

    @staticmethod
    def get_groups(frame: pd.DataFrame, cols: list):
        """
        Split papers or judges into separate groups returned as an enumerated list of dataframes.
        """
        dfg = frame[cols].dropna(axis=0)
        gc = list(filter(lambda col: 'Group' in col, cols))
        dfg[gc[0]] = dfg[gc[0]].astype(int)
        # get unique group values
        groups = list(dfg[gc[0]].unique())
        print(groups)
        # filter papers by group, n+1 as mismatch of group start at 1 vs index 0
        grouped_frames = [
            dfg[dfg[gc[0]] == n] for n in range(1,
                                                len(groups) + 1)
        ]
        return enumerate(grouped_frames, start=1)

    def consolidated_marks(self, excel_sheet):
        """Make consolidated marks spreadsheet from main spreadsheet data."""
        frame1 = pd.read_excel(self.excel_file, sheet_name=excel_sheet)
        judges = self.get_groups(frame1, CreateAsset.JUDGES_COLS)
        papers = self.get_groups(frame1, CreateAsset.PAPER_COLS)

        # [print(index, judge) for index, judge in judges]
        # [print(index, p) for index, p in papers]

        # with ExcelWriter(self.outfile) as writer:

        # for index, group in papers:
        #     pass  # index, group

    def scoresheets(self, excel_sheet, category: str = None):
        """Make each group's scoresheets from main spreadsheet data."""
        frame2 = pd.read_excel(self.excel_file, sheet_name=excel_sheet)
        grouped_papers = self.get_groups(frame2, CreateAsset.PAPER_COLS)

        fns = []

        for index, group in grouped_papers:
            fn = f"WARC {self.award} Scoresheet - {category} - GROUP {index}.csv" \
                if category else f"WARC {self.award.upper()} Scoresheet - GROUP {index}.csv"

            # TODO
            # - ExcelWriter
            # - add formula TotalScores Sum column
            # - add styles and width to titles column

            # set multiple indexes to merge
            group.set_index(['ID', 'Ref'], inplace=True)
            group.drop(['PaperGroup'], axis=1, inplace=True)
            group.sort_values(by=['ID'], inplace=True)

            group.to_csv(Path(self.path) / fn, encoding='cp1252')
            fns.append(fn)

        return fns

    def final_picks(self, excel_sheet):
        pass
