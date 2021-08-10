#!/usr/bin/env python
import click
from automate.service.scoring import CollateScores
from automate.service.scoring import CreateAsset
from automate import SETTINGS


# class Context:
#     """docstring for Context"""

#     def __init__(self):
#         pass
# self.file
# self.collate = Collate()


@click.group()
@click.pass_context
def cli(ctx):
    """Scoring"""
    pass
    # ctx.obj = Context()


@cli.command()
@click.option(
    "-i", "--infile",
    required=True,
    show_default=True,
    default=SETTINGS.SCORING_INFILE,
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
    default=SETTINGS.SCORING_FILEPATH,
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True
    ),
    help="The root directory where you want to create the marks folder and spreadsheet.",
)
@click.option(
    '-o', '--outfile',
    required=False,
    show_default=True,
    default=SETTINGS.SCORING_OUTFILE,
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False,
    ),
    help="The name for the consolidated marks spreadsheet.",
)
@click.option(
    "-a", "--award",
    required=True,
    show_default=True,
    type=click.Choice(SETTINGS.AWARDS.keys(), case_sensitive=False),
    help="Select award scheme:\n\n"+f"{list(SETTINGS.AWARDS.values())}",
)
@click.option(
    "-c", "--create_type",
    required=True,
    default=SETTINGS.SCORING_CREATE,
    type=click.Choice(['scoresheets', 'marks', 'picks'], case_sensitive=False),
    help="Select what spreadsheets to create."
)
@click.pass_context
def create(ctx, infile, path, outfile, award, create_type):
    """Create scoresheets, consolidated marks folder and spreadsheet or final picks spreadsheet."""

    click.echo(f'Creating: {create_type} - {outfile}')

    asset = CreateAsset(path, outfile, award, create_type)


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
    default=SETTINGS.SCORING_SCORESHEETS,
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
