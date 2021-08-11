# from glob import glob
from pathlib import Path
from numpy import nan
from functools import reduce
from typing import List, Dict, Union
import pandas as pd
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None


class CollateScores:
    """Collate all scoresheets in a given folder into a Consolidated marks spreadsheet."""

    def __init__(self, scoresheets_path: Path, out_filename: str):
        self.scoresheets_path: Path = Path(scoresheets_path)
        self.out_filename: Path = self.scoresheets_path / f'{out_filename}.xlsx'
        self.all_dfs: List[pd.DataFrame] = []
        self.all_papers_scores: List[pd.DataFrame] = []
        self.all_papers_diving: List[pd.DataFrame] = []

    def group_all_scoresheets(self) -> List[pd.DataFrame]:
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

    def merge_group_scores(self, group_frames: List[pd.DataFrame]) -> None:
        # get unique group values
        cols = JudgeScores.data_columns[:-1]  # ['ID', 'Ref', 'Paper']
        merged_group = reduce(
            lambda left, right: pd.merge(
                left, right.drop(cols, axis=1),
                left_index=True,
                right_index=True
            ), group_frames
        )

        def reduce_list(a: List[str], b: List[str]) -> List[str]:
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

        def split_diving_style() -> None:
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

    @staticmethod
    def rank_scored_papers(pscores) -> pd.DataFrame:
        apsc = pd.concat(pscores, axis='index')
        apsc['Rank'] = apsc['GroupAverageScore'].rank(ascending=False)
        apsc['DivingRank'] = apsc['GroupDivingStyle'].rank(ascending=False)
        apsc.sort_values('Rank', ascending=True, inplace=True)
        return apsc

    def concatenate_shortlist(self) -> pd.DataFrame:
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
    def format_scores(wkb, wks) -> None:

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

    def write_scores(self, n: int, writer: pd.ExcelWriter) -> str:
        sh = f"Group {n}"
        # filter dataframes with keys matching group number
        frames = list(filter(lambda fr: list(fr.keys())[0] == n, self.all_dfs))
        group_scores = [list(frm.values())[0] for frm in frames]
        merged_scores = self.merge_group_scores(group_scores)
        merged_scores.to_excel(writer, sheet_name=sh, index=False)
        return sh

    @staticmethod
    def format_shortlist(wkb, wks) -> None:
        pass

        # TODO:
        # - add width to papers column
        # - add conditional format to top 20 of each Ref col

    def write_shortlist(self, writer: pd.ExcelWriter) -> str:
        shortlist_name = 'Shortlist calculation'
        shortlist = self.concatenate_shortlist()
        shortlist.to_excel(
            writer, sheet_name=shortlist_name, index=False)
        return shortlist_name

    def write_consolidated_marks(self) -> None:

        # make a list of unique group numbers
        groups = list(set(list(frm.keys())[0] for frm in self.all_dfs))

        with pd.ExcelWriter(self.out_filename) as xlwriter:
            workbook = xlwriter.book
            for num in groups:
                sheetname = self.write_scores(num, xlwriter)
                print(sheetname)
                self.format_scores(workbook, xlwriter.sheets[sheetname])
            shortlist_sheet = self.write_shortlist(xlwriter)
            self.format_shortlist(workbook, xlwriter.sheets[shortlist_sheet])

    def __call__(self) -> Path:
        self.all_dfs = self.group_all_scoresheets()
        self.write_consolidated_marks()
        return self.out_filename


class JudgeScores:
    """Read score data, judge details and calculations based on scores from scoresheet."""
    data_columns = ['ID', 'Ref', 'Paper', 'Score']

    def __init__(self, scoresheet: Path):
        self.scoresheet = Path(scoresheet)
        self.judge_scores = None
        self.judge: Dict[str, Union[str, int]] = {}

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
