import click
from pathlib import Path
from pprint import pprint


class RenameFile:
    """Rename a file or directory of files according to a column in the excel sheet."""

    def __init__(self, path, ids):
        self.path = Path(path)
        self.ids = ids

    def lookup_id(self, idnum):
        """lookup id within excel ids."""
        try:
            new = self.ids[idnum]
            return new
        except KeyError as e:
            # print('KeyError:', e, '- not found during lookup')
            return False

    def rename_multiple(self, files):
        """Recursively loops through file list."""
        # Base case
        if files == []:
            return 0
        else:
            f = files[0]
            self.rename_file(f)
            return self.rename_multiple(files[1:])

    def rename_file(self, file):
        """
        Splits filename to lookup id and renames after new id if found.
        """
        fn = file.name
        # get correct ID if there is no underscore separation
        idi = fn.split('_')
        if len(idi) < 2:
            old_id = file.stem
        else:
            old_id = idi[0]
        new_id = self.lookup_id(old_id)
        if new_id:
            new_name = fn.replace(old_id, new_id).replace(
                'CaseFilm', 'v01').replace('SupportingContent', 'v02')
            new_file = file.parent / new_name
            try:
                file.rename(new_file)
                click.echo(fr"{old_id}   ->   {new_name}")
            except FileNotFoundError:
                click.echo(fn, '- src file not found')
            except FileExistsError:
                click.echo(' FAILED\t' + old_id + ' -> ' +
                           new_name + ' - already exists')

    def runprocess(self):

        p = self.path

        if p.is_dir():
            files = list(p.glob('*'))
            self.rename_multiple(files)
        elif p.is_file():
            self.rename_file(p)
