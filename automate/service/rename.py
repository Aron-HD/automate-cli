import click
from pathlib import Path
from pprint import pprint


class RenameFile:
    """Rename a file or directory of files according to a column in the excel sheet."""

    def __init__(self, path, ids, award):
        self.path = Path(path)
        self.ids = ids
        self.award = award

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

    def split_filename(self, file, name):
        """Split filename correctly to get id based on boolean award legacy or new system."""

        # write config dict type file for separator and legacy / new award for changeability
        # or have separator determined at cli entry point
        stem = file.stem
        raw_id = stem
        new_name = ''

        if file.suffix == '.docx':
            # split these up so call this function once
            new_id = self.lookup_id(raw_id)
            new_name = name.replace(raw_id, new_id) if new_id else False

        # split old id
        elif self.award:
            raw_asset = stem.split(' ')
            processed_asset = stem.split('v')
            # if filename has no delimiter
            if len(raw_asset) > 1:
                # if delimiter is present
                raw_id = raw_asset[0]
                asset_id = raw_asset[1].replace('(1)', '01').replace(
                    '(2)', '02').replace('(3)', '03')  # <------------------zfill these
            # if already processed with v0 number
            elif len(processed_asset) > 1:
                raw_id = processed_asset[0]
                asset_id = processed_asset[1]
            else:
                # add v01 to ids with only one video
                asset_id = '01'

            # return False if not in lookup
            new_id = self.lookup_id(raw_id)

            # rejoin split halves
            edited_id = 'v'.join([new_id, asset_id]) if new_id else False

            new_name = edited_id + \
                file.suffix if new_id else False

        elif not self.award:
            idi = stem.split('_')
            # get correct id if there is no underscore separation
            id_parts = len(idi)
            if id_parts > 1:
                raw_id = idi[0]

            new_id = self.lookup_id(raw_id)

            if new_id:
                new_name = name.replace(raw_id, new_id)
                # .replace('CaseFilm', 'v01')#.replace('SupportingContent', 'v02') doesn't differentiate

                # if id_parts > 1:

                #     ext = file.suffix
                #     new_name = ''.join([idi[0], idi[2]]) + ext  # rewrite this
                #     new_id = True

        return new_name, new_id, raw_id

    def rename_file(self, file):
        """
        Splits filename to lookup id and renames after new id if found.
        """
        fn = file.name
        # find better way to do this split id_exists to own function
        new_name, id_exists, original_id = self.split_filename(file, fn)

        if id_exists:

            new_file = file.parent / new_name
            try:
                file.rename(new_file)
                click.echo(fr"{fn}   ->   {new_name}")
            except FileNotFoundError:
                click.echo(fn, '- src file not found')
            except FileExistsError:
                click.echo(' FAILED\t' + fn + ' -> ' +
                           new_name + ' - already exists')

    def runprocess(self):

        p = self.path

        if p.is_dir():
            files = list(p.glob('*'))
            self.rename_multiple(files)
        elif p.is_file():
            self.rename_file(p)
