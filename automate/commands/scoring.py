#!/usr/bin/env python
import click
from automate.service.scoring import CollateScores
from automate.service.scoring import CreateAsset


class Context:
    """docstring for Context"""
    DEFAULT_INFILE = r'D:\2021 Awards\2021 2. MENA Prize\MENA 2021 EDIT.xlsx'
    DEFAULT_SCORESHEETS = r'T:\Ascential Events\WARC\Public\WARC.com\Editorial\Awards (Warc)\2021 Awards\2. MENA Prize\Returned scoresheets'
    DEFAULT_FILEPATH = r'C:\Users\arondavidson\Scripts\Test\2. MENA Prize'
    DEFAULT_MARKS = 'Consolidated_marks.csv'
    DEFAULT_CREATE = 'marks'
    AWARDS = {
        # 'effectiveness': 'WARC Awards for Effectiveness',
        'mena': 'WARC Prize for MENA Strategy',
        'asia': 'WARC Awards for Asian Strategy',
        'media': 'WARC Awards for Media'
    }

    def __init__(self):
        pass
        # self.file
        # self.collate = Collate()


@click.group()
@click.pass_context
def cli(ctx):
    """Scoring"""
    ctx.obj = Context()


@cli.command()
@click.option(
    "-i", "--infile",
    required=True,
    show_default=True,
    default=Context.DEFAULT_INFILE,  # remove later
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        readable=True, resolve_path=True
    ),
    help="The input excel file containing the relevant metadata.",
)
@click.option(
    '-p', '--path',
    required=True,
    show_default=True,
    default=Context.DEFAULT_FILEPATH,  # remove later
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True
    ),
    help="The root directory where you want to create the marks folder and spreadsheet.",
)
@click.option(
    '-o', '--outfile',
    required=True,
    show_default=True,
    default=Context.DEFAULT_MARKS,  # remove later
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False,
    ),
    help="The name for the consolidated marks spreadsheet.",
)
@click.option(
    "-a", "--award",
    default="mena",  # remove later
    required=True,
    show_default=True,  # remove later
    type=click.Choice(Context.AWARDS.keys(), case_sensitive=False),
    help="Select award scheme:\n\n"+f"{list(Context.AWARDS.values())}",
)
@click.option(
    "-c", "--create_type",
    required=True,
    default=Context.DEFAULT_CREATE,
    type=click.Choice(['scoresheets', 'marks', 'picks'], case_sensitive=False),
    help="Select what spreadsheets to create."
)
@click.pass_context
def create(ctx, infile, path, outfile, award, create_type):
    """Create scoresheets, consolidated marks folder and spreadsheet or final picks spreadsheet."""

    click.echo(f'Creating: {create_type} - {outfile}')

    asset = CreateAsset(path, outfile, award, create_type)
    pass


@cli.command()
@click.option(
    "-o", "--output_file",
    required=True,
    show_default=True,
    default='_Consolidated marks',
    help="The name for the excel spreadsheet you want output in.",
)
@click.option(
    '-p', '--path',
    required=True,
    show_default=True,
    default=Context.DEFAULT_SCORESHEETS,  # remove later
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True
    ),
    help="The root directory where you want to create the marks folder and spreadsheet.",
)
@click.pass_context
def shortlist(ctx, output_file, path):
    """Collate shortlist scoresheets from directory into output consolidated marks."""

    CS = CollateScores(path, output_file)
    output = CS()
    msg = f'Wrote: {output}'
    click.echo(msg)
