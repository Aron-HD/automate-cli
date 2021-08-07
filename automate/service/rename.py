import click
from pathlib import Path, WindowsPath
# from pprint import pprint
from typing import List, Dict, Tuple


class WafeFilenames:

    def __init__(self, path, ids, name_format):
        self.path = Path(path)
        self.ids = ids
        self.name_format = name_format
        self.old_filenames = []
        self.split_filenames: Dict[int, Dict[int, Dict[str, str]]] = dict()
        self.output_filename = self.path / 'rename_output.csv'

    def lookup_wafe_id(self, idnum: int) -> int or None:
        """lookup id within excel ids."""
        try:
            new = self.ids[idnum]
            return new
        except KeyError:
            # print('KeyError:', e, '- not found during lookup')
            return None

    def analyse_parts(self, parts):
        # split name without ext
        if len(parts) > 1:
            parts[0] = self.lookup_wafe_id(parts[0])
            return parts
        else:
            return None

    def separate_filename(
            self,
            filename: WindowsPath) -> Dict[int, Dict[int, Dict[str, str]]]:

        f = Path(filename)
        fn = f.name
        stem = f.stem
        id_parts = self.analyse_parts(stem.split('_'))

        if id_parts is not None and len(id_parts) == 3:
            new_id = id_parts[0]
            self.old_filenames.append(fn)
            # assetid, type and extensions
            asset = {id_parts[1]: {'type': id_parts[2], 'ext': f.suffix}}

            if not new_id in self.split_filenames.keys():
                self.split_filenames[new_id] = asset
            else:
                self.split_filenames[new_id].update(asset)

        return self.split_filenames

    def order_filenames(
        self, split_filenames_data: Dict[int, Dict[int,
                                                   Dict[str,
                                                        str]]]) -> List[str]:

        new_filenames: List[str] = list()
        vtypes = SETTINGS.WAFE_FILENAMES.VTYPES
        vformats = SETTINGS.WAFE_FILENAMES.VFORMATS
        itype = SETTINGS.WAFE_FILENAMES.IMGTYPE

        for id_key in split_filenames_data:
            # make this scalable to different vals

            in_ids = split_filenames_data[id_key]

            # true if any campaign videos for that ID so know if to start from v01 or v02 for SupportingContent
            campaign_vids = any([
                x == vtypes[0]
                for x in [in_ids[akey]['type'] for akey in in_ids]
            ])

            # set count for video, image and additional asset
            inum, vnum, anum = (1, 1, 1)

            for asset_key in in_ids:

                asset = in_ids[asset_key]
                kv = 'type'  # key value
                tv = asset[kv]  # type value
                ext = asset['ext'].lower()  # file extension

                # IDv0n.ext
                if self.name_format == 'v0':

                    # if campaign vids and 'type'='SupportingContent'
                    if tv == vtypes[1] and ext in vformats:
                        vnum += 1 if campaign_vids else 0

                        # update starting from v02
                        asset.update({kv: f'v0{vnum}'})

                        # else increment after each starting on v01
                        vnum += 1 if not campaign_vids else 0

                    elif tv == itype:
                        asset.update({kv: f'f0{inum}'})
                        inum += 1

                    elif tv != itype and not ext in vformats:
                        asset.update({kv: f'a0{anum}-{asset[kv]}'})
                        anum += 1

                    joined_name = ''.join(
                        [id_key, asset[kv].replace(vtypes[0], 'v01'), ext])

                # ID_asset_originaltype.ext
                elif self.name_format == '_asset':
                    joined_name = '_'.join([id_key, asset_key, asset[kv]
                                            ]) + ext

                new_filenames.append(joined_name)

        return new_filenames

    def process(self):
        p = self.path

        if p.is_dir():
            # sort files so zip order stays correct
            files: List[WindowsPath] = sorted(list(p.glob('*.*')))

            for file in files:
                split_names = self.separate_filename(file)
            new_names = self.order_filenames(split_names)
            output = [self.old_filenames, new_names]
            # lookup dict for filenames
            lookup_data = dict(zip(*output))
            # tuples for pandas csv
            output_data: List[Tuple[str, str]] = list(zip(*output))

            for f in files:
                try:
                    fn = f.name
                    new_name = lookup_data[fn]
                    # new_file = p / new_name
                    # f.rename(new_file)  # CHECK_OUPUT ####
                    click.echo(fr"{fn}   ->   {new_name}")

                except KeyError as e:
                    print('x', e)

            return output_data

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
        except KeyError:
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
                    '(2)',
                    '02').replace('(3)',
                                  '03')  # <------------------zfill these
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

        return new_name, new_id

    def rename_file(self, file):
        """
        Splits filename to lookup id and renames after new id if found.
        """
        fn = file.name
        # find better way to do this split id_exists to own function
        new_name, id_exists = self.split_filename(file, fn)

        if id_exists:

            new_file = file.parent / new_name
            try:
                file.rename(new_file)
                click.echo(fr"{fn}   ->   {new_name}")
            except FileNotFoundError:
                click.echo(fn, '- src file not found')
            except FileExistsError:
                click.echo(' FAILED\t' + fn + ' -> ' + new_name +
                           ' - already exists')

    def runprocess(self):

        p = self.path

        if p.is_dir():
            files = list(p.glob('*'))
            self.rename_multiple(files)
        elif p.is_file():
            self.rename_file(p)
