from glob import glob
from pathlib import Path
import pandas as pd


class Collate:
    """docstring for Collate."""

    def __init__(self, data):
        self.data = data

    def write_csv(self, filename):
        self.data.to_csv(filename)
        return


class Scoresheet:
    """docstring for Scoresheet."""

    def __init__(self, scoresheet):
        self.scoresheet = Path(scoresheet)

    def read_scores(self):
        """Read the scores from the scoresheet and return a dataframe."""

        df = pd.read_excel(self.scoresheet, na_filter=False,
                           index_col=None, header=None)
        # get score rows only by seeing if ID integers are present
        score_rows = df[df[0].str.isdigit()]
        # paper cols
        ids, refs, papers = score_rows[0], score_rows[1], score_rows[2]

        def find_scores(col: int):
            # base case
            if all(score_rows.iloc[:, col].astype(str).str.isnumeric()):
                return score_rows.iloc[:, col]
            else:
                print(f'Scores not found in col: {col}')
                return find_scores(col - 1)

        # find total score col recursively
        totals = find_scores(col=9)

        score_data = pd.concat(
            [ids, refs, papers, totals], axis=1).reset_index(drop=True)

        # rename columns
        score_data.columns = ['ID', 'Ref', 'Paper', 'Score']

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
        return judge_info


if __name__ == '__main__':

    file = r'T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2020 Awards\2. MENA Prize\Returned scoresheets\Aakriti Goel - GROUP 2.xlsx'
    outfile = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize\test.csv'
    SS = Scoresheet(file)
    scores = SS.read_scores()
    judge = SS.get_judge()
    print(judge, scores.Score.array)
    # CS = Collate(scores)
    # if
