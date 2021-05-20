import click
from pathlib import Path
from pprint import pprint


class WafeFilenames:
    VTYPES = ['v01', 'SupportingContent']
    IMGTYPE = 'EntryPaper'
    # inherit this from other

    def __init__(self, path, ids):
        self.path = Path(path)
        self.ids = ids
        self.files = []
        self.data = {}
        self.old_filenames = []
        self.rename_data = {}

    def lookup_wafe_id(self, idnum: int):
        """lookup id within excel ids."""
        try:
            new = self.ids[idnum]
            return new
        except KeyError as e:
            # print('KeyError:', e, '- not found during lookup')
            return None

    def separate_filenames(self):
        for name in self.files:
            f = Path(name)
            fn = f.name
            stem = f.stem
            # split name without ext
            idi = stem.split('_')
            id_parts = len(idi)

            # label parts
            if id_parts == 3:
                raw_id = idi[0]

                new_id = self.lookup_wafe_id(raw_id)
                # print(new_id)

                if new_id is not None:
                    self.old_filenames.append(fn)
                    asset_id = idi[1]
                    tail = {
                        'type': idi[2].replace('CaseFilm', 'v01'),
                        'ext': f.suffix
                    }
                    if not new_id in self.data.keys():  # change to new_id
                        # change to new_id
                        self.data[new_id] = {asset_id: tail}
                    else:
                        self.data[new_id][asset_id] = tail  # change to new_id

        return self.data

    def number_vids(self):

        def count_vids(value: str, obj: dict):
            return sum(x == value for x in obj.values())
        # make this scalable to different vals

        new_filenames = []
        vtypes = WafeFilenames.VTYPES
        itype = WafeFilenames.IMGTYPE

        for id_key in self.data:
            # make this scalable to different vals
            creative_vids = 0
            campaign_vids = 0

            in_ids = self.data[id_key]

            for asset_key in in_ids:
                # get dict object within each asset key
                asset_obj = in_ids[asset_key]
                # make this scalable to different vals
                campaign_vids += count_vids(vtypes[0], asset_obj)
                creative_vids += count_vids(vtypes[1], asset_obj)

            # count image number
            inum = 1
            # count video number
            vnum = 1
            for asset_key in in_ids:

                asset = in_ids[asset_key]
                kv = 'type'  # key value
                tv = asset[kv]  # type value

                # if no campaign vids and 'type'='SupportingContent'
                if tv == vtypes[1]:
                    vnum += 1 if campaign_vids else 0
                    # update starting from v02
                    asset.update({kv: f'v0{vnum}'})
                    # else increment after each starting on v01
                    vnum += 1 if not campaign_vids else 0
                elif tv == itype:
                    asset.update({kv: f'f0{vnum}'})
                    inum += 1

                new_filenames.append(''.join([
                    id_key,
                    asset[kv],
                    asset['ext']
                ]))

        self.rename_data = dict(zip(self.old_filenames, new_filenames))

        return new_filenames

    def process(self):
        p = self.path
        if p.is_dir():
            self.files = list(p.glob('*'))
            self.separate_filenames()
            self.number_vids()
            lookup = self.rename_data
            for f in self.files:
                try:
                    fn = f.name
                    new_name = lookup[fn]
                    par = f.parent
                    new_file = p / new_name
                    click.echo(fr"{fn}   ->   {new_file}")

                    # write the output to a csv / log in the path

                    # CHECK_OUPUT #### f.rename(new_file) ####
                    break

                except KeyError as e:
                    click.echo(e)
        elif p.is_file():
            click.echo('files not accepted')
            # self.rename_file(p)


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
        """Loops through file list."""
        if self.award:
            for file in files:
                self.rename_file(file)

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
