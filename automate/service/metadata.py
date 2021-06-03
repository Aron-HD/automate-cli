#!/usr/bin/env python

import click
import pandas as pd
from pathlib import Path
from datetime import date

pd.options.mode.chained_assignment = None  # default='warn'
echo = click.echo


class RawMetadata:
    def __init__(self, data: pd.DataFrame, file: Path):
        self.data = data
        self.file = file

    def index(self):
        """Writes only columns needed for indexing spreadsheet and collates agency details."""
        try:
            keep = [
                'ID', 'Award Reference', 'Budget', 'Campaign Duration',
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
                'ID', 'Award Reference', 'Award Title', 'Brand', 'Brand Owner Name', 'Budget',
                'Campaign Duration', 'Lead Agencies', 'Contributing Agencies', 'Countries'
            ]

            df3 = df2[keep2]

            # print(df3.columns)
            # metadata file name / add in category or shortlist etc
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
            # open writer
            with pd.ExcelWriter(index_xl, engine='xlsxwriter') as writer:

                wafe_df = self.data
                # echo(wafe_df.columns.array)
                index_sheet = wafe_df[keepcols]

                # sort categories
                categories = sorted(list(index_sheet['Entry Type'].unique()))

                for i in categories:
                    # echo(i)
                    cat_sheet = index_sheet[index_sheet['Entry Type'] == i]
                    # echo(cat_sheet.shape)
                    cat_sheet.to_excel(writer, index=False, sheet_name=i)
                    echo('\tWrote sheet: ' + i)

                # space columns
                for sheet in writer.sheets:
                    writer.sheets[sheet].set_column('A:R', 20)

                # writer.save()
            echo(str(index_xl.name))

        except KeyError as e:
            echo(click.style('KEY ERROR check headers', fg="red"))
            echo(e)
            return None

    # Codes for input options and Article Source

    def upload(self, publication_date, code):
        """Generates article upload spreadsheet details."""

        df = self.data
        df3 = df[['Award Reference']]

        # Authors
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
        df3['Issue'] = date.today().strftime("%Y")
        df3['Pub Date'] = publication_date.strftime("%d-%m-%Y")
        df3[['DOI', 'PageFrom', 'PageTo', 'Notes']] = None
        df3['Content Type'] = 'Case Study'

        # write only needed data to new dataframe
        df4 = df3[['Award Reference', 'Publication code', 'Issue', 'Pub Date',
                   'Title', 'Authors', 'DOI', 'PageFrom', 'PageTo', 'Notes', 'Content Type']]

        echo(df4.shape)

        edit = self.file
        index = edit.parent / 'Upload.xlsx'
        echo('Wrote: ' + str(index))
        return df4.to_excel(index, index=False)


class IndexedMetadata(RawMetadata):
    """docstring for IndexedMetadata"""
    keep_cols = [
        'Article Title',
        'Brand',
        'Advertiser',
        'Entrant Company',
        'Entrant Country',
        'Location/Region',
        'Idea creation',
        'Media',
        'PR',
        'Industry sector'
    ]

    def __init__(self, data, file, destination):
        super().__init__(data, file)
        self.destination = destination
        self.categories = data['Category'].unique()
        self.data = data.fillna('')
        self.data['Location/Region'] = self.data['Market']
        self.data.sort_values(
            by='Category',
            inplace=True,
            ignore_index=True
        )
        additional_cols = ['Tier', 'Special Award', 'Award']
        self.winner_cols = IndexedMetadata.keep_cols.copy()
        [self.winner_cols.insert(0, x) for x in additional_cols]

    def prep_shortlist(self, dfs):
        dfs.sort_values(by='WarcID', inplace=True, ignore_index=True)
        return dfs[IndexedMetadata.keep_cols]

    def prep_winners(self, dfw):
        dfw.sort_values(
            by='Tier',
            ascending=False,
            inplace=True,
            ignore_index=True
        )
        dfw1 = dfw[self.winner_cols]
        dfwo = dfw1.query('`Special Award`!="" or Award!="Shortlisted"')
        # drop tier as only used for sorting
        return dfwo.drop('Tier', axis=1)

    def __call__(self, shortlist, csv):

        for cat in self.categories:
            df = self.data.query(f'Category=="{cat}"')

            if csv:
                if shortlist:
                    pass
                elif not shortlist:
                    pass
            elif not csv:
                if shortlist:
                    cat_winners = self.prep_shortlist(df)
                    fnm = f'{cat} shortlist.xlsx'
                elif not shortlist:
                    cat_winners = self.prep_winners(df)
                    fnm = f'{cat} winners.xlsx'
                # self.write_winners(cat_winners, fnm)
            break


if __name__ == '__main__':

    DEFAULT_INFILE = r"T:\Ascential Events\WARC\Backup Server\Loading\Monthly content for Newgen\Project content - May 2021\2021 Effectiveness Awards\WAFE_2021_EDIT.xlsx"
    data = pd.read_excel(DEFAULT_INFILE, sheet_name='Winners')
    s = True
    c = False
    d = r"C:\Users\arondavidson\OneDrive - Ascential\Desktop\TEST_metadata"
    IM = IndexedMetadata(data, DEFAULT_INFILE, d)
    IM(s, c)
