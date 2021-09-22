#!/usr/bin/env python

import click
import pandas as pd
from pathlib import Path
from datetime import date
from openpyxl.styles import PatternFill, Border, Side, colors
from pandas.core.computation.ops import UndefinedVariableError

pd.options.mode.chained_assignment = None  # default='warn'
echo = click.echo


class RawMetadata:
    """
    Produces spreadsheets for indexing team from registration data
    and also metadata for article upload sheet used for batch creation of CMS articles.
    """

    def __init__(self, data: pd.DataFrame, file: Path):
        self.data = data
        self.file = file
        self.year = date.today().strftime("%Y")

    def index(self):
        """Writes only columns needed for indexing spreadsheet and collates agency details."""
        try:
            keep = [
                'ID', 'Award Reference', 'Award Name', 'Shortlisted', 'Budget', 'Campaign Duration',
                'Award Title', 'Brand', 'Brand Owner Name', 'Lead Agency (1)',
                'Lead Agency (2)', 'Contributing Agency (1)',
                'Contributing Agency (2)', 'Contributing Agency (3)',
                'Contributing Agency (4)', 'Holding Group', 'Countries'
                # , 'Country'
            ]
            df = self.data
            df2 = df[keep]

            def comma_join(x):
                return ', '.join(x[x.notnull()])

            df2['Lead Agencies'] = df[['Lead Agency (1)',
                                       'Lead Agency (2)']].apply(comma_join, axis=1)
            df2['Contributing Agencies'] = df[[
                'Contributing Agency (1)', 'Contributing Agency (2)',
                'Contributing Agency (3)', 'Contributing Agency (4)'
            ]].apply(comma_join, axis=1)

            keep2 = [
                'ID', 'Award Reference', 'Award Name', 'Shortlisted', 'Award Title', 'Brand', 'Brand Owner Name', 'Budget',
                'Campaign Duration', 'Lead Agencies', 'Contributing Agencies', 'Countries'
            ]

            df3 = df2[keep2]

            # ToDo: metadata file name / add in category or shortlist etc
            edit = self.file
            index = edit.parent / edit.name.replace('EDIT', 'Metadata')
            echo('Wrote: ' + str(index))
            return df3.to_excel(index, index=False)

        except KeyError as e:
            echo(click.style('KEY ERROR check headers', fg="red"))
            echo(e)
            return None

    def index_wafe(self):
        """Writes WAFE specific columns needed for indexing spreadsheet."""
        try:
            keepcols = [
                'Entry Type',
                'TBEntryId',
                'WarcID',
                'Brand',
                'Title',
                'Article Title',
                'Advertiser',
                'Product',
                'Duration of Campaign',
                'Budget',
                'Location/Region',
                'Entrant Company',
                'Entrant Country',
                'Entrant City',
                'Idea creation',
                'Production ',
                'Media ',
                'PR ',
            ]
            edit_xl = self.file
            index_xl = edit_xl.parent / \
                edit_xl.name.replace('EDIT', 'metadata')
            # ToDo: switch to openpyxl
            with pd.ExcelWriter(index_xl, engine='xlsxwriter') as writer:

                wafe_df = self.data
                index_sheet = wafe_df[keepcols]

                # sort categories
                categories = sorted(list(index_sheet['Entry Type'].unique()))

                for i in categories:

                    cat_sheet = index_sheet[index_sheet['Entry Type'] == i]
                    cat_sheet.to_excel(writer, index=False, sheet_name=i)
                    echo('\tWrote sheet: ' + i)

                # space columns
                for sheet in writer.sheets:
                    writer.sheets[sheet].set_column('A:R', 20)

            echo(str(index_xl.name))

        except KeyError as e:
            echo(click.style('KEY ERROR check headers', fg="red"))
            echo(e)
            return None

    def upload(self, publication_date, code):
        """Generates article upload spreadsheet details."""

        df = self.data
        df3 = df[['Award Reference']]

        author_fields = [('Author First Name (1)', 'Author Last Name (1)'),
                         ('Author First Name (2)', 'Author Last Name (2)'),
                         ('Author First Name (3)', 'Author Last Name (3)')]
        # join first and last name for each author with space
        keys = []
        for index, names in enumerate(author_fields, start=1):
            key = f'Author{index}'
            df3[key] = df[[names[0],
                           names[1]]].apply(lambda x: ' '.join(x[x.notnull()]),
                                            axis=1)
            keys.append(key)
        # join each full author name with comma
        df3['Authors'] = df3[[*keys]].apply(lambda x: ', '.join(x[x != '']),
                                            axis=1)

        # Title
        df3['Title'] = df[['Brand',
                           'Award Title']].apply(lambda x: ': '.join(x[x.notnull()]), axis=1)
        df3['Publication code'] = code
        df3['Issue'] = self.year
        df3['Pub Date'] = publication_date.strftime("%d-%m-%Y")
        df3[['DOI', 'PageFrom', 'PageTo', 'Notes']] = None
        df3['Content Type'] = 'Case Study'

        # write only needed data to new dataframe
        df4 = df3[['Award Reference', 'Publication code', 'Issue', 'Pub Date',
                   'Title', 'Authors', 'DOI', 'PageFrom', 'PageTo', 'Notes', 'Content Type']]

        edit = self.file
        index = edit.parent / 'Upload.xlsx'
        echo('Wrote: ' + str(index))
        return df4.to_excel(index, index=False)


class IndexedMetadata(RawMetadata):
    """
    Produces reports for awards press announcements / internal circulation, 
    as well as csv sheets for winners / shortlists that are used by landing page generator.
    """
    cols = {
        'id': 'ID',
        'award title': 'Title',
        'brand': 'Brand',
        'brand owner name': 'Parent',
        'lead agencies': 'Lead',
        'contributing agencies': 'Contributing',
        'countries': 'Market',
        'industry sector': 'Sector',
    }
    alt_cols = {
        'warcid': 'ID',
        'article title': 'Title',
        'brand': 'Brand',
        'advertiser': 'Parent',
        'entrant company': 'Entrant',
        'idea creation': 'Idea',
        'media': 'Media',
        'pr': 'PR',
        'entrant country': 'Country',
        'location/region': 'Market',
        'industry sector': 'Sector',
    }
    content_codes = {
        'mena': 'WARC-PRIZE-MENA',
        'effectiveness': 'WARC-AWARDS-EFFECTIVENESS',
        'asia': 'WARC-AWARDS-ASIA',
        'media': 'WARC-AWARDS-MEDIA',
    }

    def __init__(self, data, file, award, destination):
        super().__init__(data, file)
        self.destination = destination
        self.data = data.fillna('')
        # lowercase for case insensitivity
        self.data.columns = map(str.lower, self.data.columns)
        self.award = award
        # setup dependent on prize / award having categories

        if award == "effectiveness":
            self.data.sort_values(
                by='Category',
                inplace=True,
                ignore_index=True
            )
            self.categories = data['Category'].unique()
            self.cols = IndexedMetadata.alt_cols
            self.ID = 'warcid'
        else:
            # print(e)  # log
            self.categories = [award]
            self.cols = IndexedMetadata.cols
            self.ID = 'id'
        self.meta_cols = list(self.cols.keys())
        self.csv_cols = list(self.cols.values())
        self.award_cols = ['tier', 'special award', 'award']
        self.winner_cols = self.meta_cols.copy()
        [self.winner_cols.insert(0, x) for x in self.award_cols]

    @staticmethod
    def get_award_code(awd) -> str:
        award_name = awd.lower()
        cc = IndexedMetadata.content_codes
        return cc[award_name]

    def rename_cols(self, dframe, csv: bool):
        if csv:
            cols_to_rename = self.cols
        else:
            required_fields = ['Article Title', 'Award Title',
                               'Advertiser', 'Brand owner', 'Countries', 'Location/Region']
            cols_to_rename = {k: v for k,
                              v in self.cols.items() if k in required_fields}
        dframe.rename(columns=cols_to_rename, inplace=True)

    def prep_csv(self, dfc, shortlist: bool):
        self.rename_cols(dfc, csv=True)
        dropcols = ['Country', 'Sector', 'Idea', 'Media', 'PR']

        dfc2 = dfc[self.csv_cols] if shortlist else dfc[self.award_cols + self.csv_cols]

        content_code = self.get_award_code(self.award)
        dfc2['Link'] = f'/content/article/{content_code}/_/'
        dfc2['Link'] = dfc2['Link'].astype(str) + dfc2['ID'].astype(str)
        for col in dropcols:
            try:
                dfc2.drop([col], axis=1)
            except KeyError:
                pass
        return dfc2

    def prep_shortlist(self, dfs, csv_true: bool):
        # ToDo: switch to prep_csv()
        dfs.sort_values(by=self.ID, inplace=True, ignore_index=True)
        dfs1 = dfs[self.meta_cols]
        return self.prep_csv(dfs1, True) if csv_true else dfs1

    def prep_winners(self, dfw, csv_true: bool):
        # ToDo: switch to prep_excel()
        dfw.sort_values(
            by='tier',
            ascending=False,
            inplace=True,
            ignore_index=True
        )

        dfw1 = dfw[self.winner_cols]
        # drop Special Award, Tier
        dropcols = self.award_cols.copy()
        # dont drop Award
        dropcols.remove('award')
        self.rename_cols(dfw1, csv_true)
        if csv_true:
            dropcols.remove('special award')
            dfw1 = self.prep_csv(dfw1, False)
        else:
            dropcols += [self.ID]  # drop WarcID
            # concat special awards masking blank cells
            mask = dfw1['special award'] == ''
            dfw1['award'] = dfw1['award'].where(
                mask, dfw1[['award', 'special award']].agg(' + '.join, axis=1)
            )
        # drop shortlisted entries that didn't win special award (a + sa)
        dfwo = dfw1 if csv_true else dfw1.query(
            '"+" in award or award!="Shortlisted"')
        return dfwo.drop(dropcols, axis=1)

    @staticmethod
    def format_excel(ws):
        # format the column widths dynamically
        dims = {}
        for row in ws.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max(
                        (dims.get(cell.column_letter, 0), len(str(cell.value))))
                # format fill and border while looping through cells
                thin = Side(border_style="thin", color="000000")
                cell.fill = PatternFill("solid", fgColor="FFFFFF")
                cell.border = Border(top=thin, left=thin,
                                     right=thin, bottom=thin)

        for col, value in dims.items():
            ws.column_dimensions[col].width = value

    def write_excel(self, frame, filename: str):
        try:
            fn = self.destination / Path(f'WARC {filename} - {self.year}').with_suffix('.xlsx')
            with pd.ExcelWriter(fn, engine='openpyxl') as writer:
                frame.to_excel(writer, sheet_name=filename, index=False)
                worksheet = writer.sheets[filename]
                self.format_excel(worksheet)
            return fn.name
        except Exception as e:
            raise e

    def write_csv(self, frame, filename: str):
        try:
            fn = self.destination / Path(filename).with_suffix('.csv')
            frame.to_csv(fn, index=False, encoding='utf-8')
            return fn.name
        except Exception as e:
            raise e

    @staticmethod
    def split_category_name(name):
        outliers = ['Business', 'Culture', 'Partnerships', 'Channel']
        if not any(i in name for i in outliers):
            c = name.split()
        else:
            for i in outliers:
                if i in name:
                    return i
        if len(c) > 1:
            return c[1]
        return c[0]

    def __call__(self, shortlist: bool, csv: bool):

        try:

            for cat in self.categories:
                try:
                    df = self.data.query(f'Category=="{cat}"')
                except UndefinedVariableError:
                    df = self.data
                if csv:
                    cat = self.split_category_name(cat)

                if shortlist:
                    win_type = 'shortlist'
                    cat_winners = self.prep_shortlist(df, csv)
                else:
                    win_type = 'winners'
                    cat_winners = self.prep_winners(df, csv)

                fnm = ' '.join([cat, win_type])

                if csv:
                    alt_fnm = fnm.replace(' ', '_').lower()
                    output_name = self.write_csv(
                        frame=cat_winners, filename=alt_fnm)
                else:
                    # cat_winners['Location/Region'] = cat_winners['Market']
                    output_name = self.write_excel(
                        frame=cat_winners, filename=fnm)

                echo('\n\t wrote: ' + click.style(output_name, fg='green'))

        except KeyError as e:
            echo("\nCheck headers")
            echo(click.style(str(e), fg="red"))
            raise e
