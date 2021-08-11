#!/usr/bin/env python
import click
from automate.service.scoring import CollateScores
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
