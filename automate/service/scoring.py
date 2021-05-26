from glob import glob
from pathlib import Path
import pandas as pd
from numpy import nan
from functools import reduce
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None


class CollateScores:
    """docstring for Collate."""

    def __init__(self, scoresheets_path, out_filename):
        self.scoresheets_path = Path(scoresheets_path)
        self.out_filename = Path(r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize') / f'{out_filename}.xlsx'
        self.data = None

    def write_sheet(self):
        new_file = self.out_filename
        self.data.to_csv(new_file)
        return ''.join(['Wrote: ', new_file.name])

    def group_all_scoresheets(self):
        grouped_dfs = []
        for scoresheet in self.scoresheets_path.glob('*GROUP*.xlsx'):
            print(scoresheet.name)
            JS = JudgeScores(scoresheet)
            JS.get_judge()
            JS.read_scores()
            modified_scores = JS.calculate_formulas()
            # modified_scores = JS.diving_scores()

            # modified_scores.reset_index(inplace=True, drop=True)
            # output = JS()
            grouped_dfs.append(output)
        return grouped_dfs

    def merge_group_scores(self, group_frames):
        # get unique group values
        df_merged = reduce(
            lambda left, right: pd.merge(
                left, right,
                left_index=True,
                right_index=True,
                on=JudgeScores.data_columns[:-1]  # ['ID', 'Ref', 'Paper']
            ), group_frames
        )
        return df_merged
        # return pd.concat(group_frames, axis=1, join='inner')

    def __call__(self):

        all_dfs = self.group_all_scoresheets()
        groups = list(set(frm.iloc[0, 3] for frm in all_dfs))

        with pd.ExcelWriter(self.out_filename, engine='xlsxwriter') as writer:
            wkb = writer.book
            for n in groups:
                print(n)
                frames = list(filter(lambda fr: fr.iloc[0, 3] == n, all_dfs))
                merged_scores = self.merge_group_scores(frames)
                sheetname = f'Group {n}'
                merged_scores.to_excel(
                    writer, sheet_name=sheetname, index=False)
                wks = writer.sheets[sheetname]
                # set papers col widest
                col_format = wkb.add_format(
                    {'bg_color': '#000000', 'font_color': '#ffffff'})
                # wks.conditional_format(
                #     'A1:C200', {'type': 'no_blanks', 'format': col_format})

                wks.set_column('A:B', 14)
                wks.set_column('C:C', 55)
                wks.set_column('D:Z', 18)

                header_format = wkb.add_format({'bold': True})
                wks.set_row(0, None, header_format)

                wks.conditional_format(
                    'A1:Z1', {'type': 'no_blanks', 'format': col_format})
                scores_format = wkb.add_format({'bg_color': '#C6EFCE'})
                wks.conditional_format(
                    'D3:Z200', {'type': 'no_blanks', 'format': scores_format})
                # self.data = merged_scores
                # self.write_sheet()
                # break


class JudgeScores:
    """Read score data, judge details and calculations based on scores from scoresheet."""
    data_columns = ['ID', 'Ref', 'Paper', 'Score']

    def __init__(self, scoresheet):
        self.scoresheet = Path(scoresheet)
        self.judge_scores = None
        self.judge = {}

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
            print(f'Incorrect filename info from {self.scoresheet.name}', info)
            judge_info = None

        if judge_info:
            try:
                # Extract group integer from group string in filename
                judge_info['Group'] = int(''.join(
                    filter(str.isdigit, judge_info['Group'])))
                # set name of df = self.judge['Group']

                self.judge.update(judge_info)
            except TypeError as e:
                raise e

        return judge_info

    def read_scores(self):
        """Read the scores from the scoresheet and return a dataframe."""

        df = pd.read_excel(self.scoresheet, index_col=None, header=None)
        # get score rows only by seeing if ID integers are present after filtered first col NaNs
        score_rows = df[df[0].fillna(nan).astype(str).str.isdigit()]

        # ToDo - sort on ID

        def find_scores(col: int):
            # base case
            try:
                # convert so can hold NA
                return score_rows.iloc[:, col].astype('float')
            except IndexError:
                return find_scores(col - 1)

        # find total score col recursively
        totals = find_scores(col=9)
        # concat paper cols with total scores and drop index
        score_data = pd.concat(
            [score_rows[0], score_rows[1], score_rows[2], totals],
            axis=1).reset_index(drop=True)
        # rename columns
        score_data.columns = JudgeScores.data_columns

        self.judge_scores = score_data
        return score_data

    def calculate_formulas(self):

        dfj = self.judge_scores

        if dfj is not None:
            sc = dfj.Score  # self.judge_scores['Score']
            # build a Series with scores
            judge_formulas = {
                'JudgeCount': sc.count(),  # check if counts 0 and nan
                'JudgeAverage': sc.mean(),  # sc.sum()/count
                'JudgeMinmax': sc.max() - sc.min()
            }
            # append forumlas to judge dict
            self.judge.update(judge_formulas)
            # make the formulas into a dataframe
            # maybe make keys in 'Paper' col
            calcs = pd.DataFrame.from_dict(
                data={'ID': list(judge_formulas.keys(
                )), self.judge['Judge']: list(judge_formulas.values())},
            )
        # return calcs
            # set dfj name as group
            group = pd.DataFrame.from_dict(
                data={0: ['Group', '', '', self.judge['Group']]},
                orient='index',
                columns=JudgeScores.data_columns,
                dtype=object
            )
            # concatenate them later in CollateScores
            df2 = pd.concat([group, dfj, calcs], axis=0)

        # def diving_scores(self): ########################

            def score_formula(s):
                return (s - self.judge['JudgeAverage']) / self.judge['JudgeMinmax']*100
            # dfj = self.judge_scores
            dfj['Score'] = dfj['Score'].apply(score_formula)
            judge_diving_scores = pd.concat([df2, dfj], axis=0)

            judge_diving_scores.rename(
                columns={'Score': self.judge['Judge']}, inplace=True
            )
            # df2.rename(
            #     columns={'Score': self.judge['Judge']}, inplace=True
            # )

            return judge_diving_scores
        else:
            return None

    def __call__(self):
        # move to Collate Class
        self.get_judge()
        # self.read_scores()
        # modified_scores = self.calculate_formulas()
        # modified_scores.reset_index(inplace=True, drop=True)
        # return modified_scores


class CreateAsset(object):
    """docstring for CreateAsset"""
    JUDGES_COLS = ['Name', 'Surname', 'Company', 'Group']
    PAPER_COLS = ['PaperGroup', 'ID', 'Ref', 'Title']

    def __init__(self, path, outfile, award, create_type, excel_file):
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

            group.to_csv(Path(self.path) / fn)
            fns.append(fn)

        return fns

    def final_picks(self, excel_sheet):
        pass


if __name__ == '__main__':

    infile = r'D:\2021 Awards\2021 2. MENA Prize\MENA 2021 EDIT.xlsx'
    outfile = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize\test.csv'
    path = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize'
    DEFAULT_CREATE = 'marks'
    award = 'mena'
    sheetnum = 1

    # scoresheets_path = r"T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2021 Awards\2. MENA Prize\Returned scoresheets"
    scoresheets_path = r"C:\Users\arondavidson\Scripts\Test\2. MENA Prize\scoresheets"

    CS = CollateScores(scoresheets_path, DEFAULT_CREATE)
    CS()
    # CS.write_csv(outfile)

    # frame_output = pd.merge(*groups, how='outer', on=['ID', 'Ref', 'Paper'])
    # print(d.columns)

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
