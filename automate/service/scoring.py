from glob import glob
from pathlib import Path
import pandas as pd
from natsort import natsorted


class Collate:
    """docstring for Collate."""

    def __init__(self, data):
        self.data = data

    def write_csv(self, filename):
        self.data.to_csv(filename)
        return


class JudgeScores:
    """Read score data, judge details and calculations based on scores from scoresheet."""

    def __init__(self, scoresheet):
        self.scoresheet = Path(scoresheet)
        self.judge_scores = None
        self.judge = {}

    def read_scores(self):
        """Read the scores from the scoresheet and return a dataframe."""

        df = pd.read_excel(self.scoresheet,  # na_filter=False,
                           index_col=None, header=None)
        # get score rows only by seeing if ID integers are present after filtered first col NaNs
        score_rows = df[df[0].fillna('').str.isdigit()]

        # ToDo - sort on ID

        def find_scores(col: int):
            # base case
            try:
                # convert so can hold NA
                return score_rows.iloc[:, col].astype('Int64')
            except IndexError:
                return find_scores(col - 1)

        # find total score col recursively
        totals = find_scores(col=10)
        # concat paper cols with total scores and drop index
        score_data = pd.concat(
            [score_rows[0], score_rows[1], score_rows[2], totals], axis=1).reset_index(drop=True)
        # rename columns
        score_data.columns = ['ID', 'Ref', 'Paper', 'Score']
        self.judge_scores = score_data
        return score_data

    def get_judge(self):
        """Get the judges name, group and category from the scoresheet."""

        info = self.scoresheet.stem.split(' - ')
        info_items = len(info)

        keys = ['Judge', 'Category', 'Group']

        if info_items == 3:
            judge_info = dict(zip(keys, info))
        elif info_items == 2:
            judge_info = dict(zip(keys, [info[0], None, info[1]]))
        else:
            print(f'Incorrect filename info from {self.file.name}', info)
            judge_info = None

        if judge_info:
            try:
                # Extract group integer from group string in filename
                judge_info['Group'] = int(
                    ''.join(filter(str.isdigit, judge_info['Group'])))

                self.judge.update(judge_info)
            except TypeError as e:
                raise e

        return judge_info

    def calculate_judge_formulas(self):

        if self.judge_scores is not None:

            sc = self.judge_scores.Score
            judge_formulas = {
                'ScoreCount': sc.count(),  # check if counts 0 and nan
                'ScoreAverage': sc.mean(),  # sc.sum()/count
                'ScoreMinmax': sc.max()-sc.min()
            }

            return self.judge.update(judge_formulas)
        else:
            return None


class CreateAsset(object):
    """docstring for CreateAsset"""
    JUDGES_COLS = ['Name', 'Surname', 'Company', 'Group']
    PAPER_COLS = ['PaperGroup', 'ID', 'Ref', 'Title']

    def __init__(self, path, outfile, award,
                 create_type, excel_file):
        self.path = path
        self.outfile = outfile
        self.award = award
        self.create_type = create_type
        self.excel_file = excel_file

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
            dfg[dfg[gc[0]] == n] for n in range(1, len(groups)+1)
        ]
        return enumerate(grouped_frames, start=1)

    def consolidated_marks(self, excel_sheet):
        """Make consolidated marks spreadsheet from main spreadsheet data."""
        frame1 = pd.read_excel(
            self.excel_file, sheet_name=excel_sheet)
        judges = self.get_groups(frame1, CreateAsset.JUDGES_COLS)
        papers = self.get_groups(frame1, CreateAsset.PAPER_COLS)

        # [print(index, judge) for index, judge in judges]
        # [print(index, p) for index, p in papers]

        # with ExcelWriter(self.outfile) as writer:

        # for index, group in papers:
        #     pass  # index, group

    def scoresheets(self, excel_sheet, category: str = None):
        """Make each group's scoresheets from main spreadsheet data."""
        frame2 = pd.read_excel(
            self.excel_file, sheet_name=excel_sheet)
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

            group.to_csv(Path(self.path) / fn)
            fns.append(fn)

        return fns

    def final_picks(self, excel_sheet):
        pass


if __name__ == '__main__':

    scoresheet_file = r"T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2020 Awards\2. MENA Prize\Returned scoresheets\Tarek El Kady - GROUP 3.xlsx"
    infile = r'D:\2021 Awards\2021 2. MENA Prize\MENA 2021 EDIT.xlsx'
    outfile = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize\test.csv'
    path = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize'
    DEFAULT_CREATE = 'marks'
    award = 'mena'
    sheetnum = 1
    JS = JudgeScores(scoresheet_file)
    JS.get_judge()
    JS.read_scores()
    JS.calculate_judge_formulas()
    print(JS.judge_scores)
    print(JS.judge)

    # CS = Collate(scores)
    # create = CreateAsset(
    #     path=path,
    #     award=award,
    #     outfile=outfile,
    #     excel_file=infile,
    #     create_type=DEFAULT_CREATE,
    # )

    # create.consolidated_marks(sheetnum)
    # print(create.scoresheets(sheetnum))
    # create.final_picks()
