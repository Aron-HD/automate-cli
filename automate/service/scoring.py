from glob import glob
from pathlib import Path
import pandas as pd
from numpy import nan
from functools import reduce
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None


class CollateScores:
    """Collate all scoresheets in a given folder into a Consolidated marks spreadsheet."""

    def __init__(self, scoresheets_path, out_filename):
        self.scoresheets_path = Path(scoresheets_path)
        self.out_filename = self.scoresheets_path / f'{out_filename}.xlsx'
        self.all_dfs = []
        self.all_papers_scores = []
        self.all_papers_diving = []

    def group_all_scoresheets(self):
        grouped_dfs = []
        for scoresheet in self.scoresheets_path.glob('*GROUP*.xlsx'):
            print(scoresheet.name)
            JS = JudgeScores(scoresheet)
            JS.get_judge()
            JS.read_scores()
            modified_scores = JS.calculate_formulas()
            # modified_scores = JS.diving_scores()

            # ToDo:
            # - separate func calls
            # - concat formulas and store in self.judge_calculations

            output = modified_scores
            grouped_dfs.append(output)
        return grouped_dfs

    def merge_group_scores(self, group_frames):
        # get unique group values
        cols = JudgeScores.data_columns[:-1]  # ['ID', 'Ref', 'Paper']
        merged_group = reduce(
            lambda left, right: pd.merge(
                left, right.drop(cols, axis=1),
                left_index=True,
                right_index=True
            ), group_frames
        )

        def reduce_list(a: list, b: list):
            return list(set(a)-set(b))

        # get only judge score columns by removing ID, Ref and Paper
        judge_score_cols = reduce_list(merged_group.columns, cols)
        jsc = merged_group[judge_score_cols]
        # apply group level formulas and create columns
        merged_group['GroupAverageScore'] = jsc.mean(axis=1)

        diving_style_formula = \
            (jsc.sum(axis=1) -
             (jsc.min(axis=1) + jsc.max(axis=1))) / \
            (jsc.count(axis=1) - 2)

        merged_group['GroupDivingStyle'] = diving_style_formula

        def split_diving_style():
            # get only group score cols
            group_score_columns = reduce_list(
                merged_group.columns, judge_score_cols)
            gsc = merged_group[group_score_columns]
            # split scores and diving style
            rows = len(gsc.index)
            split = int(rows / 2)
            non_diving = gsc.iloc[:split, :]
            diving = gsc.iloc[split:, :]
            # append to separate lists to merge and rank separately
            self.all_papers_scores.append(non_diving)
            self.all_papers_diving.append(diving)

        split_diving_style()
        return merged_group

    def rank_scored_papers(self, pscores):
        apsc = pd.concat(pscores, axis='index')
        apsc['Rank'] = apsc['GroupAverageScore'].rank(ascending=False)
        apsc['DivingRank'] = apsc['GroupDivingStyle'].rank(ascending=False)
        apsc.sort_values('Rank', ascending=True, inplace=True)
        return apsc

    def concatenate_shortlist(self):
        straight = self.rank_scored_papers(self.all_papers_scores)
        diving = self.rank_scored_papers(self.all_papers_diving)
        col_order = ['GroupDivingStyle', 'DivingRank',
                     'GroupAverageScore', 'ID', 'Paper', 'Ref', 'Rank']

        # change col order and sort if straight DivingStyle calculates correctly
        if not straight['DivingRank'].isnull().values.any():
            straight.sort_values('DivingRank', ascending=True, inplace=True)
            alt_order = ['GroupAverageScore', 'Rank',
                         'GroupDivingStyle', 'ID', 'Paper', 'Ref', 'DivingRank']
            straight = straight[alt_order]
        else:
            straight = straight[col_order]

        col_order.reverse()
        diving = diving[col_order]
        diving.reset_index(drop=True, inplace=True)
        straight.reset_index(drop=True, inplace=True)
        diving.add_suffix('_alt')
        return pd.concat([straight, diving], axis=1)

    @staticmethod
    def format_scores(wkb, wks):

        wks.set_column('A:B', 14)
        wks.set_column('C:C', 55)  # set papers col widest
        wks.set_column('D:Z', 18)
        header_format = wkb.add_format(
            {'bold': True, 'bg_color': '#000000', 'font_color': '#ffffff'})
        scores_format = wkb.add_format({'bg_color': '#C6EFCE'})
        wks.conditional_format(
            'A1:Z1', {'type': 'no_blanks', 'format': header_format}
        )
        wks.conditional_format(
            'D2:Z200', {'type': 'no_blanks', 'format': scores_format}
        )

    def write_scores(self, n, writer):
        sh = f'Group {n}'
        print(sh)
        # filter dataframes with keys matching group number
        frames = list(filter(lambda fr: list(fr.keys())[0] == n, self.all_dfs))
        group_scores = [list(frm.values())[0] for frm in frames]
        merged_scores = self.merge_group_scores(group_scores)
        merged_scores.to_excel(writer, sheet_name=sh, index=False)
        return sh

    @staticmethod
    def format_shortlist(wkb, wks):
        pass

        # TODO:
        # - add width to papers column
        # - add conditional format to top 20 of each Ref col

    def write_shortlist(self, writer):
        shortlist_name = 'Shortlist calculation'
        shortlist = self.concatenate_shortlist()
        shortlist.to_excel(
            writer, sheet_name=shortlist_name, index=False)
        return shortlist_name

    def write_consolidated_marks(self):

        # make a list of unique group numbers
        groups = list(set(list(frm.keys())[0] for frm in self.all_dfs))

        with pd.ExcelWriter(self.out_filename) as xlwriter:
            workbook = xlwriter.book
            for num in groups:
                sheetname = self.write_scores(num, xlwriter)
                self.format_scores(workbook, xlwriter.sheets[sheetname])
            shortlist_sheet = self.write_shortlist(xlwriter)
            self.format_shortlist(workbook, xlwriter.sheets[shortlist_sheet])

    def __call__(self):
        self.all_dfs = self.group_all_scoresheets()
        self.write_consolidated_marks()
        return self.out_filename


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
                # Extract group integer from end of filename
                judge_info['Group'] = int(''.join(
                    filter(str.isdigit, judge_info['Group'])))
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
            """Find correct total score column recursively."""
            try:
                # convert so can hold NA
                res = score_rows.iloc[:, col].astype('float')
                if not res.isnull().all():
                    return res
                else:
                    return find_scores(col - 1)
            except IndexError:
                return find_scores(col - 1)
            except ValueError:
                return find_scores(col - 1)

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

        sc = self.judge_scores['Score']
        judge_formulas = {
            'JudgeCount': sc.count(),  # check if counts 0 and nan
            'JudgeAverage': sc.mean(),  # sc.sum()/count
            'JudgeMinmax': sc.max() - sc.min()
        }
        # add formulas to judge info dict
        self.judge.update(judge_formulas)
        # make formulas into dataframe for merging all
        # maybe make keys in 'Paper' col
        calcs = pd.DataFrame.from_dict(
            data={'ID': list(judge_formulas.keys(
            )), self.judge['Judge']: list(judge_formulas.values())},
        )
    # return calcs

        # ToDo:
        # - split to separate functions so can collate formulas and add at end

    # def diving_scores(self): ########################
        dfj = self.judge_scores

        def score_formula(s):
            return (s - self.judge['JudgeAverage']) / self.judge['JudgeMinmax']*100
        dfds = self.judge_scores.copy()
        dfds['Score'] = dfds['Score'].apply(score_formula)
        judge_diving_scores = pd.concat([dfj, dfds], axis=0)

        judge_diving_scores.rename(
            columns={'Score': self.judge['Judge']}, inplace=True
        )
        # print(judge_diving_scores)
        # df2.rename(
        #     columns={'Score': self.judge['Judge']}, inplace=True
        # )
        judge_diving_scores.reset_index(inplace=True, drop=True)
        # label dataframe with group number
        return {self.judge['Group']: judge_diving_scores}
        # else:
        #     return None

    def __call__(self):
        self.get_judge()


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

    scoresheets_path = r"T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2021 Awards\2. MENA Prize\Returned scoresheets"
    # scoresheets_path = r"C:\Users\arondavidson\Scripts\Test\2. MENA Prize\scoresheets"

    CS = CollateScores(scoresheets_path, '_Consolidated marks')
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
