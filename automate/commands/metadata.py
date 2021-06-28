#!/usr/bin/env python
from automate.service.metadata import RawMetadata
from automate.service.metadata import IndexedMetadata

import click
import pandas as pd
from pathlib import Path
from datetime import date

pd.options.mode.chained_assignment = None  # default='warn'
echo = click.echo
DEFAULT_INFILE = r'D:\2021 Awards\2021 2. MENA Prize\MENA 2021 EDIT.xlsx'
# DEFAULT_INFILE = r"T:\Ascential Events\WARC\Backup Server\Loading\Monthly content for Newgen\Project content - May 2021\2021 Effectiveness Awards\WAFE_2021_EDIT.xlsx"
print('- Change DEFAULT INFILE:' + DEFAULT_INFILE)


class Context:
    CODES = {
        'effectiveness': 'WARC-AWARDS-EFFECTIVENESS',
        'mena': 'WARC-PRIZE-MENA',
        'asia': 'WARC-AWARDS-ASIA',
        'media': 'WARC-AWARDS-MEDIA'
    }

    def __init__(self, data: pd.DataFrame, file: Path):
        self.data = data
        self.file = file
        self.raw_metadata = RawMetadata(data, file)


def read_spreadsheet(excel_file, excel_sheet):
    """Get campaign details and add to dictionary."""
    df = pd.read_excel(
        excel_file, sheet_name=excel_sheet)  # ,encoding="utf-8"  # .fillna('')
    return df


@ click.group()
@ click.option(
    "-i",
    "-f",
    "--infile",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        readable=True, resolve_path=True
    ),
    default=DEFAULT_INFILE,
    show_default=True,
    required=True,
    help="The input excel file containing the relevant metadata.",
)
@ click.option(
    "-s",
    "--sheet",
    default=0,
    required=True,
    show_default=True,
    help="The sheet within the infile you want to read. This can be the name or an index.",
)
@ click.pass_context
def cli(ctx, infile, sheet):

    f = Path(infile)
    if f.suffix == ".xlsx":
        ctx.obj = Context(data=read_spreadsheet(f, sheet), file=f)
    else:
        print("--infile must be an xlsx file.")

    # echo('\nFINISHED\n')


@ cli.command()
@ click.pass_context
def index(ctx):
    """Writes only columns needed for indexing spreadsheet and collates agency details."""

    M = ctx.obj.raw_metadata
    M.index()


@ cli.command()
@ click.pass_context
def index_wafe(ctx):
    """Writes WAFE specific columns needed for indexing spreadsheet."""

    M = ctx.obj.raw_metadata
    M.index_wafe()


@ cli.command()
@ click.option(
    "-p",
    "--publication_date",
    type=click.DateTime(formats=["%d/%m/%Y", "%d-%m-%Y"]),
    required=True,
    show_default=True,
    default=date.today().strftime("%d-%m-%Y"),
    help="The publication date for entries. Default is today's date.",
)
@ click.option(
    "-c",
    "--code",
    required=True,
    type=click.Choice(Context.CODES.keys(), case_sensitive=False),
    help="Article source publication code:\n\n"+f"{list(Context.CODES.values())}",
)
@ click.pass_context
def upload(ctx, publication_date, code):
    """Generates article upload spreadsheet details."""
    publication_code = Context.CODES[code]
    M = ctx.obj.raw_metadata
    M.upload(publication_date, publication_code)


@ cli.command()
@ click.option(
    "-s/-w",
    "--shortlist/--winners",
    required=True,
    help="Choose between shortlist or winners spreadsheets.",
)
@ click.option(
    "-c/-p",
    "--csv/--press",
    required=True,
    help="Choose to csvs for landing pages or excel spreadsheets for press.",
)
@ click.option(
    "-a",
    "--award",
    required=True,
    type=click.Choice(Context.CODES.keys(), case_sensitive=False),
    help="Award scheme:\n\n"+f"{list(Context.CODES.keys())}",
)
@ click.option(
    "-d", "-o", "--destination",
    required=True,
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    help="Specify the destination for output. Must be a folder.",
)
@ click.pass_context
def winners(ctx, shortlist, csv, award, destination):
    """Writes specific metadata for circulating winners / shortlisted spreadsheets."""

    M = IndexedMetadata(ctx.obj.data, ctx.obj.file, destination)
    M(shortlist, csv)
