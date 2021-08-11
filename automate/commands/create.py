#!/usr/bin/env python
import click
from automate.service.scoring import CreateAsset
from automate import SETTINGS


@click.command()
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
def cli(infile, path, outfile, award, create_type):
    """Create scoresheets, consolidated marks folder and spreadsheet or final picks spreadsheet."""

    click.echo(f'Creating: {create_type}')

    asset = CreateAsset(path, outfile, award, create_type, infile)
