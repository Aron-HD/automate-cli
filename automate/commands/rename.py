import click
import pandas as pd
from automate.service import rename

DEFAULT_INFILE = r"T:\Ascential Events\WARC\Backup Server\Loading\Monthly content for Newgen\Project content - May 2021\2021 Effectiveness Awards\WAFE_2021_EDIT.xlsx"
DEFAULT_FILESPATH = r'D:\2021 Awards\2021 1. Effectiveness Awards\RENAMETEST'
DEFAULT_FILE = r'D:\2021 Awards\2021 1. Effectiveness Awards\RENAMETEST\758812_1710344_CaseFilm.mp4'


def get_ids(excelfile, sheet):
    """Returns id numbers from excel sheet."""
    df = pd.read_excel(excelfile, sheet_name=sheet).fillna(0)
    # read columns and allow user to select
    click.echo('Select headers:')
    cols = dict(enumerate(df.columns.values))
    [click.echo(f'\t {k} - {v}') for k, v in cols.items()]
    from_ids = click.prompt(
        'select col index to rename from', type=int)
    to_ids = click.prompt(
        'select col index to rename to', type=int)

    col1 = cols[from_ids]
    col2 = cols[to_ids]
    # has to be int to avoid float numbers
    ids = dict(zip(df[col1].astype(
        str).tolist(), df[col2].astype(str).tolist()))
    return ids


@click.option(
    "-i",
    "--infile",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        readable=True, resolve_path=True
    ),
    default=DEFAULT_INFILE,  # remove later
    show_default=True,
    required=True,
    help="The input excel file containing the relevant metadata.",
)
@click.option(
    "-s",
    "--sheet",
    default=0,
    required=True,
    show_default=True,
    help="The sheet within the infile you want to read. This can be the name or an index.",
)
@click.option(
    "-f",
    "--filepath",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True,
        resolve_path=True
    ),
    default=DEFAULT_FILESPATH,  # remove later
    show_default=True,
    required=True,
    help="The directory containing the files to rename.",
)
@click.option(
    "--award/--new-award",
    default=True,
    required=True,
    show_default=True,
    help="The sheet within the infile you want to read. This can be the name or an index.",
)
@click.command()
def cli(infile, sheet, filepath, award):
    """Rename files for the WARC Awards for Effectiveness."""
    click.echo('\nINPUT: ' + click.style(filepath, fg='yellow'))
    ids = get_ids(infile, sheet)

    if award:
        rf = rename.RenameFile(filepath, ids, award)
        rf.runprocess()
    elif not award:
        fn = rename.WafeFilenames(filepath, ids)
        fn.process()

        # print(len(new_names))
